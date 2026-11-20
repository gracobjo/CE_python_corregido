from movebank.infrastructure.movebank.client import MovebankClient


class MovebankStudyService:
    def __init__(self, client: MovebankClient):
        self.client = client

    def list(self) -> list[dict[str, str]]:
        return self.client.read({"entity_type": "study", "i_have_download_access": "true"})


class MovebankIndividualService:
    def __init__(self, client: MovebankClient):
        self.client = client

    def list(self, study_id: int, approved_md5: str | None = None) -> list[dict[str, str]]:
        return self.client.read({"entity_type": "individual", "study_id": study_id}, approved_md5)


class MovebankEventService:
    def __init__(self, client: MovebankClient):
        self.client = client

    def list(
        self, study_id: int, individual_id: int, approved_md5: str | None = None
    ) -> list[dict[str, str]]:
        return self.client.read(
            {
                "entity_type": "event",
                "study_id": study_id,
                "individual_id": individual_id,
                "sensor_type_id": 653,
                "attributes": "event_id,individual_id,individual_local_identifier,individual_taxon_canonical_name,timestamp,location_lat,location_long,visible",
            },
            approved_md5,
        )
