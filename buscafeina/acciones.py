"""Classes d'acció: el motor que executa el que declara accions.json.

Hi ha una classe per a cada tipus d'efecte sobre l'ordinador (buscar als
portals, exportar, avaluar amb IA, filtrar amb IA, netejar fitxers, moure
fitxers) i una classe `Accio` que representa una entrada del JSON.

`Accio.from_config()` és el mètode estàtic fàbrica: construeix l'objecte a
partir del diccionari validat. Per això afegir una acció nova només exigeix
editar accions.json, no este codi.

Totes les accions:

- Reben un `ctx` (diccionari compartit: criteris, ofertes, fitxers generats,
  config…) que llegeixen i modifiquen → són combinables i encadenables.
- Retorna una cadena explicant **què s'ha fet sobre quins fitxers**.
- Respecten `simulacio=True`: en mode simulació no escriuen, no esborren ni
  criden la IA; només informen del que farien.
- Les destructives (`destructiva=True`) exigixen `--simulacio`, `--si` o
  confirmació interactiva; si no, s'aturen abans de tocar res.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path

from .errors import AccioNoValida, IAError


def _confirmar(accio, consola) -> bool:
    """Demana confirmació explícita per a accions destructives."""
    try:
        import questionary

        answer = questionary.confirm(
            f"L'acció «{accio.nom}» esborra o sobreescriu fitxers. Continuem?"
        ).ask()
        return bool(answer)
    except Exception:
        return False


# ----------------------------------------------------------------- efectes

@dataclass
class Efecte:
    """Base: qualsevol efecte rep ctx + paràmetres i torna un missatge."""

    params: dict = field(default_factory=dict)

    def aplicar(self, ctx: dict, params: dict, *, simulacio: bool = False) -> str:
        raise NotImplementedError


class AccioCerca(Efecte):
    """Consulta els portals triats i posa les ofertes a `ctx['ofertes']`.

    `ctx['cercar']` permet injectar una funció de cerca alternativa (les
    proves l'usen per a no dependre de la xarxa); per defecte, la del motor.
    """

    def aplicar(self, ctx, params, *, simulacio=False):
        from .motor import executar_cerca

        cercar = ctx.get("cercar") or executar_cerca
        limit = int(params.get("limit") or ctx.get("limit", 10))
        # el context mana: «--portals» guanya als per defectes de l'JSON
        portals = ctx.get("portals")
        if simulacio:
            noms = ", ".join(portals or ctx.get("portals", [])) or "tots"
            return f"[simulació] Consultaria {noms} amb límit {limit} i no guardaria res."
        ofertes, parells = cercar(ctx, portals=portals, limit=limit)
        ctx["ofertes"] = ofertes
        ctx["parells"] = parells
        lectors = sorted({p.label for p, o in parells if o})
        return (
            f"Consultats {len(parells)} portals"
            + (f" amb lectura automàtica: {', '.join(lectors)}" if lectors else "")
            + f" → {len(ofertes)} ofertes."
        )


class AccioExportar(Efecte):
    """Guarda les ofertes del context en CSV/JSON dins de `directori`."""

    def aplicar(self, ctx, params, *, simulacio=False):
        from .export import save_results

        ofertes = ctx.get("ofertes")
        parells = ctx.get("parells")
        if parells is None:
            parells = [(None, o) for o in ofertes or []]
        directori = str(params.get("directori") or ctx.get("directori", "resultats"))
        formats = params.get("formats")
        if formats is None:
            formats = ctx.get("formats")
        if formats is None:
            formats = ["csv", "json"]
        if isinstance(formats, str):
            formats = [formats]
        if not formats:
            # --guardar no: llista buida, no «sense decidir»
            return "No es guarda res: l'opció `--guardar` diu «no»."
        if not ofertes:
            return "Res a guardar: no hi ha ofertes al context."
        if simulacio:
            return (
                f"[simulació] Guardaria {len(ofertes)} ofertes a {directori}/ "
                f"en {' + '.join(formats)}."
            )
        created = save_results(parells, ctx["criteris"], list(formats), directory=directori)
        ctx.setdefault("fitxers", []).extend(str(p) for p in created)
        return f"Guardades {len(ofertes)} ofertes a " + ", ".join(str(p) for p in created)


class AccioAvaluar(Efecte):
    """Puntua les ofertes amb el proveïdor d'IA i exporta el rànquing."""

    def aplicar(self, ctx, params, *, simulacio=False):
        from . import avalua as avalua_mod

        ofertes = ctx.get("ofertes") or []
        perfil = str(params.get("perfil") or ctx.get("perfil") or "")
        model = params.get("model") or ctx.get("model")
        directori = str(params.get("directori") or ctx.get("directori", "resultats"))
        if not ofertes:
            return "Res a avaluar: no hi ha ofertes al context."
        if simulacio:
            return (
                f"[simulació] Avaluaria {len(ofertes)} ofertes amb "
                f"{model or 'el model del config'} (perfil: {perfil or 'genèric'}) "
                f"i guardaria el rànquing a {directori}/."
            )
        puntuades = avalua_mod.puntuar_ofertes(ctx["config"], model, ofertes, perfil)
        ctx["ofertes"] = puntuades
        path = avalua_mod.guardar_avaluades(puntuades, directory=directori)
        ctx.setdefault("fitxers", []).append(str(path))
        millors = sorted(
            (p for p in puntuades if isinstance(p.get("puntuacio"), (int, float))),
            key=lambda p: p["puntuacio"], reverse=True,
        )[:3]
        resum = "; ".join(f"{p['puntuacio']}/10 · {str(p['titol'])[:36]}" for p in millors)
        return f"Avaluades {len(puntuades)} ofertes → {path}" + (f". Millors: {resum}" if resum else "")


class AccioFiltrar(Efecte):
    """Descarta ofertes que la IA considera poc adequates per al perfil."""

    def aplicar(self, ctx, params, *, simulacio=False):
        from . import avalua as avalua_mod

        ofertes = ctx.get("ofertes") or []
        criteri = str(params.get("keyword") or ctx.get("perfil") or "")
        if not ofertes:
            return "Res a filtrar: no hi ha ofertes al context."
        if simulacio:
            return (
                f"[simulació] Filtaria {len(ofertes)} ofertes segons "
                f"«{criteri or 'perfil del config'}» i descartaria les que no encaixen."
            )
        keeps = avalua_mod.filtrar_ofertes(ctx["config"], ctx.get("model"), ofertes, criteri)
        ctx["ofertes"] = keeps
        return f"Filtrades {len(ofertes)} ofertes: en queden {len(keeps)}, descartades {len(ofertes) - len(keeps)}."


class AccioNeteja(Efecte):
    """Esborra fitxers de resultats més vells que N dies (destructiva)."""

    def aplicar(self, ctx, params, *, simulacio=False):
        directori = Path(str(params.get("directori") or ctx.get("directori", "resultats")))
        dies = int(params.get("dies") or 30)
        if not directori.is_dir():
            return f"No hi ha res a netejar: {directori} no existix."
        tall = datetime.now() - timedelta(days=dies)
        tocs = [
            f for f in sorted(directori.iterdir())
            if f.is_file() and f.suffix in (".csv", ".json")
            and datetime.fromtimestamp(f.stat().st_mtime) < tall
        ]
        if not tocs:
            return f"Cap fitxer de {directori} més vell que {dies} dies."
        if simulacio:
            return f"[simulació] Esborraria {len(tocs)} fitxers de {directori}/: " + ", ".join(
                f.name for f in tocs
            )
        for f in tocs:
            f.unlink()
        return f"Esborrats {len(tocs)} fitxers de {directori}/: " + ", ".join(f.name for f in tocs)


class AccioMoure(Efecte):
    """Mou els fitxers generats a la sessió a una subcarpeta d'arxiu (destructiva)."""

    def aplicar(self, ctx, params, *, simulacio=False):
        dest = Path(str(params.get("directori") or ctx.get("arxiu", "resultats/arxiu")))
        fitxers = [Path(f) for f in ctx.get("fitxers", []) if Path(f).exists()]
        if not fitxers:
            return "Res a moure: esta sessió no ha generat cap fitxer."
        if simulacio:
            return (
                f"[simulació] Mouria {len(fitxers)} fitxers a {dest}/: "
                + ", ".join(f.name for f in fitxers)
            )
        dest.mkdir(parents=True, exist_ok=True)
        moguts = []
        for f in fitxers:
            destinacio = _sense_colisio(dest, f)
            f.replace(destinacio)
            moguts.append(destinacio)
        ctx["fitxers"] = [str(m) for m in moguts]
        return f"Moguts {len(moguts)} fitxers a {dest}/: " + ", ".join(m.name for m in moguts)


def _sense_colisio(dest: Path, fitxer: Path) -> Path:
    """Si el nom ja existix a la destinació, afig un sufix horari en comptes de sobreescriure."""
    candidate = dest / fitxer.name
    if not candidate.exists():
        return candidate
    stamp = datetime.now().strftime("%H%M%S")
    return dest / f"{fitxer.stem}-{stamp}{fitxer.suffix}"


EFECTES = {
    "cerca": AccioCerca,
    "exportar": AccioExportar,
    "avaluar": AccioAvaluar,
    "filtrar": AccioFiltrar,
    "neteja": AccioNeteja,
    "moure": AccioMoure,
}


# ------------------------------------------------------------------- Accio

@dataclass
class Accio:
    """Una entrada d'accions.json, ja validada per l'esquema."""

    nom: str
    descripcio: str
    efecte: str
    comandos: list
    ordre: int = 50
    destructiva: bool = False
    requereix_ia: bool = False
    simulable: bool = True
    despres: list = field(default_factory=list)
    params: dict = field(default_factory=dict)
    classe: type = None  # la classe d'efecte, resolta a from_config()

    @staticmethod
    def from_config(entry: dict) -> "Accio":
        """Fàbrica: construeix l'acció a partir de l'entrada del JSON."""
        efecte = entry["efecte"]
        if efecte not in EFECTES:
            raise AccioNoValida(
                f"L'acció «{entry['nom']}» declara l'efecte desconegut «{efecte}». "
                f"Efectes permesos: {', '.join(sorted(EFECTES))}."
            )
        return Accio(
            nom=entry["nom"],
            descripcio=entry["describe"],
            efecte=efecte,
            comandos=list(entry["comandos"]),
            ordre=int(entry.get("ordre", 50)),
            destructiva=bool(entry.get("destructiva", False)),
            requereix_ia=bool(entry.get("requereix_ia", False)),
            simulable=bool(entry.get("simulable", True)),
            despres=list(entry.get("despres", [])),
            params=dict(entry.get("params", {})),
            classe=EFECTES[efecte],
        )

    @staticmethod
    def valors(entry_params: dict) -> dict:
        """Aplana `{ «param»: {«per_defecte»: v} }` a `{ «param»: v }`."""
        return {
            key: (spec.get("per_defecte") if isinstance(spec, dict) and "per_defecte" in spec else spec)
            for key, spec in entry_params.items()
        }

    def executar(self, ctx: dict, *, simulacio=False, confirmat=False, consola=None) -> str:
        """Executa l'acció aplicant les portes de seguretat pertinents."""
        params = self.valors(self.params)
        if self.requereix_ia and not simulacio:
            from .ia import ProveidorIA

            try:
                ok, motiu = ProveidorIA.from_config(ctx["config"], model=ctx.get("model")).disponble()
            except IAError as error:
                ok, motiu = False, str(error)
            if not ok:
                return f"· {self.nom}: saltada, la IA no està disponible ({motiu})"
        if self.destructiva and not simulacio and not confirmat:
            if not _confirmar(self, consola):
                return (
                    f"· {self.nom}: cancel·lat. És una acció destructiva: usa "
                    "--simulacio per a veure què faria o --si per a confirmar."
                )
        efecte = self.classe(params=params)
        resultat = efecte.aplicar(ctx, params, simulacio=simulacio)
        return f"· {self.nom}: {resultat}"
