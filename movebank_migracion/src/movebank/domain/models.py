from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Event(BaseModel):
    model_config = ConfigDict(extra="ignore")

    event_id: int
    individual_id: int | None = None
    individual_local_identifier: str | None = None
    individual_taxon_canonical_name: str | None = None
    timestamp: datetime
    location_lat: float = Field(ge=-90, le=90)
    location_long: float = Field(ge=-180, le=180)
    visible: bool | None = None

    @field_validator(
        "individual_id",
        "individual_local_identifier",
        "individual_taxon_canonical_name",
        "visible",
        mode="before",
    )
    @classmethod
    def empty_is_none(cls, value: object) -> object:
        return None if value == "" else value

    @field_validator("timestamp")
    @classmethod
    def as_utc(cls, value: datetime) -> datetime:
        from datetime import UTC

        return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


class Study(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int
    name: str


class Individual(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int
    local_identifier: str
