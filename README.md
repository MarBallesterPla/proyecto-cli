# buscafeina

[![CI](https://github.com/MarBallesterPla/proyecto-cli/actions/workflows/ci.yml/badge.svg)](https://github.com/MarBallesterPla/proyecto-cli/actions/workflows/ci.yml)
[![release](https://img.shields.io/github/v/release/MarBallesterPla/proyecto-cli)](https://github.com/MarBallesterPla/proyecto-cli/releases)
[![Python ≥3.10](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)

CLI per a buscar, avaluar i ordenar ofertes de feina des del terminal, en
valencià. Consultes a sis cercadors (Labora, SEPE, InfoJobs, Turijobs, Pacte
Comarcal i LinkedIn), accions predefinides definides en un JSON extern, IA
local (Ollama) per a puntuar ofertes, i mode simulació per a tot.

## Instal·lació

Amb `uv` (recomanat) o `pipx`, des del repositori de GitHub:

```powershell
uv tool install git+https://github.com/MarBallesterPla/proyecto-cli.git
# o bé: pipx install git+https://github.com/MarBallesterPla/proyecto-cli.git
buscafeina accions          # queda disponible com a comando en qualsevol carpeta
```

> **Nota (uv):** el executable es posa a `%USERPROFILE%\.local\bin`. Si `uv`
> avisa que eixa carpeta no està al `PATH`, obri una finestra nova després
> d'afegir-la (Environament del sistema → variables d'entorn de l'usuari →
> `Path`), perquè `buscafeina` es resolga des de qualsevol carpeta. Verificable
> amb `Get-Command buscafeina`: ha de tornar la ruta de `.local\bin`, no una
> instal·lació editable antiga.

En mode desenvolupament, des d'una còpia local:

```powershell
git clone https://github.com/MarBallesterPla/proyecto-cli.git && cd proyecto-cli
pip install -e ".[dev]"
```

Requereix Python ≥ 3.10. Depèn de `requests`, `rich`, `questionary`,
`beautifulsoup4` i `jsonschema`.

## Ús

```powershell
buscafeina cerca -k "cambrer/a" -l "València" --guardar ambdos --no-browser
buscafeina tot   -k fuster -l Xàtiva --limit 15          # cerca + exporta + avalua
buscafeina avalua                                        # el fitxer més recent de resultats/
buscafeina avalua resultats/feina-panadero-valencia-20261110-1403.csv --filtrar
buscafeina neteja --simulacio                            # què esborraria (no res)
buscafeina neteja --si                                   # esborra de veritat
buscafeina accions                                       # les accions definides i el seu esquema
```

Opcions de `cerca`/`tot`:

| Opció | Descripció |
| --- | --- |
| `-k, --keyword` | Tipus de treball o paraula clau |
| `-l, --localitat` | Localitat o província |
| `--contracte` / `--jornada` / `--torn` / `--horari` | Filtres (veure `--help`) |
| `--portals` | Llista separada per comes (noms validats: error llegible si no) |
| `--limit` | Resultats per cercador |
| `--guardar` | `csv`, `json`, `ambdos` o `no` |
| `--model` / `-p, --perfil` | Model d'IA i perfil per a les accions amb IA |
| `--simulacio` | Mostra què farien les accions sense cridar la IA ni escriure res |
| `--si` | Confirma les accions destructives sense preguntar |
| `--no-browser` | No obrir el navegador: només imprimeix les URLs |
| `--exec NOM` | Executa només una acció del JSON |

**Portals**: LinkedIn, InfoJobs, SEPE i Turijobs es llegeixen automàticament;
Labora (formulari amb sessió DNI/PIN) i Pacte Comarcal no tenen lectura
automàtica, i la CLI obri el navegador amb la cerca apuntada (o imprimeix la
URL amb `--no-browser`). Com que Labora és el propi servei valencià i el SEPE
l'agrega, pots fer la cerca al SEPE en mode lectura i t'endús a Labora quan
vulgues postular-te. Torn i horari s'incorporen al text de la cerca perquè cap
portal té filtre natiu.

## Accions predefinides (`accions.json`)

Les accions **no estan escrites a mà al codi**: viuen en un fitxer JSON que
pots editar tu. Ordre de cerca: variable `BUSCAFEINA_ACCIONS` →
`./accions.json` → `~/.buscafeina/accions.json` → exemple inclòs en el paquet
(`buscafeina/data/accions.json`). El fitxer es valida **abans d'executar
res** contra `buscafeina/data/esquema-accions.json`; un error diu la ruta
exacta del camp (`accions/0/efecte: 'palla' is not one of [...]`), mai un
traceback.

### Esquema (resum)

```jsonc
{
  "esquema": 1,
  "accions": [
    {
      "nom": "avaluar-perfil",          // id únic, minúscules i guions
      "describe": "Puntua ofertes 0-10",// què es mostra a `buscafeina accions`
      "efecte": "avaluar",              // cerca | exportar | avaluar | filtrar | neteja | moure
      "comandos": ["avalua", "tot"],    // des d'on es pot executar
      "ordre": 30,                      // posició a la seqüència (opcional, 50)
      "destructiva": false,             // esborra/mou: cal --simulacio o --si
      "requereix_ia": true,             // sense IA es salta amb avís, no trunca
      "simulable": true,                // accepta --simulacio (per defecte, sí)
      "despres": ["exportar-fitxers"],  // encadenables: ací combinem accions
      "params": { "perfil": { "per_defecte": "" } }
    }
  ]
}
```

Efectes disponibles (cada un és una classe en `buscafeina/acciones.py`):

| Efecte | Què fa |
| --- | --- |
| `cerca` | Consulta els portals i ompli el context d'ofertes |
| `exportar` | Guarda les ofertes del context en CSV/JSON |
| `avaluar` | Puntua 0-10 amb IA i escriu el rànquing |
| `filtrar` | Descarta amb IA les ofertes que no encaixen |
| `neteja` | Esborra fitxers de resultats vells (**destructiva**) |
| `moure` | Arxiva els fitxers de la sessió (**destructiva**) |

**Afegir una acció no exigeix tocar el codi**: copia una entrada, canvia
`nom`, `comandos`, `despres` i `params`, i ja eixix en `buscafeina accions`
i en els comandaments que hages dit. La justificació d'este disseny i les
alternatives descartades estan en [`docs/adr/ADR-001`](docs/adr/ADR-001-configuracio-externa.md).

## IA i secrets

La capa d'IA (`buscafeina/ia.py`) te dos proveïdors, triats a
`~/.buscafeina/config.json` amb `proveidor_ia`:

- **`ollama`** (per defecte): model local, sense claus, sense eixida a
  internet. `ollama pull qwen3` i llestos.
- **`openai`**: qualsevol servidor compatible amb `/chat/completions`
  (`openai_base_url`). La clau es llig de la variable d'entorn que indique
  `openai_api_key_env` (per defecte `OPENAI_API_KEY`) o d'un fitxer `.env` en
  la carpeta actual.

`.env` està en `.gitignore` des del primer commit i `.env.example` documenta
les variables. **No hi ha cap clau en el codi ni en la història del repositori**
(podeu verificar-ho amb `git log -p -S API_KEY`).

**Sense xarxa o sense Ollama**, la CLI no es trenca: les accions amb IA es salten
amb un missatge que explica què falta i la resta de la seqüència (cerca,
exportar, neteja) funciona igualment. També tens `--simulacio` per a veure
tot el pla sense IA.

## Configuració (`~/.buscafeina/config.json`)

```json
{
  "pacte_comarcal_url": "https://example.org/borsa-de-la-meva-comarca",
  "resultats_per_cercador": 10,
  "directori_resultats": "resultats",
  "proveidor_ia": "ollama",
  "model_ia": "qwen3",
  "ollama_url": "http://localhost:11434",
  "perfil": "experiència en forneria, busque a la Safor"
}
```

Els tipus es validen: un número on va text produeix
`~/.buscafeina/config.json · «resultats_per_cercador» ha de ser un nombre enter`, no un comportament aleatori.

## Proves

```powershell
pip install -e ".[dev]"
pytest tests -v
```

38 proves amb pytest, **totes en carpetes temporals** (`tmp_path`) — mai sobre
fitxers reals:

- Camí feliç: càrrega de l'`accions.json` de exemple, cerca en simulació,
  exportació que informa del fitxer creat, neteja simulada, configuració
  vàlida, parseig de respostes brutes de la IA, **les dues accions amb IA
  (avaluar i filtrar) amb el proveïdor simulat**, analitzadors de SEPE i
  Turijobs amb HTML fixt (sense xarxa).
- Casos feos: JSON roto, JSON amb camps que falten o efectes inventats, config
  amb tipus equivocat, portal desconegut, acció destructiva sense confirmar
  (fitxers intactes), IA no disponible (es salta, no trunca), colisions de nom
  en moure fitxers, model que no torna JSON, `--guardar csv` que no ha
  d'escriure JSON també, i `--guardar no` que no ha d'escriure res.
- Les proves no tenen xarxa: un proveïdor d'IA simulat se n'encarrega.

El flux de GitHub Actions (`.github/workflows/ci.yml`) instal·la el paquet
des del repo, comprova que `buscafeina --help` funcione i executa `pytest` en
Python 3.10 i 3.12 a cada push i PR.

## Limitacions

- LinkedIn i InfoJobs poden bloquejar l'accés automatitzat; aquesta CLI fa servir
  només API públiques i sempre ofereix el pas al navegador. Ús
  personal i moderat.
- Labora requereix DNI + PIN; la CLI no guarda credencials.
- La qualitat de l'avaluació depén del model local; amb models xicotets el
  format JSON pot tindre soroll — el parseig ho tolera, i si no, avisar.

## Autor

Mar Ballester Pla — [github.com/MarBallesterPla](https://github.com/MarBallesterPla).
