import folium
import pandas as pd
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components
from folium.plugins import HeatMap, MarkerCluster

from movebank.application.cli import database_path
from movebank.domain.analytics import daily_distance, mobility
from movebank.domain.spatial import area_and_density, visited_regions
from movebank.infrastructure.config import build_sync, credentials
from movebank.infrastructure.movebank.client import LicenseRequired, MovebankClient, MovebankError
from movebank.infrastructure.persistence.store import Store

st.set_page_config(page_title="Migracion animal", layout="wide")
st.title("Migracion animal - Movebank")
st.caption("Datos de Movebank; respete las licencias y cite cada estudio.")

username, password = credentials()
if "client" not in st.session_state:
    st.session_state.client = MovebankClient(username, password)
    st.session_state.store = Store(database_path(username))
sync = build_sync(st.session_state.client, st.session_state.store)
store = st.session_state.store


def run_action(
    kind: str, study: int | None = None, individual: int | None = None, md5: str | None = None
) -> None:
    try:
        if kind == "studies":
            sync.studies()
        elif kind == "individuals" and study is not None:
            sync.individuals(study, md5)
        elif kind == "events" and study is not None and individual is not None:
            sync.events(study, individual, md5, refresh=True)
        else:
            raise ValueError("Accion incompleta.")
        st.session_state.pop("pending", None)
        st.success("Datos actualizados.")
    except LicenseRequired as exc:
        st.session_state.pending = (kind, study, individual, exc.content, exc.md5)
    except (MovebankError, ValueError) as exc:
        st.error(str(exc))


with st.sidebar:
    st.write("Credenciales: archivo .env o variables de entorno.")
    if st.button("Actualizar estudios"):
        run_action("studies")

if "pending" in st.session_state:
    kind, pending_study, pending_individual, content, md5 = st.session_state.pending
    st.warning(f"Lea los terminos antes de aceptarlos (MD5: {md5}).")
    st.text(content.decode("utf-8", errors="replace"))
    if st.button("Acepto estos terminos y descargar"):
        run_action(kind, pending_study, pending_individual, md5)
    if st.button("Cancelar licencia"):
        del st.session_state.pending
        st.rerun()

studies = store.get_studies()
if not studies:
    st.info("Actualice los estudios para comenzar.")
    st.stop()

study_table = pd.DataFrame(studies)
with st.sidebar:
    study_labels = {int(row["id"]): f'{row["name"]} ({row["id"]})' for row in studies}
    study_id = st.selectbox(
        "Estudio", list(study_labels), format_func=lambda key: study_labels[key]
    )
    if st.button("Actualizar individuos"):
        run_action("individuals", study_id)
    individuals = store.get_individuals(study_id)
    individual_labels = {
        int(row["id"]): f'{row["local_identifier"]} ({row["id"]})' for row in individuals
    }
    individual_id = (
        st.selectbox(
            "Individuo", list(individual_labels), format_func=lambda key: individual_labels[key]
        )
        if individual_labels
        else None
    )
    if individual_id is not None and st.button("Descargar o actualizar GPS"):
        run_action("events", study_id, individual_id)
    max_gap = st.number_input(
        "Intervalo maximo entre posiciones (horas)", min_value=0.1, value=24.0
    )
    threshold = st.number_input("Umbral detenido (km/h)", min_value=0.0, value=1.0)

rows = store.get_events(study_id)
page = st.sidebar.radio("Pagina", ["Resumen", "Estudios", "Individuos", "Mapa", "Analitica"])
valid = [row for row in rows if row.get("visible") is not False]

if page == "Resumen":
    result = mobility(rows, threshold, max_gap)
    for label, key in [
        ("Individuos", "individuals"),
        ("Especies", "species"),
        ("Posiciones", "positions"),
        ("Distancia (km)", "distance_km"),
    ]:
        st.metric(label, result[key])
    st.json(result)
    try:
        area, density = area_and_density(rows)
        st.write("Envolvente convexa (km²):", area, "| Posiciones/km²:", density)
    except ValueError as exc:
        st.warning(str(exc))
    st.caption(
        "Las distancias son geodesicas entre posiciones consecutivas; los intervalos largos se excluyen."
    )
