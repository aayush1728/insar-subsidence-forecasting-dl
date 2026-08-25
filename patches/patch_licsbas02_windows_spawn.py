"""
Windows compatibility patch for LiCSBAS02_ml_prep.py.

Root cause: main() sets several module-level globals (geocdir, outdir,
nlook, etc.) at runtime, then hands work to convert_wrapper() via a
multiprocessing Pool. Under Linux's 'fork' method (what this script was
written for), worker processes inherit the parent's memory automatically,
so those globals are already there. Under Windows' 'spawn' method (what
we switched to earlier, since 'fork' doesn't exist on Windows), each
worker starts as a fresh Python process that re-imports the module from
scratch — so anything set dynamically inside main() at runtime is simply
absent, causing NameError: name 'geocdir' is not defined.

Fix: add a Pool initializer function that explicitly sets these globals
inside each worker at startup, and pass the current values through as
initargs when the Pool is created.

Run this once. Safe to re-run — if the exact text isn't found (already
patched, or a different LiCSBAS version), it prints a warning and changes
nothing rather than corrupting the file.
"""

TARGET = r"D:\Project_resume\tools\LiCSBAS\bin\LiCSBAS02_ml_prep.py"

INIT_FUNC = '''
def _init_worker(_geocdir, _outdir, _nlook, _n_valid_thre, _cycle, _cmap_wrap, _plot_cc, _cmap_cc, _width, _length, _coh_thre):
    """Set module-level globals inside each spawned worker process.

    Needed on Windows because 'spawn' workers don't inherit the parent
    process's memory the way Linux 'fork' workers do — anything main()
    set at runtime (rather than at import time) is otherwise missing.
    """
    global geocdir, outdir, nlook, n_valid_thre, cycle, cmap_wrap, plot_cc, cmap_cc, width, length, coh_thre
    geocdir, outdir, nlook, n_valid_thre, cycle, cmap_wrap, plot_cc, cmap_cc, width, length, coh_thre = \\
        _geocdir, _outdir, _nlook, _n_valid_thre, _cycle, _cmap_wrap, _plot_cc, _cmap_cc, _width, _length, _coh_thre


'''

POOL_OLD = "p = q.Pool(n_para)"
POOL_NEW = (
    "p = q.Pool(\n"
    "                n_para,\n"
    "                initializer=_init_worker,\n"
    "                initargs=(geocdir, outdir, nlook, n_valid_thre, cycle, cmap_wrap, plot_cc, cmap_cc, width, length, coh_thre),\n"
    "            )"
)

DEF_MARKER = "def convert_wrapper"


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
        print("WARNING: fewer than 2 changes applied — check the NOTE lines")
        print("above. The patch may not be fully effective; paste the error")
        print("if it still fails after retrying.")


if __name__ == "__main__":
    main()
