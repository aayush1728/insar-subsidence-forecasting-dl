"""
Overlay classified subsidence risk zones with mine lease boundaries (and
optionally settlement/infrastructure layers), producing summary stats:
what fraction of the lease area falls in each risk class, and vice versa.

This is the step that reuses your Web GIS project's PostGIS/GeoPandas
skills and turns the InSAR output into something directly relevant to a
mine boundary / lease-management use case.
"""

import geopandas as gpd

from config import RISK_ZONES_GEOJSON, MINE_BOUNDARY_GEOJSON, DATA_PROCESSED


def load_layers() -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    risk = gpd.read_file(RISK_ZONES_GEOJSON)

    if not MINE_BOUNDARY_GEOJSON.exists():
        raise FileNotFoundError(
            f"{MINE_BOUNDARY_GEOJSON} not found. Add a mine lease boundary "
            "GeoJSON (WGS84) to data/boundaries/ first — you can adapt the "
            "boundary layers from your Web GIS project if the Raniganj "
            "lease boundaries aren't readily available, or digitize a "
            "rough AOI polygon in QGIS as a stand-in."
        )
    boundary = gpd.read_file(MINE_BOUNDARY_GEOJSON)

    if risk.crs != boundary.crs:
        boundary = boundary.to_crs(risk.crs)

    return risk, boundary


def overlap_stats(risk: gpd.GeoDataFrame, boundary: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Intersect risk zones with the mine boundary and summarize by class."""
    intersected = gpd.overlay(risk, boundary, how="intersection")

    utm_crs = intersected.estimate_utm_crs()
    intersected_utm = intersected.to_crs(utm_crs)
    intersected["overlap_area_m2"] = intersected_utm.area

    summary = (
        intersected.groupby("risk_label")["overlap_area_m2"]
        .sum()
        .sort_values(ascending=False)
    )

    return intersected, summary


def main():
    risk, boundary = load_layers()
    intersected, summary = overlap_stats(risk, boundary)

    out_path = DATA_PROCESSED / "risk_zones_within_boundary.geojson"
    intersected.to_file(out_path, driver="GeoJSON")

    print(f"Wrote intersected risk zones to {out_path}")
    print("\nArea within mine boundary by risk class (m2):")
    print(summary)

    total = summary.sum()
    if total > 0:
        print("\nAs % of overlapping area:")
        print((summary / total * 100).round(1))


if __name__ == "__main__":
    main()
