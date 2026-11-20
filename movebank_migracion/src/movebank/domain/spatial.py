import json
from pathlib import Path
from typing import Any

from pyproj import CRS, Transformer
from shapely.geometry import MultiPoint, Point, shape
from shapely.ops import transform


def area_and_density(rows: list[dict[str, Any]]) -> tuple[float | None, float | None]:
    points = [
        (float(r["location_long"]), float(r["location_lat"]))
        for r in rows
        if r.get("visible") is not False
    ]
    if len(points) < 3:
        return None, None
    if max(x for x, _ in points) - min(x for x, _ in points) > 180:
        raise ValueError("El area no se calcula para trayectorias que cruzan el antimeridiano.")
    lon = sum(p[0] for p in points) / len(points)
    lat = sum(p[1] for p in points) / len(points)
    local = CRS.from_proj4(f"+proj=laea +lat_0={lat} +lon_0={lon} +datum=WGS84 +units=m")
    projection = Transformer.from_crs("EPSG:4326", local, always_xy=True)
    polygon = transform(projection.transform, MultiPoint(points)).convex_hull
    area = polygon.area / 1_000_000
    return area, len(points) / area if area > 0 else None


def visited_regions(
    rows: list[dict[str, Any]], geojson_path: str | Path, country_field: str, region_field: str
) -> tuple[set[str], set[str]]:
    with Path(geojson_path).open(encoding="utf-8") as file:
        data = json.load(file)
    if data.get("type") != "FeatureCollection":
        raise ValueError("Se requiere una coleccion GeoJSON en WGS84.")
    if "crs" in data:
        raise ValueError("El GeoJSON debe usar WGS84 sin CRS explicito.")
    countries: set[str] = set()
    regions: set[str] = set()
    features = [(shape(f["geometry"]), f["properties"]) for f in data["features"]]
    if features and not all(
        country_field in props and region_field in props for _, props in features
    ):
        raise ValueError("Faltan los campos de pais o region en el GeoJSON.")
    for row in rows:
        if row.get("visible") is False:
            continue
        point = Point(row["location_long"], row["location_lat"])
        for geometry, props in features:
            if geometry.covers(point):
                if props.get(country_field):
                    countries.add(str(props[country_field]))
                if props.get(region_field):
                    regions.add(str(props[region_field]))
    return countries, regions
