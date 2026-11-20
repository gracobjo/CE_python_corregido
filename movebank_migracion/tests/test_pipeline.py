import json

import pytest
from pydantic import ValidationError

from movebank.domain.analytics import daily_distance, mobility, segments
from movebank.domain.spatial import area_and_density, visited_regions
from movebank.infrastructure.config import build_sync
from movebank.infrastructure.persistence.store import Store


def event(id, individual, timestamp, lat, lon, visible=True):
    return {
        "event_id": id,
        "individual_id": individual,
        "timestamp": timestamp,
        "location_lat": lat,
        "location_long": lon,
        "visible": visible,
        "individual_taxon_canonical_name": "Species",
    }


def test_persistence_atomic_replace_and_cache(tmp_path):
    store = Store(tmp_path / "test.sqlite3")
    store.save_studies([{"id": "1", "name": "Study"}])
    store.save_individuals(1, [{"id": "2", "local_identifier": "bird"}])
    rows = [
        event(10, 2, "2024-01-01T00:00:00Z", 0, 0),
        event(11, 2, "2024-01-01T01:00:00Z", "", ""),
    ]
    assert store.save_events(1, 2, rows) == 1
    assert store.has_events(1, 2)
    assert len(store.get_events(1, 2)) == 1
    with pytest.raises(ValidationError):
        store.save_events(1, 2, [event(12, 2, "2024-01-01T00:00:00Z", 999, 0)])
    assert len(store.get_events(1)) == 1
    with pytest.raises(ValueError):
        store.save_events(1, 2, [event(13, 3, "2024-01-01T00:00:00Z", 0, 0)])
    assert store.get_studies()[0]["name"] == "Study"
    assert store.get_individuals(1)[0]["local_identifier"] == "bird"
    store.save_events(1, 2, [])
    assert store.has_events(1, 2)
    assert store.get_events(1) == []


def test_mobility_separates_animals_gaps_and_outliers():
    rows = [
        event(1, 1, "2024-01-01T00:00:00Z", 0, 0),
        event(2, 1, "2024-01-01T01:00:00Z", 0, 1),
        event(3, 1, "2024-01-03T00:00:00Z", 0, 3),
        event(4, 2, "2024-01-01T00:00:00Z", 20, 20),
        event(5, 1, "2024-01-01T00:30:00Z", 80, 80, False),
    ]
    result = mobility(rows, stop_threshold_kmh=120, max_gap_hours=24)
    assert result["positions"] == 4
    assert result["individuals"] == 2
    assert result["species"] == 1
    assert result["distance_km"] == pytest.approx(111.319, abs=0.01)
    assert result["stopped_hours"] == 1
    assert result["moving_hours"] == 0
    assert len(daily_distance(rows)) == 1
    assert mobility([])["mean_speed_kmh"] is None
    assert segments([]).empty
    with pytest.raises(ValueError):
        segments(rows, 0)
    with pytest.raises(ValueError):
        mobility(rows, -1)


def test_mixed_timestamp_precision():
    rows = [
        event(1, 1, "2024-01-01T00:00:00.500Z", 0, 0),
        event(2, 1, "2024-01-01T01:00:00Z", 0, 1),
    ]
    assert mobility(rows)["positions"] == 2
    assert mobility(rows)["tracking_span_hours"] == pytest.approx(3599.5 / 3600)
    assert daily_distance(rows)["distance_km"].iloc[0] == pytest.approx(111.319, abs=0.01)


def test_spatial_geojson_and_area(tmp_path):
    rows = [
        event(1, 1, "2024-01-01T00:00:00Z", 0, 0),
        event(2, 1, "2024-01-01T01:00:00Z", 0, 1),
        event(3, 1, "2024-01-01T02:00:00Z", 1, 0),
    ]
    area, density = area_and_density(rows)
    assert area == pytest.approx(6154, rel=0.02)
    assert density == pytest.approx(3 / area)
    assert area_and_density(rows[:2]) == (None, None)
    path = tmp_path / "boundaries.geojson"
    path.write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": {"country": "A", "region": "B"},
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [[[-1, -1], [2, -1], [2, 2], [-1, 2], [-1, -1]]],
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    assert visited_regions(rows, path, "country", "region") == ({"A"}, {"B"})
    with pytest.raises(ValueError):
        visited_regions(rows, path, "missing", "region")
    with pytest.raises(ValueError):
        area_and_density(
            [
                event(1, 1, "2024-01-01T00:00:00Z", 0, 179),
                event(2, 1, "2024-01-01T01:00:00Z", 0, -179),
                event(3, 1, "2024-01-01T02:00:00Z", 1, 179),
            ]
        )


class FakeClient:
    def __init__(self):
        self.calls = []

    def read(self, params, approved_md5=None):
        self.calls.append(params)
        if params["entity_type"] == "study":
            return [{"id": "1", "name": "Study"}]
        if params["entity_type"] == "individual":
            return [{"id": "2", "local_identifier": "bird"}]
        return [event(1, 2, "2024-01-01T00:00:00Z", 0, 0)]


def test_sync_uses_cache_and_refresh(tmp_path):
    client = FakeClient()
    store = Store(tmp_path / "test.sqlite3")
    sync = build_sync(client, store)
    sync.studies()
    sync.individuals(1)
    assert sync.events(1, 2)
    assert not sync.events(1, 2)
    assert sync.events(1, 2, refresh=True)
    assert len(client.calls) == 4
