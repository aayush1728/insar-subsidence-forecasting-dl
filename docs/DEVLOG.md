# Build Log

Detailed pipeline status and debugging history, moved out of the main README to keep that page recruiter-friendly. Kept here because the actual problem-solving (Windows/LiCSBAS fork compatibility issues, threshold recalibration, etc.) is real engineering work worth having a record of.

# InSAR Mine Subsidence Monitoring — Raniganj Coalfield

Ground deformation monitoring pipeline using Sentinel-1 InSAR time series to
detect and classify mining-induced subsidence, overlaid against mine
boundaries for a monitoring-style (not just visualization) GIS tool.

This project bridges a B.Tech in Mining Engineering with an M.Tech in
Geoinformatics — the AOI, risk thresholds, and validation approach are all
chosen with that connection in mind.

## Study area

**Raniganj Coalfield**, Paschim Bardhaman district, West Bengal, India
(~23.629°N, 87.115°E). Chosen over Jharia because there's a recent (2024)
peer-reviewed study combining InSAR with 4 DGPS stations at known collapse
locations — a real benchmark to validate against (see References).

## Pipeline

1. **Data acquisition** — Sentinel-1 InSAR products for the AOI, either
   pre-processed via the COMET-LiCS portal (fast path) or raw SLCs processed
   in SNAP (fallback path).
2. **Time series generation** — LiCSBAS turns interferogram stacks into a
   cumulative line-of-sight (LOS) displacement time series and mean
   velocity map.
3. **Risk zone extraction** — threshold the velocity map into
   stable / moderate / high-risk subsidence zones.
4. **GIS overlay** — intersect risk zones with mine lease boundaries and
   settlement/infrastructure layers.
5. **Validation** — compare risk zones and rates against published
   subsidence rates and DGPS station locations.
6. **Dashboard** — Streamlit app showing the risk map and time series.
7. **Forecasting (ML/DL extension)** — train an LSTM/GRU on the per-pixel
   or per-zone displacement time series from step 2 to forecast future
   subsidence rates, benchmarked against a classical baseline (linear
   trend or ARIMA). This is what makes the project legible to AI/ML/deep
   learning keyword filters, not just GIS/remote sensing ones — added
   deliberately for that reason. Needs `cum.h5` from step 2 (LiCSBAS
   steps 13-15) as training data, so it comes after the core pipeline is
   working, not before.

## Status

- [ ] AOI boundary finalized (`data/boundaries/`)
- [x] COMET-LiCS frame coverage checked for AOI (frame `012A_06687_181919`,
      ascending, 1386 products, no descending coverage; archive spans
      2017–Feb 2024, not to present)
- [x] Sentinel-1 data acquired (127 IFG pairs, Jan 2023–Feb 2024, ~6GB)
- [x] Multilook/format prep complete (`LiCSBAS02_ml_prep.py`, output in
      `data/processed/GEOCml`)
- [x] Clipped to sub-AOI (`LiCSBAS05op_clip_unw.py`, 34×34px, output in
      `data/processed/GEOCml_clip`)
- [x] Unwrapping quality check (`LiCSBAS11_check_unw.py`, 0/127 ifgs
      discarded — clean dataset)
- [x] Loop closure check (`LiCSBAS12_loop_closure.py`, 31/127 ifgs
      discarded; **network gap Oct 31–Dec 6 2023** splits data into a
      strong 25-image segment (Jan–Oct 2023) and a weak 8-image segment
      (Dec 2023–Feb 2024) — effective time series likely ends up Jan–Oct
      2023 once step 13 selects the largest connected component)
- [x] **NSBAS time series inversion complete** (`LiCSBAS13_sb_inv.py`,
      96 ifgs / 33 images / 947 points, reference point at 14:15/11:12,
      output: `cum.h5` + velocity map in `data/processed/TS_GEOCml_clip`)
      — this is the actual displacement time series the whole project is
      built around
- [x] Velocity uncertainty estimated (`LiCSBAS14_vel_std.py`, bootstrap
      + STC, 100 iterations)
- [x] **Final masking complete** (`LiCSBAS15_mask_ts.py`, 485/946 pixels
      kept at 51.3% — full LiCSBAS pipeline done, `vel.mskd` is the final
      velocity product)
- [x] Converted `vel.mskd` to georeferenced GeoTIFF (`flt_to_geotiff.py`,
      output: `vel_mskd.tif`, EPSG:4326)
- [x] **Risk zones extracted** (`extract_risk_zones.py`, thresholds
      recalibrated to actual data distribution — high: 2.5 km², moderate:
      10.4 km², stable: 28.6 km²)
- [x] LiCSBAS environment installed and verified (installed into `geoinfo`)
- [ ] Time series / velocity map generated
- [ ] Risk zones extracted
- [ ] Overlay with mine boundaries complete
- [ ] Validated against literature
- [ ] Dashboard built
- [ ] Forecasting model trained (LSTM/GRU vs. classical baseline)
- [ ] README + write-up finalized for GitHub/resume

## Folder structure

```
insar-mine-subsidence/
├── README.md
├── SETUP.md              # environment + tool installation guide
├── environment.yml        # conda environment spec
├── .gitignore
├── data/
│   ├── raw/                # downloaded SAR products (gitignored)
│   ├── processed/          # LiCSBAS outputs, risk rasters (gitignored)
│   └── boundaries/         # AOI + mine lease boundary files (small, tracked)
├── src/
│   ├── check_licsar_coverage.py
│   ├── download_licsar_data.py
│   ├── run_licsbas_pipeline.py
│   ├── extract_risk_zones.py
│   ├── overlay_boundaries.py
│   ├── validate_against_literature.py
│   └── forecast_subsidence.py    # LSTM/GRU forecasting (added after core pipeline)
├── dashboard/
│   └── app.py               # Streamlit risk map + time series
├── notebooks/
│   └── exploration.ipynb
└── docs/
    ├── resume_bullet_draft.md
    └── references.md
```

## References

- González et al., *LiCSBAS: An Open-Source InSAR Time Series Analysis
  Package Integrated with the LiCSAR Automated Sentinel-1 InSAR Processor*,
  Remote Sensing, 2020.
- Surface deformation monitoring of Raniganj coalfield, India, using
  advanced InSAR and DGPS, *International Journal of Digital Earth*, 2024.
- Kumar et al., *Land subsidence mapping and monitoring using modified
  persistent scatterer interferometric synthetic aperture radar in Jharia
  Coalfield, India*, Journal of Earth System Science, 2020.
- Raju & Mehdi, subsidence rates in Jharia Coalfield from Sentinel-1, 2023.

See `docs/references.md` for full details and links as you collect them.
