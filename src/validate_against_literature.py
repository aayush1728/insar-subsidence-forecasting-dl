"""
Sanity-check your extracted velocity/risk results against published rates
and known station locations (e.g. the DGPS stations from the Raniganj
InSAR+DGPS paper). Fill in config.LITERATURE_REFERENCE_POINTS with real
coordinates and reported rates as you extract them from the paper(s).

This won't be a rigorous statistical validation (you don't have the raw
DGPS data), but a qualitative match — "our high-risk zone lines up with
the reported collapse location near X" — is enough to demonstrate rigor
without needing field data of your own.
"""

import numpy as np
import rasterio

from config import VELOCITY_TIF, LITERATURE_REFERENCE_POINTS


def sample_velocity_at_point(src: rasterio.DatasetReader, lon: float, lat: float) -> float:
    row, col = src.index(lon, lat)
    window_data = src.read(1, window=((row - 1, row + 2), (col - 1, col + 2)))
    valid = window_data[~np.isnan(window_data)]
    if valid.size == 0:
        return float("nan")
    return float(np.nanmean(valid))


def main():
    if not LITERATURE_REFERENCE_POINTS:
        print(
            "config.LITERATURE_REFERENCE_POINTS is empty — add coordinates "
            "and reported rates from the papers in README references before "
            "running this. Even 2-3 points is enough for a qualitative "
            "validation section in your write-up."
        )
        return

    if not VELOCITY_TIF.exists():
        raise FileNotFoundError(f"{VELOCITY_TIF} not found — run the LiCSBAS pipeline first.")

    with rasterio.open(VELOCITY_TIF) as src:
        print(f"{'Site':30s} {'Reported (mm/yr)':>18s} {'Measured (mm/yr)':>18s} {'Diff':>8s}")
        for point in LITERATURE_REFERENCE_POINTS:
            measured = sample_velocity_at_point(src, point["lon"], point["lat"])
            reported = point["reported_rate_mm_yr"]
            diff = measured - reported if not np.isnan(measured) else float("nan")
            print(f"{point['name']:30s} {reported:18.1f} {measured:18.1f} {diff:8.1f}")


if __name__ == "__main__":
    main()
