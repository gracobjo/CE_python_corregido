import argparse
import hashlib
import logging
from collections.abc import Callable
from pathlib import Path

from movebank.infrastructure.config import build_sync, credentials
from movebank.infrastructure.movebank.client import LicenseRequired, MovebankClient
from movebank.infrastructure.persistence.store import Store


def database_path(username: str | None) -> Path:
    identity = hashlib.sha256((username or "anonymous").encode()).hexdigest()[:16]
    return Path(f"movebank-{identity}.sqlite3")


def with_consent(action: Callable[[str | None], object]) -> object:
    try:
        return action(None)
    except LicenseRequired as license_request:
        print(license_request.content.decode("utf-8", errors="replace"))
        print(f"MD5: {license_request.md5}")
        if input("Escriba ACEPTO para aceptar estos terminos: ").strip() != "ACEPTO":
            raise SystemExit("Licencia no aceptada; no se han descargado los datos.")
        return action(license_request.md5)


def main() -> None:
    parser = argparse.ArgumentParser(description="Descarga datos de Movebank a una cache local.")
    parser.add_argument("command", choices=["studies", "individuals", "events"])
    parser.add_argument("--study", type=int)
    parser.add_argument("--individual", type=int)
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--database", type=Path)
    args = parser.parse_args()
    if args.command in {"individuals", "events"} and args.study is None:
        parser.error("--study es obligatorio")
    if args.command == "events" and args.individual is None:
        parser.error("--individual es obligatorio")
    logging.basicConfig(level=logging.INFO)
    username, password = credentials()
    client = MovebankClient(username, password)
    store = Store(args.database or database_path(username))
    sync = build_sync(client, store)
    try:
        if args.command == "studies":
            sync.studies()
            print(f"Estudios: {len(store.get_studies())}")
        elif args.command == "individuals":
            with_consent(lambda md5: sync.individuals(args.study, md5))
            print(f"Individuos: {len(store.get_individuals(args.study))}")
        else:
            downloaded = with_consent(
                lambda md5: sync.events(args.study, args.individual, md5, args.refresh)
            )
            print("Descarga actualizada." if downloaded else "Se utilizo la cache existente.")
    finally:
        client.close()


if __name__ == "__main__":
    main()
