"""
Turn the LiCSBAS mean velocity map (mm/year, negative = subsidence) into
classified risk-zone polygons.

This is the step that makes the project read as "monitoring" rather than
just "processing" — raw InSAR output is a continuous raster that only a
specialist can interpret; this turns it into discrete risk categories
anyone reviewing your resume/GitHub can understand at a glance.
"""

import numpy as np
import rasterio
from rasterio.features import shapes
import geopandas as gpd
from shapely.geometry import shape

from config import VELOCITY_TIF, RISK_ZONES_GEOJSON, RISK_THRESHOLDS_MM_YR


def classify_velocity(velocity: np.ndarray) -> np.ndarray:
    """Map each pixel's velocity (mm/yr) to an integer risk class.

    0 = nodata, 1 = stable, 2 = moderate, 3 = high
    """
    risk = np.zeros(velocity.shape, dtype=np.uint8)

    stable_lo, stable_hi = RISK_THRESHOLDS_MM_YR["stable"]
    mod_lo, mod_hi = RISK_THRESHOLDS_MM_YR["moderate"]
    high_lo, high_hi = RISK_THRESHOLDS_MM_YR["high"]

    valid = ~np.isnan(velocity)
    risk[valid & (velocity >= stable_lo) & (velocity <= stable_hi)] = 1
    risk[valid & (velocity >= mod_lo) & (velocity < mod_hi)] = 2
    risk[valid & (velocity >= high_lo) & (velocity < high_hi)] = 3

    return risk


def polygonize_risk(risk: np.ndarray, transform, crs) -> gpd.GeoDataFrame:
    """Convert the classified risk raster into vector polygons."""
    records = []
    for geom, value in shapes(risk, mask=(risk > 0), transform=transform):
        records.append({"geometry": shape(geom), "risk_class": int(value)})

    gdf = gpd.GeoDataFrame(records, crs=crs)

    class_labels = {1: "stable", 2: "moderate", 3: "high"}
    gdf["risk_label"] = gdf["risk_class"].map(class_labels)

    return gdf


def main():
    if not VELOCITY_TIF.exists():
        raise FileNotFoundError(
            f"{VELOCITY_TIF} not found. Run run_licsbas_pipeline.py first, "
            "or check that config.VELOCITY_TIF points at the right output "
            "path from your LiCSBAS run."
        )

    with rasterio.open(VELOCITY_TIF) as src:
        velocity = src.read(1, masked=True).filled(np.nan)
        transform = src.transform
        crs = src.crs

    risk = classify_velocity(velocity)
    gdf = polygonize_risk(risk, transform, crs)

    # Dissolve adjacent same-class pixels into cleaner polygons and drop
    # tiny speckle polygons (likely noise, not real subsidence).
    gdf = gdf.dissolve(by="risk_class").reset_index()
    gdf["area_m2"] = gdf.to_crs(gdf.estimate_utm_crs()).area
    gdf = gdf[gdf["area_m2"] > 500]  # drop sub-500m2 speckle; tune as needed

    gdf.to_file(RISK_ZONES_GEOJSON, driver="GeoJSON")
    print(f"Wrote {len(gdf)} risk zone polygons to {RISK_ZONES_GEOJSON}")
    print(gdf[["risk_label", "area_m2"]].groupby("risk_label").sum())


if __name__ == "__main__":
    main()
