"""
Windows compatibility patch for LiCSBAS13_sb_inv.py.

Same root cause as the step 02/05/12 patches. This file has FOUR active
Pool() call sites across different stages (nullify_noloops, gap
counting, increment PNG generation, residual PNG/txt generation), all
sharing one set of 24 globals declared once in main().

One site uses a `with q.Pool(...) as p:` context-manager pattern rather
than a plain assignment — handled the same way (initializer/initargs go
inside the Pool(...) call regardless of how the result is used).

As with step 12: not all 24 globals are set yet at every call site (this
script computes things progressively), so initargs pulls each value from
globals() with a None fallback rather than assuming all are ready.

Run once. Safe to re-run.
"""

TARGET = r"D:\Project_resume\tools\LiCSBAS\bin\LiCSBAS13_sb_inv.py"

GLOBAL_NAMES = [
    "n_para", "n_para_gap", "G", "Aloop", "unwpatch", "hasdatapatch",
    "imdates", "incdir", "ifgdir", "length", "width", "coef_r2m",
    "ifgdates", "ref_unw", "cycle", "keep_incfile", "resdir",
    "restxtfile", "cmap_vel", "cmap_wrap", "wavelength",
    "nullify_noloops", "debugflag", "estimate_ts_errors",
]

_params = ", ".join(f"_{n}" for n in GLOBAL_NAMES)
_globals_line = ", ".join(GLOBAL_NAMES)

INIT_FUNC = f'''
def _init_worker({_params}):
    """Set module-level globals inside each spawned worker process.

    Needed on Windows because 'spawn' workers don't inherit the parent
    process's memory the way Linux 'fork' workers do.
    """
    global {_globals_line}
    {_globals_line} = \\
        {_params}


'''

_names_list_literal = ", ".join(f"'{n}'" for n in GLOBAL_NAMES)
_initargs_expr = f"tuple(globals().get(n) for n in [{_names_list_literal}])"

REPLACEMENTS = [
    (
        "p = q.Pool(n_para)",
        f"p = q.Pool(n_para, initializer=_init_worker, initargs={_initargs_expr})",
    ),
    (
        "p = q.Pool(n_para_gap)",
        f"p = q.Pool(n_para_gap, initializer=_init_worker, initargs={_initargs_expr})",
    ),
    (
        "with q.Pool(_n_para) as p:",
        f"with q.Pool(_n_para, initializer=_init_worker, initargs={_initargs_expr}) as p:",
    ),
    (
        "p = q.Pool(_n_para)",
        f"p = q.Pool(_n_para, initializer=_init_worker, initargs={_initargs_expr})",
    ),
]

DEF_MARKER = "def count_gaps_wrapper"


def main():
    with open(TARGET, "r", encoding="utf-8") as f:
        content = f.read()

    changed = 0

    for old, new in REPLACEMENTS:
        count = content.count(old)
        if count:
            content = content.replace(old, new)
            changed += count
            print(f"Patched {count} occurrence(s) of: {old}")
        else:
            print(f"NOTE: exact text not found (already patched?): {old}")

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
    if changed < 5:
        print("WARNING: expected 5 changes (4 Pool sites + 1 function insert) "
              "— check the NOTE lines above.")


if __name__ == "__main__":
    main()
