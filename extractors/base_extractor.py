"""
Extractor base para o Portal da Transparência.
Implementa: rate limiting, retry com backoff exponencial,
paginação automática e checkpoint de resumo.
"""

from __future__ import annotations

import os
import time
import json
import threading
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Generator

import requests
from loguru import logger
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)
import logging


# ─── Configuração ─────────────────────────────────────────────────────────────

BASE_URL = os.getenv("TRANSPARENCIA_BASE_URL", "https://api.portaldatransparencia.gov.br/api-de-dados")
API_KEY = os.getenv("TRANSPARENCIA_API_KEY", "")

# Limites por horário (Portal da Transparência)
# 00:00–06:00 → 700 req/min  |  resto → 400 req/min  |  APIs restritas → 180 req/min
RATE_RESTRICTED = 180   # req/min para APIs restritas
RATE_NORMAL = 400       # req/min para APIs normais
RATE_NOCTURNAL = 700    # req/min das 00h às 06h

RESTRICTED_PATHS = {
    "despesas/documentos-por-favorecido",
    "bolsa-familia-disponivel-por-cpf-ou-nis",
    "bolsa-familia-por-municipio",
    "bolsa-familia-sacado-por-nis",
    "auxilio-emergencial-beneficiario-por-municipio",
    "auxilio-emergencial-por-cpf-ou-nis",
    "auxilio-emergencial-por-municipio",
    "seguro-defeso-codigo",
}


class RateLimiter:
    """Token bucket thread-safe para respeitar os limites da API."""

    def __init__(self, calls_per_minute: int):
        self._calls_per_minute = calls_per_minute
        self._min_interval = 60.0 / calls_per_minute
        self._lock = threading.Lock()
        self._last_call = 0.0

    def wait(self):
        with self._lock:
            elapsed = time.monotonic() - self._last_call
            sleep_for = self._min_interval - elapsed
            if sleep_for > 0:
                time.sleep(sleep_for)
            self._last_call = time.monotonic()

    def update_limit(self, calls_per_minute: int):
        with self._lock:
            self._calls_per_minute = calls_per_minute
            self._min_interval = 60.0 / calls_per_minute


def _get_rate_limit(endpoint_path: str) -> int:
    """Retorna o limite de requisições por minuto conforme horário e endpoint."""
    hour = datetime.now().hour
    is_nocturnal = 0 <= hour < 6
    is_restricted = any(p in endpoint_path for p in RESTRICTED_PATHS)

    if is_restricted:
        return RATE_RESTRICTED
    if is_nocturnal:
        return RATE_NOCTURNAL
    return RATE_NORMAL


# ─── Extractor base ───────────────────────────────────────────────────────────

class BaseExtractor(ABC):

    PAGE_SIZE = 200  # máximo aceito pela API

    def __init__(self, endpoint: str, checkpoint_dir: str = "data/checkpoints"):
        self.endpoint = endpoint.lstrip("/")
        self.url = f"{BASE_URL}/{self.endpoint}"
        self.session = self._build_session()
        self.rate_limiter = RateLimiter(_get_rate_limit(self.endpoint))
        self.checkpoint_path = Path(checkpoint_dir) / f"{self.endpoint.replace('/', '_')}.json"
        self.checkpoint_path.parent.mkdir(parents=True, exist_ok=True)

    def _build_session(self) -> requests.Session:
        session = requests.Session()
        session.headers.update({
            "chave-api-dados": API_KEY,
            "Accept": "application/json",
            "User-Agent": "beneficios-ao-cidadao-elt/1.0",
        })
        return session

    @retry(
        stop=stop_after_attempt(7),
        wait=wait_exponential(multiplier=2, min=4, max=120),
        retry=retry_if_exception_type((requests.Timeout, requests.ConnectionError)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    def _get(self, params: dict[str, Any]) -> list[dict]:
        """Faz uma requisição GET com rate limiting e retry automático."""
        self.rate_limiter.update_limit(_get_rate_limit(self.endpoint))
        self.rate_limiter.wait()

        response = self.session.get(self.url, params=params, timeout=30)

        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 60))
            logger.warning(f"Rate limit atingido. Aguardando {retry_after}s...")
            time.sleep(retry_after)
            raise requests.ConnectionError("Rate limit — retrying")

        if response.status_code == 503:
            logger.warning("API indisponível (503). Aguardando 30s...")
            time.sleep(30)
            raise requests.ConnectionError("Service unavailable — retrying")

        response.raise_for_status()
        return response.json()

    def paginate(self, params: dict[str, Any]) -> Generator[list[dict], None, None]:
        """Itera sobre todas as páginas de um endpoint."""
        page = 1
        params = {**params, "pagina": page}

        while True:
            params["pagina"] = page
            logger.debug(f"{self.endpoint} | params={params}")

            data = self._get(params)

            if not data:
                logger.info(f"{self.endpoint} | página {page} vazia — fim da paginação")
                break

            yield data
            logger.info(f"{self.endpoint} | página {page} → {len(data)} registros")

            if len(data) < self.PAGE_SIZE:
                break

            page += 1

    # ─── Checkpoint (resumo) ──────────────────────────────────────────────────

    def load_checkpoint(self) -> dict:
        if self.checkpoint_path.exists():
            return json.loads(self.checkpoint_path.read_text(encoding="utf-8"))
        return {}

    def save_checkpoint(self, state: dict):
        self.checkpoint_path.write_text(
            json.dumps(state, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def is_already_extracted(self, key: str) -> bool:
        return self.load_checkpoint().get(key) == "done"

    def mark_done(self, key: str):
        state = self.load_checkpoint()
        state[key] = "done"
        self.save_checkpoint(state)

    # ─── Interface obrigatória ────────────────────────────────────────────────

    @abstractmethod
    def extract(self, **kwargs) -> Generator[list[dict], None, None]:
        """Yields batches de registros extraídos da API."""
        ...

    @property
    @abstractmethod
    def nome(self) -> str:
        """Nome legível do extractor (ex: 'bolsa_familia')."""
        ...
