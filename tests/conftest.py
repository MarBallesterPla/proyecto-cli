"""Patches compartides per a les proves: aïllen la xarxa i l'IA."""

import io
import json

import pytest
import requests


class RespostaFalsa(io.BytesIO):
    """Un requests.Response mínim fet d'un body JSON."""

    def __init__(self, payload, status_code=200):
        super().__init__(json.dumps(payload).encode("utf-8"))
        self.status_code = status_code
        self.url = "http://test"
        self.headers = {"Content-Type": "application/json"}
        self._payload = payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}", response=self)

    def json(self):
        return self._payload


@pytest.fixture
def sense_red(monkeypatch):
    """Qualsevol requests.get/post falla: simula estar sense xarxa."""

    def sin_red(*args, **kwargs):
        raise requests.ConnectionError("sense xarxa (simulat en la prova)")

    monkeypatch.setattr(requests, "get", sin_red)
    monkeypatch.setattr(requests, "post", sin_red)
    return sin_red


@pytest.fixture
def ofertes_planes():
    """Tres ofertes planes, com les que eixixen del CSV/JSON de resultats."""
    return [
        {"portal": "InfoJobs", "titol": "Fuster d'arxa", "empresa": "Fustes Sud",
         "lloc": "Xàtiva", "data": "2026-11-20", "detalls": "Indefinit · Jornada completa",
         "url": "https://example.org/oferta-1"},
        {"portal": "LinkedIn", "titol": "Cambrer/a torn de nit", "empresa": "Casa Nord",
         "lloc": "València", "data": "2026-11-21", "detalls": "Temporal",
         "url": "https://example.org/oferta-2"},
        {"portal": "LinkedIn", "titol": "Programador/a Python", "empresa": "Soft Nord",
         "lloc": "Alacant", "data": "2026-11-22", "detalls": "Indefinit · Remot",
         "url": "https://example.org/oferta-3"},
    ]


class ProveidorSimulat:
    """Proveïdor d'IA fals: torna el JSON que li digues, sense xarxa."""

    def __init__(self, resposta: str, disponible: bool = True, motiu: str = ""):
        self.resposta = resposta
        self._disponible = disponible
        self._motiu = motiu
        self.model = "model-simulat"
        self.crides = []

    def disponble(self):
        return self._disponible, self._motiu

    def chat(self, system, user):
        self.crides.append((system, user))
        return self.resposta


@pytest.fixture
def proveidor_fals(monkeypatch):
    """Substitueix la fàbrica ProveidorIA.from_config per un proveïdor simulat."""
    from buscafeina import ia

    estat = {"proveidor": ProveidorSimulat(json.dumps({"avaluacions": []}))}

    def fàbrica(config, model=None):
        return estat["proveidor"]

    monkeypatch.setattr(ia.ProveidorIA, "from_config", staticmethod(fàbrica))
    return estat
