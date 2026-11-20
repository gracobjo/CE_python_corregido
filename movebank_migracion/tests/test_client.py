import hashlib

import pytest
import requests

from movebank.infrastructure.movebank.client import LicenseRequired, MovebankClient, MovebankError
from movebank.infrastructure.movebank.services import (
    MovebankEventService,
    MovebankIndividualService,
    MovebankStudyService,
)


def response(content: bytes, status: int = 200) -> requests.Response:
    result = requests.Response()
    result.status_code = status
    result._content = content
    result.url = "https://www.movebank.org"
    return result


def test_csv_and_services(monkeypatch):
    client = MovebankClient(interval=0)
    calls = []

    def get(url, params, timeout):
        calls.append(params)
        if params["entity_type"] == "study":
            return response(b"id,name\n1,Study\n")
        if params["entity_type"] == "individual":
            return response(b"id,local_identifier\n2,Bird\n")
        return response(
            b"event_id,individual_id,timestamp,location_lat,location_long,visible,individual_taxon_canonical_name\n"
        )

    monkeypatch.setattr(client.session, "get", get)
    assert MovebankStudyService(client).list()[0]["id"] == "1"
    assert MovebankIndividualService(client).list(1)[0]["id"] == "2"
    assert MovebankEventService(client).list(1, 2) == []
    assert calls[-1]["sensor_type_id"] == 653
    assert calls[-1]["individual_id"] == 2
    client.close()


def test_license_requires_explicit_matching_consent(monkeypatch):
    client = MovebankClient(interval=0)
    terms = b"<html>License Terms: test</html>"
    digest = hashlib.md5(terms, usedforsecurity=False).hexdigest()
    calls = []

    def get(url, params, timeout):
        calls.append(params)
        if params.get("license-md5") == digest:
            return response(b"id,name\n1,Study\n")
        return response(terms)

    monkeypatch.setattr(client.session, "get", get)
    with pytest.raises(LicenseRequired) as exc:
        client.read({"entity_type": "study"})
    assert exc.value.md5 == digest
    with pytest.raises(LicenseRequired):
        client.read({"entity_type": "study"}, "wrong")
    assert client.read({"entity_type": "study"}, digest)[0]["id"] == "1"
    assert calls[-1]["license-md5"] == digest
    client.close()


@pytest.mark.parametrize(
    "body", [b"<html>failed</html>", b"wrong,columns\nx,y", b"id,name\n1,a,extra", b"id,name\n1"]
)
def test_invalid_responses_are_errors(monkeypatch, body):
    client = MovebankClient(interval=0)
    monkeypatch.setattr(client.session, "get", lambda *a, **k: response(body))
    with pytest.raises(MovebankError):
        client.read({"entity_type": "study"})


def test_http_and_configuration_errors(monkeypatch):
    with pytest.raises(ValueError):
        MovebankClient("user", None)
    with pytest.raises(ValueError):
        MovebankClient(interval=-1)
    client = MovebankClient(interval=0)
    monkeypatch.setattr(client.session, "get", lambda *a, **k: response(b"unauthorized", 401))
    with pytest.raises(MovebankError):
        client.read({"entity_type": "study"})
