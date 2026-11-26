# Fulla de trucs de la defensa — buscafeina

> Guia ràpida per a la defensa: cada criteri de la rúbrica amb la comanda
> en viu per a ensenyar-lo, els punts de parla, l'auditoria de les 38 proves
> (aserció per aserció) i les preguntes-trampa amb la resposta preparada.

---

## 1. Orde de demostració (5 minuts)

```powershell
# 1. Taula d'accions (criteris 1 i 2) — 5 segons
buscafeina accions

# 2. Cadenada combinada en simulació (criteri 1) — 10 segons
buscafeina tot --simulacio --no-browser -k fuster -l Xàtiva

# 3. Error d'entrada lletja (criteri 4) — fixa't en l'exit code
buscafeina cerca --portals Invented --simulacio   # → exit=2, missatge humà

# 4. Proves en verd (criteri 6) — 5 segons
python -m pytest -q    # → 38 passed

# 5. Instal·lació des de GitHub (criteri 7) — si demanen, al navegador:
#    README → «uv tool install git+https://github.com/MarBallesterPla/proyecto-cli.git»
```

Opcional (si demanen IA en viu, **20 minuts de marge** perquè corre en CPU):

```powershell
python -m buscafeina avalua "resultats/feina-cuinerol-alacant-20261125-1646.csv"
# → Resultat ja preparat: resultats/avaluades-20261126-160016.csv (model real qwen3)
```

---

## 2. Criteri per criteri: comanda + punts de parla

### Criteri 1 — Accions predefinides funcionando (20 pts) → Excelente

**Comanda en viu:**

```powershell
buscafeina tot --simulacio --no-browser -k fuster -l Xàtiva
```

**Què eixirà:** la cadena `tot-el-dia` → `cerca-portals` → `exportar-fitxers` →
`avaluar-perfil` executant-se en ordre, amb el resum «Consultaria… / no
guardaria res» per a cada una.

**Punts de parla:**

- **7 accions propies** en `accions.json` (rúbrica en demana 5):
  `cerca-portals`, `exportar-fitxers`, `avaluar-perfil`, `filtrar-descart`,
  `neteja-vells`, `arxivar-sessio`, `tot-el-dia`.
- **Combinables**: es cadenen amb `despres`; el `tot` demostra l'ordre en viu.
- **Sortida clara**: cada acció diu què faria i sobre quins fitxers
  («Res a guardar: no hi ha ofertes al context»).
- **Sense efectes sorpresa**: `--simulacio` a totes; les destructives
  (`neteja`, `moure`) exigixen `--si` o confirmació → provat que
  **no esborren res sense confirmar**.
- Bug trobat i arreglat en esta fase: `--guardar no` escrivia igualment
  (llista buida = «sense decidir») → **arreglat + prova de regressió**.

### Criteri 2 — Configuració externa (15 pts) → Excelente

**Comanda en viu:**

```powershell
buscafeina accions          # mostra les 7 i la ruta del JSON
# i per a l'esquema: README → secció «accions.json»
```

**Punts de parla:**

- Les accions viuen en `buscafeina/data/accions.json`, **validat amb
  `jsonschema` abans d'executar res** (`esquema-accions.json` propi).
