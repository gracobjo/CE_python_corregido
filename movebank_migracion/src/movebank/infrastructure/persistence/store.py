from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import (
    JSON,
    Column,
    Float,
    Integer,
    MetaData,
    String,
    Table,
    create_engine,
    delete,
    select,
)
from sqlalchemy.pool import NullPool

from movebank.domain.models import Event, Individual, Study

metadata = MetaData()
studies = Table(
    "studies",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("data", JSON, nullable=False),
)
individuals = Table(
    "individuals",
    metadata,
    Column("study_id", Integer, primary_key=True),
    Column("id", Integer, primary_key=True),
    Column("data", JSON, nullable=False),
)
events = Table(
    "events",
    metadata,
    Column("study_id", Integer, primary_key=True),
    Column("event_id", Integer, primary_key=True),
    Column("individual_id", Integer, nullable=False),
    Column("timestamp", String, nullable=False),
    Column("latitude", Float, nullable=False),
    Column("longitude", Float, nullable=False),
    Column("data", JSON, nullable=False),
)
downloads = Table(
    "downloads",
    metadata,
    Column("study_id", Integer, primary_key=True),
    Column("individual_id", Integer, primary_key=True),
    Column("downloaded_at", String, nullable=False),
)


class Store:
    def __init__(self, path: str | Path):
        self.engine = create_engine(f"sqlite:///{Path(path).absolute()}", poolclass=NullPool)
        metadata.create_all(self.engine)

    def save_studies(self, rows: list[dict[str, str]]) -> None:
        validated = [Study.model_validate(row) for row in rows]
        with self.engine.begin() as conn:
            conn.execute(delete(studies))
            if validated:
                conn.execute(
                    studies.insert(),
                    [{"id": x.id, "data": x.model_dump(mode="json")} for x in validated],
                )

    def get_studies(self) -> list[dict[str, str]]:
        with self.engine.connect() as conn:
            return list(conn.execute(select(studies.c.data)).scalars())

    def save_individuals(self, study_id: int, rows: list[dict[str, str]]) -> None:
        validated = [Individual.model_validate(row) for row in rows]
        with self.engine.begin() as conn:
            conn.execute(delete(individuals).where(individuals.c.study_id == study_id))
            if validated:
                conn.execute(
                    individuals.insert(),
                    [
                        {"study_id": study_id, "id": x.id, "data": x.model_dump(mode="json")}
                        for x in validated
                    ],
                )

    def get_individuals(self, study_id: int) -> list[dict[str, str]]:
        with self.engine.connect() as conn:
            return list(
                conn.execute(
                    select(individuals.c.data).where(individuals.c.study_id == study_id)
                ).scalars()
            )

    def save_events(self, study_id: int, individual_id: int, rows: list[dict[str, str]]) -> int:
        # Movebank may return sensor records without a location.
        located = [
            row
            for row in rows
            if row.get("location_lat") not in (None, "")
            and row.get("location_long") not in (None, "")
        ]
        validated = [Event.model_validate(row) for row in located]
        if any(event.individual_id != individual_id for event in validated):
            raise ValueError("La respuesta contiene eventos de otro individuo o sin identificador.")
        values = [
            {
                "study_id": study_id,
                "event_id": x.event_id,
                "individual_id": individual_id,
                "timestamp": x.timestamp.isoformat(),
                "latitude": x.location_lat,
                "longitude": x.location_long,
                "data": x.model_dump(mode="json"),
            }
            for x in validated
        ]
        with self.engine.begin() as conn:
            conn.execute(
                delete(events).where(
                    events.c.study_id == study_id, events.c.individual_id == individual_id
                )
            )
            conn.execute(
                delete(downloads).where(
                    downloads.c.study_id == study_id, downloads.c.individual_id == individual_id
                )
            )
            if values:
                conn.execute(events.insert(), values)
            conn.execute(
                downloads.insert().values(
                    study_id=study_id,
                    individual_id=individual_id,
                    downloaded_at=datetime.now(UTC).isoformat(),
                )
            )
        return len(rows) - len(located)

    def has_events(self, study_id: int, individual_id: int) -> bool:
        with self.engine.connect() as conn:
            return (
                conn.execute(
                    select(downloads.c.study_id).where(
                        downloads.c.study_id == study_id, downloads.c.individual_id == individual_id
                    )
                ).first()
                is not None
            )

    def get_events(self, study_id: int, individual_id: int | None = None) -> list[dict]:
        query = select(events.c.data).where(events.c.study_id == study_id)
        if individual_id is not None:
            query = query.where(events.c.individual_id == individual_id)
        with self.engine.connect() as conn:
            return list(conn.execute(query.order_by(events.c.timestamp)).scalars())
