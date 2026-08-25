# Setup Guide (Windows + Anaconda)

This mirrors the environment you're already using for the Web GIS project,
with a few InSAR-specific additions.

## 1. Set up the conda environment

Installing directly into your existing `geoinfo` env — it already has
numpy, scipy, pandas, matplotlib, scikit-learn, and rtree, so no need to
duplicate all of that.

```powershell
conda activate geoinfo
conda install -c conda-forge gdal rasterio geopandas shapely fiona pyproj statsmodels gmt psycopg2 streamlit folium streamlit-folium sqlalchemy geoalchemy2
```

Run the install as one command, not one package at a time — `geoinfo` has
a few pip-installed packages (scipy, scikit-learn) mixed with conda
builds, and solving everything together minimizes the chance conda tries
to fight with those versions. Check the solve output before confirming —
if it proposes downgrading numpy/scipy/scikit-learn significantly, stop
and double check before proceeding.

If `psycopg2` fails via pip, install it separately via conda (same issue
you hit on the Web GIS project):

```powershell
conda install -c conda-forge psycopg2
```

All commands and scripts below assume the `geoinfo` env is active.

## 2. Install SNAP (ESA Sentinel Application Platform)

Only needed for the **fallback path** (raw SLC processing). Skip this if
`check_licsar_coverage.py` confirms a pre-processed COMET-LiCS frame covers
the AOI.

1. Download the SNAP installer (all toolboxes, includes Sentinel-1 toolbox)
   from the ESA STEP site: https://step.esa.int/main/download/snap-download/
2. Run the installer. On Windows, install to a path with no spaces
   (e.g. `C:\snap`) to avoid known SNAP path-handling bugs.
3. During install, let it configure Python (snappy) — or skip this if you
   only plan to use the SNAP Desktop GUI for coregistration/interferogram
   generation rather than scripting it.
4. Verify: launch SNAP Desktop, open a Sentinel-1 SLC product (once
   downloaded) to confirm the Sentinel-1 toolbox is active.

## 3. Install LiCSBAS

LiCSBAS is distributed as a GitHub repo, not a conda/pip package.

**Important:** COMET migrated their data storage in October 2025. Use
COMET's own maintained fork, not the original yumorishita/LiCSBAS repo —
the original can hit file-not-found errors against the new storage system.

```powershell
mkdir D:\tools
cd D:\tools
git clone https://github.com/comet-licsar/LiCSBAS.git
```

(Any drive/location works — this just needs to match `LICSBAS_BIN` in
`src/download_licsar_data.py` and `src/run_licsbas_pipeline.py`, which are
already set to `D:\tools\LiCSBAS\bin`.)

Add the `LiCSBAS/bin` and `LiCSBAS/batch_scripts` folders to your PATH, or
call scripts with full paths from within the `geoinfo` conda env.

LiCSBAS scripts are mostly Python + a handful of GMT-based plotting
utilities. GMT was installed into `geoinfo` in step 1 above, so you
shouldn't need a separate GMT install on Windows.

Verify:

```powershell
python C:\tools\LiCSBAS\bin\LiCSBAS02_ml_prep.py -h
```

If that prints a help message without import errors, you're set.

## 4. Check COMET-LiCS coverage for the AOI

Run `src/check_licsar_coverage.py` (prints the portal URL and frame-search
guidance — the sandbox that built this scaffold can't reach the portal
directly, so this is a manual check you'll do locally) — or just visit:

https://comet.nerc.ac.uk/comet-lics-portal/

and search around 23.629°N, 87.115°E on the interactive map.

- **Frame found with products** → skip SNAP, go straight to LiCSBAS
  (`src/run_licsbas_pipeline.py`) using the downloaded frame data.
- **No frame / no products** → use SNAP to generate interferograms from
  raw Sentinel-1 SLC pairs (downloaded from ASF Vertex:
  https://search.asf.alaska.edu/), then feed those into LiCSBAS.

## 5. PostGIS (reusing your Web GIS setup)

If you want to overlay risk zones against mine boundaries in PostGIS rather
than plain GeoPandas, reuse the Docker Compose setup from the Web GIS
project — no new install needed, just a new database/schema for this
project's boundary and risk-zone tables.

## Known gotchas (carried over from Web GIS project)

- Use `conda install -c conda-forge psycopg2`, not pip, on Windows.
- Docker Desktop must be running before `docker compose up` if you use
  PostGIS for the overlay step.
- PowerShell can silently collapse spaces in copy-pasted multi-line
  commands — type install commands manually or use `Copy-Item` rather than
  pasting long chained commands.
- Install SNAP to a path with no spaces (see above) — this is an
  InSAR-specific gotcha, not one you've hit before.
