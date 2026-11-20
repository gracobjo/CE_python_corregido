import sys
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from movebank.application import cli
from movebank.infrastructure.config import credentials
from movebank.infrastructure.movebank.client import LicenseRequired
from movebank.infrastructure.persistence.store import Store


class Client:
    def __init__(self):
        self.closed = False

    def read(self, params, approved_md5=None):
        if params["entity_type"] == "study":
            return [{"id": "1", "name": "Study", "sensor_type_ids": "GPS"}]
        if params["entity_type"] == "individual":
            return [{"id": "2", "local_identifier": "bird"}]
        return [
            {
                "event_id": "1",
                "individual_id": "2",
                "timestamp": "2024-01-01T00:00:00.500Z",
                "location_lat": "0",
                "location_long": "0",
                "visible": "true",
                "individual_taxon_canonical_name": "Bird",
            },
            {
                "event_id": "2",
                "individual_id": "2",
                "timestamp": "2024-01-01T01:00:00Z",
                "location_lat": "0",
                "location_long": "1",
                "visible": "true",
                "individual_taxon_canonical_name": "Bird",
            },
        ]

    def close(self):
        self.closed = True


def test_credentials_from_dotenv_and_environment(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("MOVEBANK_USERNAME", raising=False)
    monkeypatch.delenv("MOVEBANK_PASSWORD", raising=False)
    assert credentials() == (None, None)
    (tmp_path / ".env").write_text(
        "MOVEBANK_USERNAME='local-user'\nMOVEBANK_PASSWORD='value$with#characters'\n",
        encoding="utf-8",
    )
    assert credentials() == ("local-user", "value$with#characters")
    monkeypatch.setenv("MOVEBANK_USERNAME", "environment-user")
    monkeypatch.setenv("MOVEBANK_PASSWORD", "environment-password")
    assert credentials() == ("environment-user", "environment-password")


def test_cli_sync_and_consent(tmp_path, monkeypatch, capsys):
    client = Client()
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("MOVEBANK_USERNAME", raising=False)
    monkeypatch.delenv("MOVEBANK_PASSWORD", raising=False)
    monkeypatch.setattr(cli, "MovebankClient", lambda *args: client)
    for args in [
        ["studies"],
        ["individuals", "--study", "1"],
        ["events", "--study", "1", "--individual", "2"],
    ]:
        monkeypatch.setattr(sys, "argv", ["movebank-load", *args])
        cli.main()
    assert client.closed
    assert "Descarga actualizada" in capsys.readouterr().out

    def action(md5):
        if not md5:
            raise LicenseRequired(b"License Terms: test")
        return md5

    monkeypatch.setattr("builtins.input", lambda _: "ACEPTO")
    assert cli.with_consent(action) == LicenseRequired(b"License Terms: test").md5
    monkeypatch.setattr("builtins.input", lambda _: "NO")
    with pytest.raises(SystemExit):
        cli.with_consent(action)


def test_streamlit_pages(tmp_path):
    store = Store(tmp_path / "ui.sqlite3")
    client = Client()
    store.save_studies(client.read({"entity_type": "study"}))
    store.save_individuals(1, client.read({"entity_type": "individual"}))
    store.save_events(1, 2, client.read({"entity_type": "event"}))
    app_path = (
        Path(__file__).parents[1] / "src" / "movebank" / "presentation" / "streamlit" / "app.py"
    )
    app = AppTest.from_file(str(app_path), default_timeout=120)
    app.session_state["client"] = client
    app.session_state["store"] = store
    app.run()
    assert not app.exception
    for page in ["Estudios", "Individuos", "Mapa", "Analitica"]:
        app.radio[0].set_value(page).run()
        assert not app.exception
