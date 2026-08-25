"""
Driver script for the standard LiCSBAS processing sequence.

LiCSBAS ships as a set of numbered CLI scripts rather than an importable
Python package, so this wrapper just calls them in order with paths from
config.py. This keeps the sequence documented and repeatable instead of
you having to remember flags from memory every time.

IMPORTANT: verify the exact script names and flags against the README of
the LiCSBAS version you actually clone from GitHub (yumorishita/LiCSBAS)
before running — the sequence below reflects the commonly documented
workflow, but options and script names can shift between releases.

IMPORTANT: before running this wrapper, apply the one-time Windows
compatibility patches to your local LiCSBAS installation (see
../patches/ and SETUP.md's "InSAR-specific Windows gotchas" section) —
this wrapper assumes those patches are already applied to the LiCSBAS
scripts it calls, since they patch the third-party tool itself rather
than anything in this project's own code.

Typical sequence:
  01: download geotiffs from LiCSAR portal (skip if you downloaded manually)
  02: multilook + convert to LiCSBAS binary format
  03/04 (optional): GACOS atmospheric correction, unwrapping error masking
  05 (optional): clip to a sub-AOI (recommended — don't process the whole frame)
  11: check unwrapping quality
  12: loop closure check (removes bad interferograms)
  13: small baseline inversion -> displacement time series
  14: velocity + STD estimation
  15: time series masking / filtering -> final velocity map + cumulative displacement

Run each step, inspect the output/plots LiCSBAS produces, and only move to
the next step once the previous one looks reasonable — don't chain all
steps blindly in one run the first time through.
"""

import os
import subprocess
import sys
from pathlib import Path

from config import DATA_PROCESSED, DATA_RAW, AOI_BBOX

# Point this at wherever you cloned LiCSBAS locally (see SETUP.md)
LICSBAS_BIN = Path(r"D:\Project_resume\tools\LiCSBAS\bin")
LICSBAS_LIB = LICSBAS_BIN.parent / "LiCSBAS_lib"


def run_step(script_name: str, args: list[str]) -> None:
    script_path = LICSBAS_BIN / script_name
    cmd = [sys.executable, str(script_path)] + args
    print(f"\n--- Running {script_name} ---")
    print(" ".join(cmd))
    env = os.environ.copy()
    env["PYTHONPATH"] = str(LICSBAS_LIB) + os.pathsep + env.get("PYTHONPATH", "")
    result = subprocess.run(cmd, capture_output=False, env=env)
    if result.returncode != 0:
        print(f"WARNING: {script_name} exited with code {result.returncode}")
        print("Stop and inspect before continuing to the next step.")
        sys.exit(result.returncode)


def main():
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)

    # Step 02: multilook + format conversion
    # Note: data landed in data/raw/GEOC/ (confirmed from actual download
    # output), not directly in data/raw/ — LiCSBAS01 always creates this
    # GEOC subfolder itself.
    run_step(
        "LiCSBAS02_ml_prep.py",
        [
            "-i", str(DATA_RAW / "GEOC"),
            "-o", str(DATA_PROCESSED / "GEOCml"),
            "-n", "3",  # multilook factor; increase for noisier/coarser output
        ],
    )

    # Step 05: clip to sub-AOI (strongly recommended — narrows processing
    # to the collieries you actually care about instead of the full frame)
    # Note: this fork names the script LiCSBAS05op_clip_unw.py, not
    # LiCSBAS05op_clip.py as the original LiCSBAS naming would suggest.
    bbox_str = "{min_lon}/{max_lon}/{min_lat}/{max_lat}".format(**AOI_BBOX)
    run_step(
        "LiCSBAS05op_clip_unw.py",
        [
            "-i", str(DATA_PROCESSED / "GEOCml"),
            "-o", str(DATA_PROCESSED / "GEOCml_clip"),
            "-g", bbox_str,
        ],
    )

    # Step 11: unwrapping quality check
    run_step(
        "LiCSBAS11_check_unw.py",
        ["-d", str(DATA_PROCESSED / "GEOCml_clip")],
    )

    # Step 12: loop closure (removes bad interferograms from the network)
    run_step(
        "LiCSBAS12_loop_closure.py",
        ["-d", str(DATA_PROCESSED / "GEOCml_clip")],
    )

    # Step 13: small baseline inversion -> raw displacement time series
    run_step(
        "LiCSBAS13_sb_inv.py",
        ["-d", str(DATA_PROCESSED / "GEOCml_clip"), "-t", str(DATA_PROCESSED / "TS_GEOCml_clip")],
    )

    # Step 14: velocity + STD estimation
    run_step(
        "LiCSBAS14_vel_std.py",
        ["-t", str(DATA_PROCESSED / "TS_GEOCml_clip")],
    )

    # Step 15: final masking/filtering -> vel.geo.tif and cum.h5
    run_step(
        "LiCSBAS15_mask_ts.py",
        ["-t", str(DATA_PROCESSED / "TS_GEOCml_clip")],
    )

    print("\nDone. Check TS_GEOCml_clip/results/vel.geo.tif and cum.h5")
    print("against config.VELOCITY_TIF / config.TS_FILE paths — adjust")
    print("config.py if LiCSBAS placed them somewhere slightly different.")


if __name__ == "__main__":
    main()
