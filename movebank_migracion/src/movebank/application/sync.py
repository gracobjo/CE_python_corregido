import logging

from movebank.application.ports import EventReader, IndividualReader, StudyReader, SyncStore

logger = logging.getLogger(__name__)


class Sync:
    def __init__(
        self,
        studies: StudyReader,
        individuals: IndividualReader,
        events: EventReader,
        store: SyncStore,
    ):
        self.study_reader = studies
        self.individual_reader = individuals
        self.event_reader = events
        self.store = store

    def studies(self) -> None:
        self.store.save_studies(self.study_reader.list())

    def individuals(self, study_id: int, approved_md5: str | None = None) -> None:
        self.store.save_individuals(study_id, self.individual_reader.list(study_id, approved_md5))

    def events(
        self,
        study_id: int,
        individual_id: int,
        approved_md5: str | None = None,
        refresh: bool = False,
    ) -> bool:
        if not refresh and self.store.has_events(study_id, individual_id):
            return False
        rows = self.event_reader.list(study_id, individual_id, approved_md5)
        skipped = self.store.save_events(study_id, individual_id, rows)
        if skipped:
            logger.warning("Se omitieron %d eventos sin coordenadas GPS.", skipped)
        return True
