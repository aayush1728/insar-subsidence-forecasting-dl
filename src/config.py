"""
Shared configuration for the InSAR subsidence monitoring pipeline.

Fill in / adjust these once you've picked your exact AOI and confirmed
data availability. Keeping everything here means the other scripts don't
need paths or thresholds hardcoded inline.
"""

from pathlib import Path

# --- Paths -------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
DATA_BOUNDARIES = PROJECT_ROOT / "data" / "boundaries"

# LiCSBAS time-series output directory (confirmed actual location)
TS_DIR = DATA_PROCESSED / "TS_GEOCml_clip"

# Final masked velocity map, converted to GeoTIFF by flt_to_geotiff.py.
# LiCSBAS itself writes this as a raw binary float32 file at
# TS_DIR/results/vel.mskd (confirmed on disk) — NOT a GeoTIFF despite
# living alongside .png previews. Run flt_to_geotiff.py before using this.
VELOCITY_TIF = TS_DIR / "results" / "vel_mskd.tif"

# Cumulative displacement time series (confirmed actual location)
TS_FILE = TS_DIR / "cum.h5"

# Mine lease / AOI boundary (GeoJSON, WGS84)
MINE_BOUNDARY_GEOJSON = DATA_BOUNDARIES / "mine_lease_boundary.geojson"

# Output of risk zone extraction
RISK_ZONES_GEOJSON = DATA_PROCESSED / "risk_zones.geojson"

# --- Confirmed COMET-LiCS frame coverage -------------------------------
# Checked manually on the COMET-LiCS portal at the AOI coordinates below.
# Ascending frame confirmed directly over the AOI (lon 87.116, lat 23.629
# vs. target 87.115/23.629 — essentially exact match), fully processed
# (100% epochs), well-populated (1386 products). No descending coverage
# at this location, so this project uses single-direction LOS only.

FRAME_ID = "012A_06687_181919"
FRAME_DIRECTION = "ascending"

# --- Study area ----------------------------------------------------------
# Raniganj Coalfield, Paschim Bardhaman district, West Bengal
# Adjust the bounding box once you've picked your exact sub-AOI —
# don't process the entire 443 sq km coalfield for a first pass.

AOI_CENTER_LAT = 23.629
AOI_CENTER_LON = 87.115

# Rough starting bbox (~10km box around center) — narrow this down once
# you've identified specific known-subsidence collieries to focus on.
AOI_BBOX = {
    "min_lon": AOI_CENTER_LON - 0.05,
    "max_lon": AOI_CENTER_LON + 0.05,
    "min_lat": AOI_CENTER_LAT - 0.05,
    "max_lat": AOI_CENTER_LAT + 0.05,
}

# --- Risk classification thresholds (mm/year, LOS velocity) --------------
# Recalibrated against the actual observed distribution for this AOI
# (min -18.07, max 8.75, percentiles [5,25,50,75,95] =
# [-9.0, -3.13, -0.45, 2.22, 4.31] mm/yr — confirmed by direct inspection
# of vel_mskd.tif). The original literature-based thresholds (Jharia/Korba,
# -21 to -120 mm/yr) never triggered "high" at all in this AOI — this
# specific 10km box, centered generically on the coalfield rather than a
# known-active colliery, shows meaningfully gentler subsidence than
# Jharia's headline rates. Worth noting as a finding in the write-up
# rather than treating as a bug.
#
# These thresholds are now relative to this AOI's own distribution:
# stable ≈ within the 25th-75th percentile band, moderate ≈ 5th-25th,
# high ≈ below the 5th percentile (the most extreme ~5% of pixels).

RISK_THRESHOLDS_MM_YR = {
    "stable": (-3, 3),         # roughly the 25th-75th percentile band
    "moderate": (-9, -3),      # roughly 5th-25th percentile
    "high": (-1000, -9),       # below 5th percentile — most extreme subsidence
}

# Original literature-derived thresholds, kept for reference/comparison —
# these matched Jharia/Korba's more extreme documented rates but didn't
# fit this AOI's actual data:
# RISK_THRESHOLDS_MM_YR = {
#     "stable": (-10, 10),
#     "moderate": (-30, -10),
#     "high": (-1000, -30),
# }

# --- Known literature reference points (fill in as you find exact coords) -
# Use this in validate_against_literature.py to sanity-check your results
# against the DGPS stations / known collapse locations from the Raniganj
# InSAR+DGPS paper. Placeholder values below — replace with the real
# coordinates once you've read the paper's site descriptions.

LITERATURE_REFERENCE_POINTS = [
    # {"name": "DGPS station 1 (replace)", "lat": 23.63, "lon": 87.10, "reported_rate_mm_yr": -25},
]

# --- LSTM/GRU forecasting settings ----------------------------------------
# Trained across all valid pixels' time series (not just one AOI-average
# series) — with only ~33 epochs total, a single series is too little
# data for a meaningful deep learning model. Treating each pixel as a
# separate training sequence (standard in spatio-temporal deep learning)
# gives ~485 sequences instead of 1, which is a defensible amount of
# training signal for a small GRU.

FORECAST_WINDOW_SIZE = 6   # epochs of history used to predict the next one
FORECAST_TEST_EPOCHS = 6   # most recent epochs held out for evaluation (temporal split, not random)
FORECAST_GRU_UNITS = 16    # small on purpose — short sequences, limited data
FORECAST_EPOCHS = 50
FORECAST_DIR = PROJECT_ROOT / "models"
FORECAST_MODEL_PATH = FORECAST_DIR / "subsidence_gru.keras"
FORECAST_PLOT_PATH = FORECAST_DIR / "forecast_comparison.png"
