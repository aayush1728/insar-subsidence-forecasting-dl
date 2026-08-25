"""
Check COMET-LiCS coverage for the AOI.

The COMET-LiCS portal (https://comet.nerc.ac.uk/comet-lics-portal/) is an
interactive map, not a documented public REST API, so this is a manual
lookup rather than something that can be fully automated. This script's
job is to compute the AOI corners for you and open/print the right place
to look, so you're not eyeballing coordinates on the map by hand.

Run this locally (not in a sandbox without internet access to the portal).
"""

import webbrowser

from config import AOI_BBOX, AOI_CENTER_LAT, AOI_CENTER_LON

PORTAL_URL = "https://comet.nerc.ac.uk/comet-lics-portal/"


def main(open_browser: bool = True) -> None:
    print("AOI center: {:.4f}N, {:.4f}E".format(AOI_CENTER_LAT, AOI_CENTER_LON))
    print("AOI bbox:")
    for key, val in AOI_BBOX.items():
        print(f"  {key}: {val:.4f}")

    print()
    print("Next steps:")
    print(f"1. Open {PORTAL_URL}")
    print("2. Pan/zoom to the AOI center coordinates above.")
    print("3. Look for a frame (coloured shape) covering the AOI.")
    print("   - Frame colour indicates how many products are available;")
    print("     avoid frames with very few products.")
    print("   - Ascending and descending tracks give different look")
    print("     directions — note both frame IDs if available, since")
    print("     combining them later can help resolve vertical vs.")
    print("     horizontal deformation components.")
    print("4. If you find a usable frame:")
    print("   - Note its frame ID (e.g. '115D_05248_131313').")
    print("   - Download products via the portal's Python download tools")
    print("     (linked from the portal page) into data/raw/.")
    print("   - Skip SNAP entirely; go to run_licsbas_pipeline.py.")
    print("5. If no frame covers the AOI or coverage is sparse:")
    print("   - Fall back to raw Sentinel-1 SLC pairs from ASF Vertex")
    print("     (https://search.asf.alaska.edu/) and process them in SNAP")
    print("     (coregistration -> interferogram -> unwrap -> geocode)")
    print("     before feeding the results into LiCSBAS.")

    if open_browser:
        try:
            webbrowser.open(PORTAL_URL)
        except Exception:
            pass


if __name__ == "__main__":
    main()
