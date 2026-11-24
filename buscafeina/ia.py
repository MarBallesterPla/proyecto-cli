"""Proveïdors d'IA per a les accions amb llenguatge natural.

Dos proveïdors, tots dos locals o amb la clau fora del codi:

- Ollama (per defecte): servidor local a http://localhost:11434. Sense clau
  i sense eixida a internet.
- OpenAI-compatible: qualsevol endpoint compatible amb /chat/completions
  (OpenAI, OpenRouter, un servei propi…). La clau es llegeix de la variable
  d'entorn que indiqui el config; mai s'escriu al codi ni al repositori.

Si el proveïdor no està disponible, les funcions llancen IAError amb un
missatge humà; el CLI l'imprimeix i continua amb les accions que no
necessiten IA (veure cli.py).
"""

import os
import re
import json

import requests

from .errors import IAError

DEFAULT_TIMEOUT_CONNECT = 5
DEFAULT_TIMEOUT_GENERATE = 900


def extract_json(text: str) -> dict:
    """Extrau el primer objecte JSON d'una resposta d'un model.

    Gestiona blocs <|im_start|>propis de models raonadors i text envoltant
    el JSON (```json … ```). Llança IAError si no hi ha cap JSON vàlid.
    """
    text = re.sub(r"<\|think\|>.*?<\|/think\|>", "", text, flags=re.DOTALL)
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            raise IAError(f"El model no ha tornat cap JSON: {text[:200]}")
        try:
            return json.loads(match.group())
        except json.JSONDecodeError as error:
            raise IAError(f"El model ha tornat JSON invàlid: {error}")


class ProveidorIA:
    """Interfície mínima: donar servei i respondre promptes."""

    def __init__(self, config: dict, model: str | None = None):
        self.config = config
        self.model = model or config.get("model_ia") or "qwen3"

    @staticmethod
    def from_config(config: dict, model: str | None = None) -> "ProveidorIA":
        """Fàbrica: tria el proveïdor segons la clau «proveidor_ia» del config."""
        kind = (config.get("proveidor_ia") or "ollama").lower()
        if kind in ("ollama", "local"):
            return Ollama(config, model=model)
        if kind == "openai":
            return OpenAICompatible(config, model=model)
        raise IAError(
            f"Proveïdor d'IA desconegut: '{kind}'. "
            "Valors permesos a «proveidor_ia»: 'ollama' o 'openai'."
        )

    def disponble(self) -> tuple[bool, str]:
        """(disponible, motiu_legible). No llança excepcions."""
        raise NotImplementedError

    def chat(self, system: str, user: str) -> str:
        """Resposta de text del model per al prompte donat."""
        raise NotImplementedError


class Ollama(ProveidorIA):
    """Servidor Ollama local (per defecte, sense claus i sense eixida a internet)."""

    def __init__(self, config: dict, model: str | None = None, base_url: str | None = None):
        super().__init__(config, model=model)
        self.base_url = (base_url or config.get("ollama_url") or "http://localhost:11434").rstrip("/")

    @property
    def tags_url(self) -> str:
        return f"{self.base_url}/api/tags"

    @property
    def chat_url(self) -> str:
        return f"{self.base_url}/api/chat"

    def llista_models(self) -> list[str]:
        try:
            response = requests.get(self.tags_url, timeout=DEFAULT_TIMEOUT_CONNECT)
            response.raise_for_status()
        except requests.RequestException as error:
            raise IAError(
                f"No hi ha cap servidor Ollama a {self.base_url} "
                f"({error.__class__.__name__}). Inicia'l amb «ollama serve» i torna-ho a provar."
            )
        return [m.get("name", "") for m in response.json().get("models", [])]

    def disponble(self) -> tuple[bool, str]:
        try:
            installed = self.llista_models()
        except IAError as error:
            return False, str(error)
        bases = {name.split(":")[0] for name in installed}
        if self.model not in installed and self.model not in bases:
            disponibles = ", ".join(installed) or "cap"
            return False, (
                f"El model '{self.model}' no està descarregat a Ollama. "
                f"Disponibles: {disponibles}. Baixa'l amb: ollama pull {self.model}"
            )
        return True, ""

    def chat(self, system: str, user: str) -> str:
        ok, reason = self.disponble()
        if not ok:
            raise IAError(reason)
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
            "format": "json",
            "think": False,
            "options": {"temperature": 0.2},
        }
        try:
            response = requests.post(
                self.chat_url, json=payload,
                timeout=(DEFAULT_TIMEOUT_CONNECT, DEFAULT_TIMEOUT_GENERATE),
            )
            if response.status_code == 400 and "think" in response.text.lower():
                payload.pop("think")  # versions sense suport de «think»
                response = requests.post(
                    self.chat_url, json=payload,
                    timeout=(DEFAULT_TIMEOUT_CONNECT, DEFAULT_TIMEOUT_GENERATE),
                )
            response.raise_for_status()
        except requests.RequestException as error:
            raise IAError(f"Error de connexió amb Ollama: {error}")
        try:
            return response.json()["message"]["content"]
        except (KeyError, ValueError) as error:
            raise IAError(f"Resposta inesperada del model: {error}")


class OpenAICompatible(ProveidorIA):
    """Endpoint compatible amb OpenAI /chat/completions; clau només per entorn o config."""

    def __init__(self, config: dict, model: str | None = None):
        super().__init__(config, model=model)
        self.base_url = (config.get("openai_base_url") or "https://api.openai.com/v1").rstrip("/")
        var = config.get("openai_api_key_env") or "OPENAI_API_KEY"
        self._api_key_var = var
        self.api_key = config.get("openai_api_key") or os.environ.get(var, "")

    def disponble(self) -> tuple[bool, str]:
        if not self.api_key:
            return False, (
                f"Falta la clau de l'API: defineix la variable d'entorn "
                f"{self._api_key_var} (o «openai_api_key» a config.json). "
                "Mai escrigues la clau dins del codi ni la puges al repositori."
            )
        return True, ""

    def chat(self, system: str, user: str) -> str:
        ok, reason = self.disponble()
        if not ok:
            raise IAError(reason)
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "temperature": 0.2,
                },
                timeout=(DEFAULT_TIMEOUT_CONNECT, DEFAULT_TIMEOUT_GENERATE),
            )
            response.raise_for_status()
        except requests.RequestException as error:
            raise IAError(f"No s'ha pogut parlar amb {self.base_url}: {error}")
        try:
            return response.json()["choices"][0]["message"]["content"]
        except (KeyError, IndexError, ValueError) as error:
            raise IAError(f"Resposta inesperada de l'API: {error}")
