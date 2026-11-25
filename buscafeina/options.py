"""Opcions dels menús i correspondències amb els filtres de cada portal."""

# Portals disponibles
PORTALS = ["Labora", "InfoJobs", "Pacte Comarcal", "LinkedIn", "SEPE", "Turijobs"]

# Tipus de contracte (categoríes reals d'InfoJobs)
CONTRACT_OPTIONS = [
    "Qualsevol",
    "Indefinit",
    "Temporal",
    "Pràctiques",
    "Autònom / Freelance",
    "Altres",
]

# Tipus de jornada
WORKDAY_OPTIONS = [
    "Qualsevol",
    "Completa",
    "Parcial",
    "Mitja jornada",
    "Per hores",
]

# Tipus de torn
SHIFT_OPTIONS = [
    "Qualsevol",
    "Matí",
    "Tarda",
    "Nit",
    "Rotatiu",
]

# Tipus d'horari
SCHEDULE_OPTIONS = [
    "Qualsevol",
    "Horari flexible",
    "Horari partit",
    "Mig horari",
]

# Terme textual que s'afegeix a la paraula clau (sense filtre natiu)
SHIFT_TERMS = {
    "Matí": "torn de matí",
    "Tarda": "torn de tarda",
    "Nit": "torn de nit",
    "Rotatiu": "torn rotatiu",
}

SCHEDULE_TERMS = {
    "Horari flexible": "horari flexible",
    "Horari partit": "horari partit",
    "Mig horari": "mig jornada",
}

# --- InfoJobs (API oficial: slugs del diccionari /dictionary/contract-type) ---
INFOJOBS_CONTRACT = {
    "Indefinit": "indefinido",
    "Temporal": "temporal",
    "Pràctiques": "practicas",
    "Autònom / Freelance": "autonomo",
    "Altres": "otros-contratos",
}

INFOJOBS_WORKDAY = {
    "Completa": "completa",
    "Parcial": "parcial",
    "Mitja jornada": "parcial",
    "Per hores": "por-horas",
}

# --- LinkedIn (codi f_JT: F=complet, P=parcial, C=contracte, I=pràctiques,
#     T=temporal, O=altres) ---
LINKEDIN_CONTRACT = {
    "Indefinit": "F",
    "Temporal": "T",
    "Pràctiques": "I",
    "Autònom / Freelance": "O",
    "Altres": "C",
}

LINKEDIN_WORKDAY = {
    "Completa": "F",
    "Parcial": "P",
    "Mitja jornada": "P",
    "Per hores": "P",
}
