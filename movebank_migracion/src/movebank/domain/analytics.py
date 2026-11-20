from typing import Any

import pandas as pd
from geopy.distance import geodesic

from movebank.domain.models import Event


def segments(rows: list[dict[str, Any]], max_gap_hours: float = 24) -> pd.DataFrame:
    if max_gap_hours <= 0:
        raise ValueError("La separacion maxima debe ser positiva.")
    columns = ["individual_id", "timestamp", "distance_km", "hours", "speed_kmh"]
    if not rows:
        return pd.DataFrame(columns=columns)
    frame = pd.DataFrame(rows)
    frame = frame[frame["visible"] != False].copy()
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True, format="ISO8601")
    frame = frame.sort_values(["individual_id", "timestamp"])
    result = []
    for individual_id, group in frame.groupby("individual_id"):
        previous: Event | None = None
        for raw in group.to_dict(orient="records"):
            row = Event.model_validate(raw)
            if previous is not None:
                hours = (row.timestamp - previous.timestamp).total_seconds() / 3600
                if 0 < hours <= max_gap_hours:
                    distance = geodesic(
                        (previous.location_lat, previous.location_long),
                        (row.location_lat, row.location_long),
                    ).km
                    result.append((individual_id, row.timestamp, distance, hours, distance / hours))
            previous = row
    return pd.DataFrame(result, columns=columns)


def mobility(
    rows: list[dict[str, Any]], stop_threshold_kmh: float = 1.0, max_gap_hours: float = 24
) -> dict[str, float | int | None]:
    if stop_threshold_kmh < 0:
        raise ValueError("El umbral no puede ser negativo.")
    valid = [row for row in rows if row.get("visible") is not False]
    track = segments(valid, max_gap_hours)
    hours = float(track["hours"].sum())
    distance = float(track["distance_km"].sum())
    timestamps = pd.to_datetime([row["timestamp"] for row in valid], utc=True, format="ISO8601")
    return {
        "individuals": len({row["individual_id"] for row in valid}),
        "species": len(
            {
                row.get("individual_taxon_canonical_name")
                for row in valid
                if row.get("individual_taxon_canonical_name")
            }
        ),
        "positions": len(valid),
        "tracking_span_hours": (
            float((timestamps.max() - timestamps.min()).total_seconds() / 3600)
            if len(timestamps)
            else 0.0
        ),
        "distance_km": distance,
        "mean_segment_km": distance / len(track) if len(track) else None,
        "mean_speed_kmh": distance / hours if hours else None,
        "max_speed_kmh": float(track["speed_kmh"].max()) if len(track) else None,
        "stopped_hours": float(track.loc[track["speed_kmh"] < stop_threshold_kmh, "hours"].sum()),
        "moving_hours": float(track.loc[track["speed_kmh"] >= stop_threshold_kmh, "hours"].sum()),
    }


def daily_distance(rows: list[dict[str, Any]], max_gap_hours: float = 24) -> pd.DataFrame:
    track = segments(rows, max_gap_hours)
    if track.empty:
        return pd.DataFrame(columns=["individual_id", "date", "distance_km"])
    track["date"] = track["timestamp"].dt.date
    return track.groupby(["individual_id", "date"], as_index=False).agg(
        distance_km=("distance_km", "sum")
    )
