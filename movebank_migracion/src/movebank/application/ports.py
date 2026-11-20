from typing import Protocol


class StudyReader(Protocol):
    def list(self) -> list[dict[str, str]]: ...


class IndividualReader(Protocol):
    def list(self, study_id: int, approved_md5: str | None = None) -> list[dict[str, str]]: ...


class EventReader(Protocol):
    def list(
        self, study_id: int, individual_id: int, approved_md5: str | None = None
    ) -> list[dict[str, str]]: ...


class SyncStore(Protocol):
    def save_studies(self, rows: list[dict[str, str]]) -> None: ...

    def save_individuals(self, study_id: int, rows: list[dict[str, str]]) -> None: ...

    def save_events(self, study_id: int, individual_id: int, rows: list[dict[str, str]]) -> int: ...

    def has_events(self, study_id: int, individual_id: int) -> bool: ...
