# buscafeina

CLI per a buscar feina des del terminal, en valencià, amb quatre cercadors:

- **Labora** (Servei Valencià d'Ocupació — Punt Labora)
- **InfoJobs**
- **Pacte Comarcal** per a l'Ocupació
- **LinkedIn**

La CLI et pregunta els criteris (tipus de treball, localitat, tipus de
contracte, tipus de torn, horari i tipus de jornada) i fa dues coses:

1. **Mostra resultats al terminal** quan el portal ho permet (LinkedIn,
   InfoJobs).
2. Si un portal no permet lectura automàtica (Labora, Pacte Comarcal), fa
   **fallback**: obre el navegador amb la cerca i t'indica quins filtres
   has de triar al formulari.

## Instal·lació

```powershell
cd proyecto-cli
python -m pip install -e .
```

## Ús

```powershell
buscafeina
```

o bé, sense prompts ( útil per a scripts):

```powershell
buscafeina -k "cambrer/a" -l "València" --contracte Temporal --jornada Parcial --torn Matí --portals InfoJobs,LinkedIn --limit 5 --no-browser
```

Opcions:

| Opció | Descripció |
| --- | --- |
| `-k, --keyword` | Tipus de treball o paraula clau |
| `-l, --localitat` | Localitat o província |
| `--contracte` | Qualsevol / Indefinit / Temporal / Pràctiques / Autònom / Altres |
| `--jornada` | Qualsevol / Completa / Parcial / Mitja jornada / Per hores |
| `--torn` | Qualsevol / Matí / Tarda / Nit / Rotatiu |
| `--horari` | Qualsevol / Horari flexible / Horari partit / Mig horari |
| `--portals` | Llista separada per comes: `Labora,InfoJobs,Pacte Comarcal,LinkedIn` |
| `--limit` | Resultats per cercador (per defecte 10) |
| `--guardar` | Guardar els resultats: `csv`, `json` o `ambdos` (sense valor: `ambdos`) |
| `--no-browser` | No obrir el navegador; mostra les URLs de cerca |

## Com tracta cada portal

| Portal | Resultats al terminal | Filtres que s'apliquen |
| --- | --- | --- |
| **LinkedIn** | Sí (endpoint públic `jobs-guest`) | paraula clau, localitat, jornada/tipus (`f_JT`) |
| **InfoJobs** | Sí (HTML o API oficial) | paraula clau, localitat, contracte i jornada |
| **Labora** | No (formulari amb sessió DNI/PIN) | et duu al cercador amb els criteris apuntats |
| **Pacte Comarcal** | No (no té cercador unificat) | obre la borsa de la teua comarca |

**Torn i horari**: cap dels portals grans té filtre natiu de torn o horari,
així que la CLI els incorpora al text de la cerca (p. ex. «cambrer/a torn de
nit»).

## Guardar els resultats

Tres maneres:

```powershell
# Al final de la cerca interactiva et preguntarà si vols guardar
buscafeina

# Directament amb la opció (csv, json o ambdos)
buscafeina -k "cambrer/a" -l "València" --guardar ambdos

# Sense obrir el navegador
buscafeina -k "panadero" -l "València" --guardar csv --no-browser
```

Els fitxers es creen a la carpeta `resultats/` amb el nom de la cerca i la
data, per exemple `resultats/feina-panadero-valencia-20261110-1032.csv`:

- **CSV**: amb codificació `utf-8-sig` i separador `;`, a punt d'obrir amb
  doble clic a Excel o LibreOffice.
- **JSON**: llista d'ofertes amb tots els camps, útil per a tractar-les
  després amb Python.

En ambdós formats també es guarden els portals que no permeten lectura
automàtica (Labora, Pacte Comarcal) amb la seua URL de cerca per a obrir-los
més tard.

## Avaluar les ofertes amb IA local (Ollama)

Si tens [Ollama](https://ollama.com) instal·lat, pots fer que un model
local — que no ix a internet i és gratuït — puntuï les ofertes guardades
segons el teu perfil:

```powershell
ollama pull qwen3                # primer, descarrega el model (~5 GB)

buscafeina avalua                # avalua el fitxer més recent de resultats/
buscafeina avalua resultats/feina-panadero-valencia-20261110-1403.csv
buscafeina avalua -p "2 anys d'experiència en forneria, busque jornada completa a la Safor"
buscafeina avalua -m qwen3:4b    # model alternatiu
```

Per a cada oferta, el model dona una **puntuació de 0 a 10** i un motiu breu
en valencià. Les ofertes queden ordenades i es guarden a
`resultats/avaluades-<data>.csv`.

El perfil habitual es pot deixar fixat a `~/.buscafeina/config.json`:

```json
{
  "model_ollama": "qwen3",
  "perfil": "experiència en forneria i hostaleria, busque a la Safor"
}
```

## Configuració

El fitxer `~/.buscafeina/config.json` (es crea automàticament) permet:

```json
{
  "pacte_comarcal_url": "https://example.org/borsa-de-la-meva-comarca",
  "resultats_per_cercador": 10,
  "model_ollama": "qwen3",
  "perfil": "experiència en forneria, busque a la Safor"
}
```

Pots trobar el pacte de la teua comarca a
[Avalem Territori](https://avalemterritori.es/acords-territorials/pactes-per-locupacio/)
i posar-ne la URL de la borsa d'ocupació.

### InfoJobs via API (opcional, recomanat)

Per a resultats d'InfoJobs més fiables i amb filtres complets, registra una
aplicació gratuïta a [developer.infojobs.net](https://developer.infojobs.net)
i exporta:

```powershell
$env:INFOJOBS_CLIENT_ID = "el-teu-id"
$env:INFOJOBS_CLIENT_SECRET = "el-teu-secret"
```

Sense aquestes variables, la CLI intenta llegir la pàgina de resultats i, si
el portal la bloqueja, cau al navegador. Tingues en compte que, en mode de
rascat i sense API, el filtre de localitat no es pot aplicar de manera
fiable (el mateix InfoJobs l'aplica al navegador); la CLI t'ho advertirà.

## Limitacions

- LinkedIn i InfoJobs reserven el dret de bloquejar l'accés automatitzat;
  aquesta CLI n'usa només endpoints públics i sempre ofereix el fallback al
  navegador. Feu-ne un ús personal i moderat.
- Labora requereix DNI + PIN per a postular-se; la CLI no guarda credencials.
