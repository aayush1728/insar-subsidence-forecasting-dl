"""
Windows compatibility patch for LiCSBAS05op_clip_unw.py.

Same root cause as the LiCSBAS02_ml_prep.py patch (see
patch_licsbas02_windows_spawn.py for the full explanation): main() sets
module-level globals at runtime, worker processes under Windows 'spawn'
don't inherit them, so clip_wrapper() fails with NameError.

Confirmed via inspection of this specific file:
  - globals set in main(): ifgdates2, in_dir, out_dir, length, width,
    x1, x2, y1, y2, cycle, cmap_wrap, bool_mask
  - Pool created at: p = q.Pool(n_para)
  - worker function: def clip_wrapper(ifgix):

Run once. Safe to re-run — checks for the real function definition
(not just a reference to it) before deciding whether to insert.
"""

TARGET = r"D:\Project_resume\tools\LiCSBAS\bin\LiCSBAS05op_clip_unw.py"

INIT_FUNC = '''
def _init_worker(_ifgdates2, _in_dir, _out_dir, _length, _width, _x1, _x2, _y1, _y2, _cycle, _cmap_wrap, _bool_mask):
    """Set module-level globals inside each spawned worker process.

    Needed on Windows because 'spawn' workers don't inherit the parent
    process's memory the way Linux 'fork' workers do.
    """
    global ifgdates2, in_dir, out_dir, length, width, x1, x2, y1, y2, cycle, cmap_wrap, bool_mask
    ifgdates2, in_dir, out_dir, length, width, x1, x2, y1, y2, cycle, cmap_wrap, bool_mask = \\
        _ifgdates2, _in_dir, _out_dir, _length, _width, _x1, _x2, _y1, _y2, _cycle, _cmap_wrap, _bool_mask


'''

POOL_OLD = "p = q.Pool(n_para)"
POOL_NEW = (
    "p = q.Pool(\n"
    "        n_para,\n"
    "        initializer=_init_worker,\n"
    "        initargs=(ifgdates2, in_dir, out_dir, length, width, x1, x2, y1, y2, cycle, cmap_wrap, bool_mask),\n"
    "    )"
)

DEF_MARKER = "def clip_wrapper"


def main():
    with open(TARGET, "r", encoding="utf-8") as f:
        content = f.read()

    changed = 0

    if POOL_OLD in content:
        content = content.replace(POOL_OLD, POOL_NEW)
        changed += 1
        print("Patched Pool(...) creation with initializer.")
    else:
        print(f"NOTE: exact text not found (already patched?): {POOL_OLD}")

    if "def _init_worker" in content:
        print("NOTE: _init_worker already present — skipped function insertion.")
    else:
        lines = content.splitlines(keepends=True)
        target_idx = None
        for i, line in enumerate(lines):
            if line.lstrip().startswith(DEF_MARKER):
                target_idx = i
                break

        if target_idx is None:
            print(f"NOTE: no line starting with '{DEF_MARKER}' found — skipped.")
        else:
            lines.insert(target_idx, INIT_FUNC)
            content = "".join(lines)
            changed += 1
            print(f"Inserted _init_worker() before line {target_idx + 1} "
                  f"({lines[target_idx + 1].strip()[:60]}...).")

    with open(TARGET, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"\nDone. {changed} change(s) applied to {TARGET}")
    if changed < 2:
        print("WARNING: fewer than 2 changes applied — check the NOTE lines above.")


if __name__ == "__main__":
    main()
