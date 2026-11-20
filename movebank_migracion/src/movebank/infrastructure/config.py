import os
from pathlib import Path

from dotenv import dotenv_values

from movebank.application.sync import Sync
from movebank.infrastructure.movebank.client import MovebankClient
from movebank.infrastructure.movebank.services import (
    MovebankEventService,
    MovebankIndividualService,
    MovebankStudyService,
)
from movebank.infrastructure.persistence.store import Store


def credentials() -> tuple[str | None, str | None]:
    values = dotenv_values(Path.cwd() / ".env", interpolate=False)
    return (
        os.environ.get("MOVEBANK_USERNAME", values.get("MOVEBANK_USERNAME")),
        os.environ.get("MOVEBANK_PASSWORD", values.get("MOVEBANK_PASSWORD")),
    )


def build_sync(client: MovebankClient, store: Store) -> Sync:
    return Sync(
        MovebankStudyService(client),
        MovebankIndividualService(client),
        MovebankEventService(client),
        store,
    )
