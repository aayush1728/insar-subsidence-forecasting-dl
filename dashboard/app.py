"""
Streamlit dashboard: subsidence risk map + time series viewer.

Reuses the same Streamlit pattern you're building for the UHI project, so
this should feel familiar. Run with:

    streamlit run dashboard/app.py
"""

import sys
from pathlib import Path

import streamlit as st
import geopandas as gpd
import folium
from streamlit_folium import st_folium

sys.path.append(str(Path(__file__).resolve().parent.parent / "src"))
from config import RISK_ZONES_GEOJSON, MINE_BOUNDARY_GEOJSON, AOI_CENTER_LAT, AOI_CENTER_LON

st.set_page_config(page_title="Raniganj Subsidence Monitor", layout="wide")

st.title("Raniganj Coalfield — InSAR Subsidence Monitoring")
st.caption(
    "Sentinel-1 InSAR (LiCSBAS) derived ground deformation, classified into "
    "risk zones and overlaid with mine lease boundaries."
)

RISK_COLORS = {"stable": "#2ecc71", "moderate": "#f39c12", "high": "#e74c3c"}


@st.cache_data
def load_risk_zones():
    if not RISK_ZONES_GEOJSON.exists():
        return None
    return gpd.read_file(RISK_ZONES_GEOJSON)


@st.cache_data
def load_boundary():
    if not MINE_BOUNDARY_GEOJSON.exists():
        return None
    return gpd.read_file(MINE_BOUNDARY_GEOJSON)


risk_gdf = load_risk_zones()
boundary_gdf = load_boundary()

col1, col2 = st.columns([3, 1])

with col1:
    m = folium.Map(location=[AOI_CENTER_LAT, AOI_CENTER_LON], zoom_start=13, tiles="CartoDB positron")

    if boundary_gdf is not None:
        folium.GeoJson(
            boundary_gdf,
            name="Mine lease boundary",
            style_function=lambda x: {"color": "#3388ff", "weight": 2, "fillOpacity": 0},
        ).add_to(m)

    if risk_gdf is not None:
        for _, row in risk_gdf.iterrows():
            folium.GeoJson(
                row["geometry"],
                style_function=lambda x, c=RISK_COLORS.get(row["risk_label"], "#999999"): {
                    "fillColor": c,
                    "color": c,
                    "weight": 1,
                    "fillOpacity": 0.6,
                },
                tooltip=f"Risk: {row['risk_label']}",
            ).add_to(m)
    else:
        st.warning(
            "No risk zones found yet — run extract_risk_zones.py after the "
            "LiCSBAS pipeline completes, then reload this dashboard."
        )

    folium.LayerControl().add_to(m)
    st_folium(m, width=900, height=600)

with col2:
    st.subheader("Risk zone summary")
    if risk_gdf is not None:
        summary = risk_gdf.groupby("risk_label")["area_m2"].sum().sort_values(ascending=False)
        st.dataframe(summary.rename("Area (m²)"))

        for label, color in RISK_COLORS.items():
            st.markdown(
                f"<span style='color:{color}; font-size:20px;'>&#9632;</span> {label.title()}",
                unsafe_allow_html=True,
            )
    else:
        st.info("Run the pipeline to populate this view.")

st.markdown("---")
st.caption(
    "Deformation zones validated against published Raniganj/Jharia InSAR+DGPS "
    "studies — see README.md references."
)
