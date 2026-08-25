"""
Step 01: download LiCSAR interferogram/coherence products for the confirmed
frame from the COMET-LiCS portal.

This calls LiCSBAS01_get_geotiff.py (part of the comet-licsar/LiCSBAS repo
— see SETUP.md for why it must be that fork specifically, not the original
yumorishita one, following COMET's October 2025 storage migration).

IMPORTANT — start with a limited date range, not the full archive:
frame 012A_06687_181919 has 1386 products across its full history, which
is a lot of data and processing for a first pass. Start with ~1-2 years
of recent data to get the pipeline working end-to-end quickly, then widen
the range later once everything downstream is validated.
"""

import os
import subprocess
import sys
from pathlib import Path

from config import DATA_RAW, FRAME_ID

LICSBAS_BIN = Path(r"D:\Project_resume\tools\LiCSBAS\bin")
LICSBAS_LIB = LICSBAS_BIN.parent / "LiCSBAS_lib"

# Adjust this window once the pipeline is validated — starting narrow
# keeps the first run fast and the download size manageable.
# The frame's actual archive runs 2017 through Feb 2024 (confirmed by
# browsing the raw interferogram directory listing directly — the portal's
# "100% epochs processed" / "last compiled" stats describe portal-wide
# update cycles, not this specific frame, which appears to have stopped
# receiving new interferograms after Feb 2024).
#
# Starting with a ~14-month slice near the end of the archive rather than
# the full 7 years — full archive could be tens of GB and hours to
# download at these speeds. Get the pipeline working end-to-end on this
# first, then widen the range later if there's time before the resume
# deadline.
START_DATE = "20230101"
END_DATE = "20240229"


def main():
    DATA_RAW.mkdir(parents=True, exist_ok=True)

    script_path = LICSBAS_BIN / "LiCSBAS01_get_geotiff.py"
    cmd = [
        sys.executable, str(script_path),
        "-f", FRAME_ID,
        "-s", START_DATE,
        "-e", END_DATE,
    ]

    print("Running:", " ".join(cmd))
    print(f"Downloading frame {FRAME_ID} products for {START_DATE}-{END_DATE}")
    print("into", DATA_RAW / "GEOC", "(this script has no -o flag — it")
    print("always writes a GEOC/ folder inside the current working")
    print("directory, so we run it with data/raw as the working dir)")
    print()
    print("This can take a while depending on connection speed and how")
    print("many products fall in the date range — let it run rather than")
    print("assuming it's stuck; check Task Manager for network activity")
    print("if unsure, same as with the earlier conda install.")

    env = os.environ.copy()
    env["PYTHONPATH"] = str(LICSBAS_LIB) + os.pathsep + env.get("PYTHONPATH", "")

    result = subprocess.run(cmd, cwd=str(DATA_RAW), env=env)
    if result.returncode != 0:
        print(f"WARNING: exited with code {result.returncode}")
        print("Common causes: frame ID typo, date range with no products,")
        print("or LiCSBAS still pointing at the old (pre-migration) repo —")
        print("double check you cloned comet-licsar/LiCSBAS, not the")
        print("original yumorishita/LiCSBAS.")
        sys.exit(result.returncode)

    print("\nDone. Verify data/raw/ has interferogram (.unw.tif) and")
    print("coherence (.cc.tif) files before moving to")
    print("run_licsbas_pipeline.py.")


if __name__ == "__main__":
    main()