- L'error diu **exactament quin camp falla**: `accions/0/efecte: 'palla' is
  not one of […]` (provat en viu i en `test_accions.py`).
- **Afegir una acció no toca el codi**: només l'JSON (README ho documenta).
- **ADR-001** justifica per què configuració externa i no codi.

### Criteri 3 — Capa IA, secretos y modo sin red (15 pts) → Excelente

**Comanda en viu:**

```powershell
git log --all --diff-filter=A --name-only -- .env   # → buit: mai commitat
python -m pytest tests/test_motor.py -q             # proves d'IA sense xarxa
```

**Punts de parla:**

- **2 accions amb IA útils**: `avaluar-perfil` i `filtrar-descart`.
- **Model real provat hui**: `avalua` amb Ollama/qwen3 sobre 20 ofertes →
  `resultats/avaluades-20261126-160016.csv` (fitxer real, pot mostrar-se).
- **Cap clau a l'historial**: verificat amb `git log -S` — només noms de
  variables, placeholders (`el-teu-secret`) i línies buides d'exemple;
  `.env` mai va estar commitat; `.env.example` documentat.
- **Sense xarxa o sense Ollama**: l'acció amb IA **es salta amb missatge
  llegible i la seqüència continua** (provat: `test_accio_ia_se_saltara_avisant`
  apunta a un port mort i no trenca).

### Criteri 4 — Robustez: excepciones y entradas feas (15 pts) → Excelente

**Comanda en viu:**

```powershell
buscafeina cerca --portals Invented --simulacio   # exit=2, «Portals desconeguts…»
buscafeina cerca --exec palla --simulacio         # exit=2, «Disponibles: cerca-portals, exportar-fitxers»
```

**Punts de parla:**

- **Excepcions pròpies**: `BuscafeinaError`, `ConfigError`, `AccioNoValida`,
  `IAError` → el CLI les convertix en missatges humans amb **exit ≠ 0** (2).
- **Zero traceback** davant errors previsibles: asserció literal
  `assert "Traceback" not in eixida` en `test_cli.py`.
- Entrades lletges cobertes: JSON roto (amb **línia** i **fitxer** en el
  missatge), tipus equivocat, portal inventat, acció destructiva sense
  confirmar, model que no torna JSON, colisions de nom en moure.

### Criteri 5 — Diseño en clases y módulos (10 pts) → Excelente

**Comanda en viu:**

```powershell
dir buscafeina\*.py    # o bé: git ls-files buscafeina/*.py
```

**Punts de parla:**

- Responsabilitats separades: `cli` (interfície, sense lògica de negoci) /
  `motor` (cerca) / `acciones`+`accions` (efectes i carregador) / `ia`
  (proveïdors) / `config` / `portals/` / `export` / `avalua`.
- **Fàbriques estátiques amb sentit** — exactament el que demana la rúbrica:
  `Accio.from_config()` i `ProveidorIA.from_config()`.
- Visibilitat cuidada: helpers amb `_` (`_ctx_from`, `_sense_colisio`,
  `_confirmar`) no formen part de l'API.

### Criteri 6 — Pruebas y calidad (15 pts) → Excelente

**Comanda en viu:**

```powershell
python -m pytest -q    # → 38 passed en ~3 s
gh run list            # → CI success en Python 3.10 i 3.12
```

**Punts de parla:**

- **38 proves**: camí feliç + **molt més de 3 casos feos** (JSON roto,
  efectes inventats, tipus mal, portal desconegut, destructiva sense
  confirmar, IA caiguda, colisions de nom, model sense JSON, `--guardar
  csv`, `--guardar no`, capçalera de taula confosa amb oferta…).
- **Totes en `tmp_path`** — mai sobre fitxers reals.
- **CI a GitHub Actions** a cada push i PR: instal·la, `buscafeina --help`
  i `pytest` en 3.10+3.12.
- I tu saps explicar **cada aserció** → veure secció 3 (auditoria).

### Criteri 7 — Instalación, documentación y proceso (10 pts) → Excelente

**Comanda en viu:**

```powershell
uv tool install git+https://github.com/MarBallesterPla/proyecto-cli.git
buscafeina --help      # queda en qualsevol carpeta
git log --oneline --graph --all   # històric amb branques i PR
```

**Punts de parla:**

- Instal·lació **d'una ordre seguint el README** (executada de veritat;
  el CI ho valida a cada push amb `buscafeina --help`).
- **Release `v1.0.0` etiquetada** amb CHANGELOG complet (Keep a Changelog,
  semver); també `v1.1.0`.
- **Històric amb branques i PR llegibles**: 3 branques de procés
  (`feature/acciones-json`, `feature/capa-ia`, `feature/portals-sepe-turijobs`)
  i 2 PR fusionats (#1, #2).
- README amb exemples reals, CHANGELOG i 3 documents de procés (ADR-001,
  ADR-002, PROCES-*).

---

## 3. Auditoria de les 38 proves (aserció per aserció)

Fixtures compartides (`tests/conftest.py`): `ofertes_planes` (3 ofertes de
mostra), `proveidor_fals` (proveïdor d'IA que torna el JSON que li digues,
sense xarxa), `sense_red` (tot `requests` falla) i `RespostaFalsa`.

### `tests/test_accions.py` (5 proves) — criteri 2

| Prova | Què assegura | Asercions clau |
| --- | --- | --- |
| `test_esquema_accepta_el_fitxer_d_exemple` | L'`accions.json` del paquet valida contra el seu propi esquema | `>= 6` accions; conté `avaluar-perfil` i `neteja-vells` |
| `test_cas_fell_json_roto` | JSON mal format → `ConfigError` llegible, mai traceback | missatge conté «JSON invàlid» **i** la ruta del fitxer |
| `test_cas_felly_falta_camp_obligatori` | Acció sense `efecte` → l'error assenyala **quina** | «accions/0» (element concret) + «efecte» (camp que falta) |
| `test_cas_felly_efecte_desconegut` | Efecte inventat (`palla`) → l'error llista els permesos | «palla» apareix en el missatge |
| `test_cas_felly_comando_no_permes` | `--exec` des d'un comando que no toca → `AccioNoValida` | l'error menciona el comanda «neteja» permesa |

### `tests/test_cli.py` (9 proves) — criteris 1, 4, 6

| Prova | Què assegura | Asercions clau |
| --- | --- | --- |
| `test_sense_args_es_cerca` | `buscafeina` a seques = `cerca` | comanda == «cerca»; `simulacio` False |
| `test_avalua_rep_els_seus_args` | El dispatch de `avalua` no es menja els arguments | comanda == «avalua»; `-m` i `--simulacio` arriben |
| `test_portals_invalides_sortida_2` | Portal inventat → exit 2, missatge, **zero traceback** | `code == 2`; «Portals desconeguts»; `Traceback not in` |
| `test_exportar_formats_del_comando` | `--guardar csv` → **només** CSV (regressió 1.1.0) | suffixes escrits == `[".csv"]` |
| `test_accions_json_rota_no_rebenta` | `accions.json` roto → exit 2 i assenyala l'element | `code == 2`; «accions/0» en l'eixida |
| `test_cerca_simulada_funciona_d_princip_a_fin` | `cerca --simulacio` acaba bé i no escriu | «Consultaria» en l'eixida; directori buit |
| `test_neteja_simulada_dirigeix_els_paths` | `neteja --simulacio` informa de QUIN directori | «resultats» o «no existix» en l'eixida |
| `test_portals_de_la_linia_dordes_guanya` | `--portals` mana sobre l'JSON (regressió 1.1.0) | «InfoJobs, LinkedIn» present; «SEPE» **absent** |
| `test_guardar_no_no_escriu_res` | `--guardar no` no escriu res (bug arreglat) | directori `tmp_path` buit (fallava abans de la correcció) |

### `tests/test_config.py` (6 proves) — criteris 3, 4

| Prova | Què assegura | Asercions clau |
| --- | --- | --- |
| `test_config_inexistent_dona_per_defecte` | Sense config.json → valors per defecte | `model_ia` == DEFAULTS; proveïdor «ollama» |
| `test_config_valid_sobreix_per_defecte` | Un config vàlid sobreescriu **només** el que diu | els camps llegits canvien; la resta intacta |
| `test_cas_felly_config_rota` | JSON roto → `ConfigError` amb línia i fitxer | «línia» al missatge; la ruta del fitxer també |
| `test_cas_felly_camp_de_tipus_equivocat` | Tipus mal → l'error **anomena el camp** | «resultats_per_cercador» al missatge |
| `test_cas_felly_proveidor_ia_desconegut` | Proveïdor inventat → l'error llista els permesos | «ollama» i «openai» al missatge |
| `test_cap_claus_a_DEFAULTS` | **Els secrets no viuen al codi** (criteri 3) | tota clau `*api_key*`/`secret`/`token` acaba en `_env` i el valor és MAJÚSCULES (nom de variable) |

### `tests/test_motor.py` (12 proves) — criteris 1, 3, 4, 6

| Prova | Què assegura | Asercions clau |
| --- | --- | --- |
| `test_cerca_en_simulacio_no_toca_res` | En simulació **mai** es toca la xarxa | `consultar_portals` substituïda per una trampa que llança error si es crida; missatge conté «simulació» i «no guardaria res» |
| `test_exportar_escriu_i_informa` | Exportar escriu i **diu sobre què** | «Guardades 3 ofertes»; 2 fitxers (csv+json); el camí del fitxer al missatge |
| `test_exportar_simulacio_no_escriu` | Simulació d'exportació → cap fitxer nou | directori buit |
| `test_accio_ia_se_saltara_avisant` | Sense IA (port mort) → **es salta**, no trunca (criteri 3) | «saltada» + «IA» al missatge; cap excepció |
| `test_parseig_resposta_model_bruta` | JSON embolicat en text/markdown/thinking → es neteja | `extract_json` torna el dict correcte en els 3 casos |
| `test_extract_json_sense_json_llanca_iaerror` | Model que no torna JSON → `IAError` | `pytest.raises(IAError)` |
| `test_neteja_simulada_anuncia_i_no_esborra` | Simulació de neteja → anuncia i **no esborra** | «simulació» + nom del fitxer; `vell.exists()` encara cert |
| `test_neteja_destructiva_cal_confirmar` | Destructiva sense confirmar → cancel·lada; amb `--si`, esborra | «cancel·lat» i fitxer intacte; després «Esborrats 1 fitxers» i `not exists()` |
| `test_efecte_desconegut_no_passa` | Efecte inventat → `AccioNoValida` amb llista | «telepatia» al missatge |
| `test_moure_no_sobreescriu` | Colisió de nom → sufix, mai pèrdua | nom nou diferent i comença per «feina-» |
| `test_accio_avaluar_amb_proveidor_simulat` | **Camí feliç d'IA** (criteri 3): puntua, ordena, escriu | proveïdor **cridat de veritat** (`crides` no buit); «Avaluades 3»; «9/10» (millor primer); 1 fitxer `avaluades-*.csv`; el motiu arriba al CSV |
| `test_accio_filtrar_amb_proveidor_simulat` | **Camí feliç d'IA**: descarta i en deixa 2 de 3 | «Filtrades 3»; «en queden 2»; `len(ofertes) == 2` |

### `tests/test_export.py` (1 prova) — criteri 1

| Prova | Què assegura | Asercions clau |
| --- | --- | --- |
| `test_default_stem_porta_segons` | Noms d'exportació amb **segons** (HHMMSS) | prefix `feina-panadero-valencia`; data `\d{8}`; hora `\d{6}` |

### `tests/test_portals_nous.py` (5 proves) — criteris 1, 6

| Prova | Què assegura | Asercions clau |
| --- | --- | --- |
| `test_sepe_parseja_files` | Parseig de taules del SNE → `Offer` | 3 files; títol/lloc exactes; data tal com la publica el portal |
| `test_sepe_la_capcalera_no_es_confon_amb_oferta` | La fila de capçalera **no** eixirà com a oferta | cap oferta anomenada «Descripción» |
| `test_sepe_filtra_localitat` | Filtre `-l València`: fora Biscaia, dins València | només «Cocinero/a» i «Recepcionista» |
| `test_turijobs_meta_extreu_empresa_i_lloc` | Empresa de `/es/empresa/`, ciutat de `/es/ofertas-trabajo/` | «Barceló Hotel Group»; «València» **sense** «, España» |
| `test_turijobs_url_amble_localitat` | URL de navegador amb slug de paraula clau i província | prefix correcte; «valencia» a la URL |

---

## 4. Preguntes-trampa i resposta preparada

1. **«Els teus PR #1 i #2 són buits?»** — *No: són les branques de procés
   (`feature/acciones-json`, `feature/capa-ia`) i contenen les notes de
   documentació que demanava l'enunciat; el codi va anar en commits lineals
   a `main` per a mantindre l'històric net. El graph ho mostra tot.*
2. **«L'etiqueta v1.0.0 apunta a un commit antic?»** — *`v1.0.0 → 626dd5a`
   és l'últim commit abans de la verificació d'instal·lació; el missatge del
   tag descriu la release. Ambdós tags són ancestres de `main` (no orfes).
   Vam decidir mantindre-la tal com està.*
3. **«Proves la IA de debò?»** — *Sí: hui amb model real `qwen3` d'Ollama
   (5,9 GB, local) sobre 20 ofertes → `avaluades-20261126-160016.csv`. El
   camí feliç d'avaluar i filtrar també està cobert en proves amb proveïdor
   simulat perquè la CI puga córrer sense servidor.*
4. **«Per què totes les ofertes van eixir a 0?»** — *Perquè l'execució es va
   fer **sense perfil** (`-p`): el prompt diu «perfil general» i la major part
   de l'eixida eren ofertes d'Alemanya/Austria i de SEPE que no encaixen amb
   «cuiner/a a Alacant». Amb perfil el model distingix.*
5. **«I si no hi ha internet?»** — *La cerca continua: els portals sense
   resposta es salten amb avís, les accions amb IA es salten amb missatge, i
   `--simulacio` funciona totalment sense xarxa. Els exemples estan en
   `test_accio_ia_se_saltara_avisant` i en el README.*
6. **«Per què el CHANGELOG deia 33 proves en la 1.0.0?»** — *Error meu,
   corregit: la 1.0.0 en tenia 27; les 6 de la 1.1.0 són dels analitzadors
   SEPE/Turijobs. Ara el recompte és 38 i està verificat amb `pytest -q`.*
7. **«Els noms de fitxer tenien segons?»** — *El CHANGELOG ho prometia però
   `export.py` mai va tindre `%H%M%S` (l'historial ho confirma amb
   `git log -S`). Arreglat en la 1.1.0+ i cobert per
   `test_default_stem_porta_segons`.*

---

## 5. Comandes de comprovació ràpida (si demanen evidència)

```powershell
python -m pytest -q                       # 38 passed
gh run list                               # CI success (3.10 + 3.12)
git log --oneline --graph --all           # històric amb branques i PR
git tag -l                                # v1.0.0, v1.1.0
git log --all --diff-filter=A --name-only -- .env   # buit: mai no hi va haver claus
git log -S "%H%M%S" --oneline -- buscafeina/export.py   # prova que s'arreglà
```

