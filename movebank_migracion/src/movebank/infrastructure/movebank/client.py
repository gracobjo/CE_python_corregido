import csv
import hashlib
import io
import logging
import threading
import time
from collections.abc import Mapping

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)
URL = "https://www.movebank.org/movebank/service/direct-read"
_request_lock = threading.Lock()
_last_request = 0.0


class MovebankError(Exception):
    pass


class LicenseRequired(MovebankError):
    def __init__(self, content: bytes):
        self.content = content
        self.md5 = hashlib.md5(content, usedforsecurity=False).hexdigest()
        super().__init__("Movebank requiere aceptar los terminos del estudio.")


class MovebankClient:
    def __init__(
        self,
        username: str | None = None,
        password: str | None = None,
        interval: float = 1.0,
    ) -> None:
        if bool(username) != bool(password):
            raise ValueError("Debe proporcionar usuario y contrasena juntos.")
        if interval < 0:
            raise ValueError("El intervalo no puede ser negativo.")
        self.session = requests.Session()
        if username and password:
            self.session.auth = (username, password)
        retry = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
            respect_retry_after_header=True,
        )
        self.session.mount("https://", HTTPAdapter(max_retries=retry))
        self.interval = interval

    def close(self) -> None:
        self.session.close()

    def _get(self, params: Mapping[str, str | int]) -> bytes:
        global _last_request
        try:
            with _request_lock:
                delay = self.interval - (time.monotonic() - _last_request)
                if delay > 0:
                    time.sleep(delay)
                try:
                    response = self.session.get(URL, params=params, timeout=(15, 120))
                finally:
                    _last_request = time.monotonic()
                response.raise_for_status()
                content = response.content
        except requests.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else "desconocido"
            logger.warning("Movebank devolvio HTTP %s", status)
            raise MovebankError(f"Movebank devolvio HTTP {status}.") from exc
        except requests.RequestException as exc:
            logger.warning("Error HTTP al consultar Movebank: %s", type(exc).__name__)
            raise MovebankError(f"Error al consultar Movebank: {type(exc).__name__}") from exc
        return content

    def read(
        self, params: Mapping[str, str | int], approved_md5: str | None = None
    ) -> list[dict[str, str]]:
        content = self._get(params)
        if b"License Terms:" in content:
            license_request = LicenseRequired(content)
            if approved_md5 != license_request.md5:
                raise license_request
            content = self._get({**params, "license-md5": approved_md5})
            if b"License Terms:" in content:
                raise LicenseRequired(content)
        try:
            text = content.decode("utf-8-sig")
            reader = csv.DictReader(io.StringIO(text, newline=""), strict=True)
            if not reader.fieldnames or len(reader.fieldnames) < 2:
                raise MovebankError("Movebank devolvio una respuesta que no es CSV valido.")
            required = {
                "study": {"id", "name"},
                "individual": {"id", "local_identifier"},
                "event": {
                    "event_id",
                    "individual_id",
                    "timestamp",
                    "location_lat",
                    "location_long",
                    "visible",
                    "individual_taxon_canonical_name",
                },
            }.get(str(params.get("entity_type")), set())
            if not required.issubset(reader.fieldnames):
                raise MovebankError("Movebank devolvio un CSV sin los campos esperados.")
            rows = list(reader)
            if any(None in row or any(value is None for value in row.values()) for row in rows):
                raise MovebankError("Movebank devolvio filas CSV malformadas.")
            logger.info("Movebank: %s, %d filas", params.get("entity_type"), len(rows))
            return rows
        except (UnicodeDecodeError, csv.Error) as exc:
            raise MovebankError("No se pudo interpretar el CSV de Movebank.") from exc
