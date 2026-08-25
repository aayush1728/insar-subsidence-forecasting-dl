# InSAR-Based Ground Subsidence Monitoring & Forecasting — Raniganj Coalfield

> Remote Sensing / Geospatial ML project — 2026
> An end-to-end Sentinel-1 InSAR pipeline for detecting, classifying, and
> forecasting mining-induced ground subsidence, combining classical SAR
> interferometry with a GRU-based deep learning forecasting model.

---

## Problem Statement

Underground coal mining causes gradual ground subsidence that can threaten
infrastructure and settlements above active and abandoned workings.
Traditional monitoring (leveling surveys, GPS) is sparse, slow, and
expensive to run at scale. This project builds a complete pipeline — from
raw Sentinel-1 SAR data through a validated subsidence risk map to a
short-horizon deformation forecast — for the **Raniganj Coalfield**, West
Bengal, one of India's oldest and most heavily mined coal regions.

It bridges a B.Tech in Mining Engineering with an M.Tech in Geoinformatics:
the study area, risk thresholds, and validation approach are all chosen
with practical mining-subsidence knowledge in mind, not just as a generic
remote-sensing exercise.

---

## Key Results

- Processed **127 Sentinel-1 interferometric pairs** (Jan 2023 – Feb 2024)
  through the COMET-LiCS / LiCSBAS pipeline
- NSBAS time series inversion across **96 quality-filtered interferograms**
  and **33 SAR epochs**, yielding a per-pixel displacement time series
  (`cum.h5`) and velocity map for the AOI
- Classified subsidence into three risk tiers, calibrated to the AOI's
  *actual* observed velocity distribution rather than borrowed literature
  thresholds:

  | Risk level | Area      |
  |------------|-----------|
  | High       | 2.5 km²   |
  | Moderate   | 10.4 km²  |
  | Stable     | 28.6 km²  |

- Trained a **GRU model** across ~485 pixel-level displacement time series
  (treating each pixel as an independent training sequence, since the
  33-epoch record alone is too short for a single-series deep learning
  model) to forecast next-epoch subsidence, benchmarked against a
  classical linear-trend baseline using a temporal (not random) train/test
  split:

  <!-- Results from src/forecast_subsidence.py, temporal train/test split
       (938 valid pixel series, 19698 train / 5628 test windows) -->
  | Model        | MAE (mm) | RMSE (mm) |
  |--------------|----------|-----------|
  | Linear trend | 4.309    | 6.302     |
  | GRU          | 4.214    | 6.215     |

  The GRU improves on the linear-trend baseline by ~2.2% (MAE) — a modest
  but genuine gain. Worth stating honestly: with only 33 SAR epochs, a
  linear trend is a strong baseline for one-step-ahead forecasting, and
  the sample forecasts show real pixel-level noise the model has to
  contend with. A longer observation window would likely widen this gap.

---

## Tech Stack

| Layer            | Technology                                   |
|-------------------|-----------------------------------------------|
| SAR data source   | Sentinel-1 (ESA Copernicus, via COMET-LiCS)   |
| InSAR processing  | LiCSBAS (NSBAS time series inversion)          |
| Geospatial        | GDAL, rasterio, GeoPandas, Shapely, pyproj    |
| Deep learning     | TensorFlow / Keras (GRU forecasting)           |
| Dashboard         | Streamlit + Folium                             |
| Language          | Python 3.13                                    |

---

## Pipeline

1. **Data acquisition** — Sentinel-1 InSAR products for the AOI via the
   COMET-LiCS portal.
2. **Time series generation** — LiCSBAS turns the interferogram stack into
   a cumulative line-of-sight (LOS) displacement time series and mean
   velocity map (NSBAS inversion).
3. **Risk zone extraction** — threshold the velocity map into
   stable / moderate / high-risk subsidence zones, calibrated to the
   observed data distribution.
4. **GIS overlay** — intersect risk zones with mine lease boundaries and
   infrastructure layers.
5. **Validation** — compare risk zones and rates against published
   InSAR + DGPS subsidence studies for the region.
6. **Dashboard** — interactive Streamlit app showing the risk map and
   displacement time series.
7. **Forecasting** — a GRU trained across pixel-level time series
   forecasts near-term subsidence, benchmarked against a classical linear
   trend baseline.

---

## Project Structure

```
insar-mine-subsidence/
├── README.md
├── SETUP.md                     # full environment setup (incl. Windows-specific notes)
├── environment.yml
├── data/
│   └── boundaries/               # AOI + mine lease boundary files
├── src/
│   ├── check_licsar_coverage.py
│   ├── download_licsar_data.py
│   ├── run_licsbas_pipeline.py
│   ├── flt_to_geotiff.py         # LiCSBAS raw binary -> GeoTIFF
│   ├── extract_risk_zones.py
│   ├── overlay_boundaries.py
│   ├── validate_against_literature.py
│   └── forecast_subsidence.py    # GRU forecasting module
├── patches/                      # one-time Windows compatibility patches
│   └── ...                       # applied to the local LiCSBAS install — see SETUP.md
├── dashboard/
│   └── app.py                    # Streamlit risk map + time series viewer
├── models/
│   └── forecast_comparison.png   # GRU vs. baseline forecast comparison
└── docs/
    ├── references.md
    └── DEVLOG.md                 # detailed build log, incl. Windows/LiCSBAS fork gotchas
```

---

## Setup

Full environment setup (conda environment, LiCSBAS installation, and a set
of Windows-specific compatibility notes for this particular LiCSBAS fork)
is documented in [`SETUP.md`](SETUP.md). Quick summary once the
environment is ready:

```bash
python src/check_licsar_coverage.py     # confirm frame coverage for your AOI
python src/download_licsar_data.py      # pull Sentinel-1 interferogram products
python src/run_licsbas_pipeline.py      # LiCSBAS steps 02-15 (or run individually - see SETUP.md)
python src/flt_to_geotiff.py            # convert final velocity map to GeoTIFF
python src/extract_risk_zones.py        # classify subsidence risk zones
python src/forecast_subsidence.py       # train/evaluate the GRU forecasting model
streamlit run dashboard/app.py          # interactive risk map dashboard
```

---

## References

- González et al., *LiCSBAS: An Open-Source InSAR Time Series Analysis
  Package Integrated with the LiCSAR Automated Sentinel-1 InSAR Processor*,
  Remote Sensing, 2020.
- Surface deformation monitoring of Raniganj coalfield, India, using
  advanced InSAR and DGPS, *International Journal of Digital Earth*, 2024.
- Kumar et al., *Land subsidence mapping and monitoring using modified
  persistent scatterer interferometric synthetic aperture radar in Jharia
  Coalfield, India*, Journal of Earth System Science, 2020.

See [`docs/references.md`](docs/references.md) for full citations.