elif page == "Estudios":
    species = st.text_input("Especie o taxon")
    year = st.text_input("Ano de seguimiento")
    sensor = st.text_input("Tipo de sensor")
    filtered = study_table
    for column, value in [("taxon_ids", species), ("sensor_type_ids", sensor)]:
        if value and column in filtered:
            filtered = filtered[
                filtered[column].fillna("").astype(str).str.contains(value, case=False, regex=False)
            ]
    if year:
        if not year.isdigit() or len(year) != 4:
            st.warning("Introduzca el ano con cuatro digitos.")
            filtered = filtered.iloc[0:0]
        elif {"timestamp_first_deployed_location", "timestamp_last_deployed_location"} <= set(
            filtered.columns
        ):
            start = pd.to_datetime(
                filtered["timestamp_first_deployed_location"],
                errors="coerce",
                utc=True,
                format="ISO8601",
            )
            end = pd.to_datetime(
                filtered["timestamp_last_deployed_location"],
                errors="coerce",
                utc=True,
                format="ISO8601",
            )
            filtered = filtered[(start.dt.year <= int(year)) & (end.dt.year >= int(year))]
        else:
            st.warning("El estudio no tiene fechas de seguimiento disponibles.")
            filtered = filtered.iloc[0:0]
    st.dataframe(filtered)
elif page == "Individuos":
    st.dataframe(pd.DataFrame(individuals))
    if individual_id is not None:
        st.json(next(row for row in individuals if int(row["id"]) == individual_id))
elif page == "Mapa":
    if not valid:
        st.info("Descargue posiciones GPS.")
    else:
        map_ = folium.Map(
            location=[valid[0]["location_lat"], valid[0]["location_long"]], zoom_start=4
        )
        paths = folium.FeatureGroup(name="Trayectorias")
        points = folium.FeatureGroup(name="Posiciones GPS")
        heat = folium.FeatureGroup(name="Mapa de calor")
        clusters = folium.FeatureGroup(name="Agrupaciones")
        cluster = MarkerCluster().add_to(clusters)
        frame = pd.DataFrame(valid)
        frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True, format="ISO8601")
        frame = frame.sort_values(["individual_id", "timestamp"])
        for _, group in frame.groupby("individual_id"):
            coords = group[["location_lat", "location_long"]].values.tolist()
            if len(coords) > 1:
                folium.PolyLine(coords).add_to(paths)
            for lat, lon in coords:
                folium.CircleMarker([lat, lon], radius=2).add_to(points)
                folium.Marker([lat, lon]).add_to(cluster)
        HeatMap(frame[["location_lat", "location_long"]].values.tolist()).add_to(heat)
        for layer in [paths, points, heat, clusters]:
            layer.add_to(map_)
        folium.LayerControl().add_to(map_)
        components.html(map_.get_root().render(), height=650)
elif page == "Analitica":
    if not valid:
        st.info("Descargue posiciones GPS.")
    else:
        daily = daily_distance(rows, max_gap)
        if not daily.empty:
            st.plotly_chart(
                px.line(
                    daily,
                    x="date",
                    y="distance_km",
                    color="individual_id",
                    title="Distancia diaria (asignada al dia final del intervalo)",
                )
            )
        frame = pd.DataFrame(valid)
        frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True, format="ISO8601")
        frame["mes"] = frame["timestamp"].dt.month
        frame["ano"] = frame["timestamp"].dt.year
        frame["estacion_norte"] = frame["mes"].map(
            {
                12: "Invierno",
                1: "Invierno",
                2: "Invierno",
                3: "Primavera",
                4: "Primavera",
                5: "Primavera",
                6: "Verano",
                7: "Verano",
                8: "Verano",
                9: "Otono",
                10: "Otono",
                11: "Otono",
            }
        )
        for column in ["mes", "estacion_norte", "ano", "individual_id"]:
            counts = frame.groupby(column).size().reset_index(name="posiciones")
            st.plotly_chart(px.bar(counts, x=column, y="posiciones"))
        st.caption(
            "Estaciones meteorologicas del hemisferio norte; actividad = numero de posiciones."
        )
    st.subheader("Limites administrativos locales")
    path = st.text_input("Ruta a GeoJSON WGS84")
    country = st.text_input("Campo de pais", "country")
    region = st.text_input("Campo de region", "region")
    if st.button("Calcular paises y regiones") and path:
        try:
            countries, regions = visited_regions(rows, path, country, region)
            st.write("Paises:", sorted(countries), "Regiones:", sorted(regions))
        except (OSError, ValueError, KeyError) as exc:
            st.error(f"No se pudo leer el GeoJSON: {exc}")
