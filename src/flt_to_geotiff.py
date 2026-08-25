"""
Convert a LiCSBAS raw binary float32 output (e.g. vel.mskd, vstd, coh_avg)
into a proper georeferenced GeoTIFF, using the corner coordinates and
pixel spacing from EQA.dem_par.

LiCSBAS's own outputs (vel, vel.mskd, coh_avg, hgt, etc.) are flat
binary float32 arrays with no embedded georeferencing — not GeoTIFFs,
despite some of them showing up in a folder alongside .png previews.
This script adds that missing georeferencing so the rest of the project
(extract_risk_zones.py, the dashboard) can read them with rasterio like
any other raster.

EQA.dem_par format (confirmed against the actual file in this project):
    width: <int>
    nlines: <int>
    corner_lat: <float>  decimal degrees   (top-left corner)
    corner_lon: <float>  decimal degrees   (top-left corner)
    post_lat: <float> decimal degrees      (negative — south per row)
    post_lon: <float> decimal degrees      (positive — east per column)
"""

import numpy as np
import rasterio
from rasterio.transform import Affine


def parse_dem_par(dem_par_path):
    """Parse the handful of fields we need from an EQA.dem_par file."""
    values = {}
    with open(dem_par_path, "r") as f:
        for line in f:
            if ":" not in line:
                continue
            key, rest = line.split(":", 1)
            key = key.strip()
            if key in ("width", "nlines"):
                values[key] = int(rest.split()[0])
            elif key in ("corner_lat", "corner_lon", "post_lat", "post_lon"):
                values[key] = float(rest.split()[0])
    required = {"width", "nlines", "corner_lat", "corner_lon", "post_lat", "post_lon"}
    missing = required - values.keys()
    if missing:
        raise ValueError(f"EQA.dem_par missing expected fields: {missing}")
    return values


def flt_to_geotiff(flt_path, dem_par_path, out_tif_path, nodata=np.nan):
    """Read a LiCSBAS raw binary float32 file and write it out as a GeoTIFF."""
    meta = parse_dem_par(dem_par_path)
    width, nlines = meta["width"], meta["nlines"]

    data = np.fromfile(flt_path, dtype=np.float32).reshape(nlines, width)

    transform = Affine(
        meta["post_lon"], 0.0, meta["corner_lon"],
        0.0, meta["post_lat"], meta["corner_lat"],
    )

    with rasterio.open(
        out_tif_path, "w",
        driver="GTiff",
        height=nlines, width=width,
        count=1, dtype=np.float32,
        crs="EPSG:4326",
        transform=transform,
        nodata=nodata,
    ) as dst:
        dst.write(data, 1)

    print(f"Wrote {out_tif_path} ({width}x{nlines}, EPSG:4326)")
    return out_tif_path


if __name__ == "__main__":
    import sys
    sys.path.append(str(__import__("pathlib").Path(__file__).resolve().parent))
    from config import DATA_PROCESSED

    ts_dir = DATA_PROCESSED / "TS_GEOCml_clip"
    dem_par = ts_dir / "info" / "EQA.dem_par"

    # Convert the final masked velocity map — this is what
    # extract_risk_zones.py consumes.
    flt_to_geotiff(
        ts_dir / "results" / "vel.mskd",
        dem_par,
        ts_dir / "results" / "vel_mskd.tif",
    )
