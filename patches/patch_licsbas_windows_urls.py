"""
One-time Windows compatibility patch for LiCSBAS01_get_geotiff.py.

Root cause: the script builds download URLs using os.path.join(), which
on Windows joins paths with backslashes ('\\') instead of forward slashes
('/'). A URL like ".../metadata\\file.tif" is invalid, so every download
fails with an HTTPError — even though nothing is wrong with your network,
frame ID, or date range.

This patches only the URL-building os.path.join() calls (verified against
the actual file content), appending .replace(os.sep, '/') so the result
always uses forward slashes for the web request. The local-filesystem
os.path.join() calls — output directories and the "save to disk" side of
each download pair — are deliberately left untouched, since those should
keep native Windows path separators.

Run this once after cloning/re-cloning LiCSBAS, before your first
download attempt. Safe to re-run — if a pattern is already patched or
already fixed upstream, it just prints a warning and skips it rather than
double-patching or erroring.
"""

TARGET = r"D:\Project_resume\tools\LiCSBAS\bin\LiCSBAS01_get_geotiff.py"

# Exact substring -> exact replacement. Only single-line URL assignments.
REPLACEMENTS = [
    (
        "url = os.path.join(LiCSARweb, trackID, frameID, 'metadata', enutif)",
        "url = os.path.join(LiCSARweb, trackID, frameID, 'metadata', enutif).replace(os.sep, '/')",
    ),
    (
        "url = os.path.join(LiCSARweb, trackID, frameID, 'metadata', 'baselines')",
        "url = os.path.join(LiCSARweb, trackID, frameID, 'metadata', 'baselines').replace(os.sep, '/')",
    ),
    (
        "url = os.path.join(LiCSARweb, trackID, frameID, 'metadata', 'network.png')",
        "url = os.path.join(LiCSARweb, trackID, frameID, 'metadata', 'network.png').replace(os.sep, '/')",
    ),
    (
        "url = os.path.join(LiCSARweb, trackID, frameID, 'metadata', 'metadata.txt')",
        "url = os.path.join(LiCSARweb, trackID, frameID, 'metadata', 'metadata.txt').replace(os.sep, '/')",
    ),
    (
        "url = os.path.join(LiCSARweb, trackID, frameID, 'epochs/')",
        "url = os.path.join(LiCSARweb, trackID, frameID, 'epochs/').replace(os.sep, '/')",
    ),
    (
        "url_epoch = os.path.join(url, imd + '/')",
        "url_epoch = os.path.join(url, imd + '/').replace(os.sep, '/')",
    ),
    (
        "url_mli = os.path.join(url_epoch, imd+'.geo.mli.tif')",
        "url_mli = os.path.join(url_epoch, imd+'.geo.mli.tif').replace(os.sep, '/')",
    ),
    (
        "url_ifgdir = os.path.join(LiCSARweb, trackID, frameID, 'interferograms/')",
        "url_ifgdir = os.path.join(LiCSARweb, trackID, frameID, 'interferograms/').replace(os.sep, '/')",
    ),
]

# These patterns each appear twice (main download block + retry block).
# Only the URL side of each download pair — never the local save-path
# side, which is a separate, different string and is left untouched.
PAIR_URL_PATTERNS = [
    "os.path.join(url, imd, '{}.sltd.geo.tif'.format(imd))",
    "os.path.join(url, imd, '{}.icams.sltd.geo.tif'.format(imd))",
    "os.path.join(url_ifgdir, ifgd, '{0}.geo.{1}.tif'.format(ifgd, ext))",
    "os.path.join(url, imd, '{}.geo.mli.tif'.format(imd))",
]


def main():
    with open(TARGET, "r", encoding="utf-8") as f:
        content = f.read()

    changed = 0

    for old, new in REPLACEMENTS:
        if old in content:
            content = content.replace(old, new)
            changed += 1
        else:
            print(f"NOTE: exact text not found (already patched?): {old[:60]}...")

    for pattern in PAIR_URL_PATTERNS:
        count = content.count(pattern)
        if count:
            content = content.replace(pattern, pattern + ".replace(os.sep, '/')")
            changed += count
        else:
            print(f"NOTE: exact text not found (already patched?): {pattern[:60]}...")

    with open(TARGET, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"\nPatched {changed} occurrence(s) in {TARGET}")
    print("If this ran with 0 changes and downloads still fail with the")
    print("same backslash-in-URL symptom, paste the file's current")
    print("os.path.join lines again — the fork may have changed slightly")
    print("since this patch was written.")


if __name__ == "__main__":
    main()
