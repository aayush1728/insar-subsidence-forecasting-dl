"""
Windows compatibility patch for LiCSBAS12_loop_closure.py.

Same root cause as the step 02/05 patches (see
patch_licsbas02_windows_spawn.py for the full explanation), but this file
has FOUR separate Pool() call sites across different processing stages
(1st/2nd/3rd loop closure check + PNG generation), all sharing one set of
21 globals declared once in main().

Complication: some of those globals (bad_ifg, refy1/y2/x1/x2, etc.) are
only computed by later stages — they don't exist yet when the FIRST
Pool() runs. So instead of a fixed tuple, the initargs expression pulls
each value from globals() with a fallback of None if not yet set. Safe
because a given worker function only touches the subset of globals it
actually uses; the ones that are still None simply aren't touched yet.

Run once. Safe to re-run — checks for the real function definition
before deciding whether to insert.
"""

TARGET = r"D:\Project_resume\tools\LiCSBAS\bin\LiCSBAS12_loop_closure.py"

GLOBAL_NAMES = [
    "Aloop", "resultsdir", "ifgdates", "ifgdir", "length", "width",
    "loop_pngdir", "cycle", "nullify_threshold", "save_ori_unw",
    "nullify_fix_ref", "multi_prime", "bad_ifg", "noref_ifg",
    "bad_ifg_all", "refy1", "refy2", "refx1", "refx2", "cmap_noise_r",
    "nullify_aggressive",
]

_params = ", ".join(f"_{n}" for n in GLOBAL_NAMES)
_globals_line = ", ".join(GLOBAL_NAMES)
_assign_line = ", ".join(GLOBAL_NAMES)
_assign_vals = ", ".join(f"_{n}" for n in GLOBAL_NAMES)

INIT_FUNC = f'''
def _init_worker({_params}):
    """Set module-level globals inside each spawned worker process.

    Needed on Windows because 'spawn' workers don't inherit the parent
    process's memory the way Linux 'fork' workers do.
    """
    global {_globals_line}
    {_assign_line} = \\
        {_assign_vals}


'''

_names_list_literal = ", ".join(f"'{n}'" for n in GLOBAL_NAMES)
_initargs_expr = f"tuple(globals().get(n) for n in [{_names_list_literal}])"

POOL_OLD_1 = "p = q.Pool(_n_para)"
POOL_NEW_1 = f"p = q.Pool(_n_para, initializer=_init_worker, initargs={_initargs_expr})"

POOL_OLD_2 = "p = q.Pool(_n_para2)"
POOL_NEW_2 = f"p = q.Pool(_n_para2, initializer=_init_worker, initargs={_initargs_expr})"

DEF_MARKER = "def loop_closure_1st_wrapper"


def main():
    with open(TARGET, "r", encoding="utf-8") as f:
        content = f.read()

    changed = 0

    count1 = content.count(POOL_OLD_1)
    if count1:
        content = content.replace(POOL_OLD_1, POOL_NEW_1)
        changed += count1
        print(f"Patched {count1} occurrence(s) of Pool(_n_para).")
    else:
        print(f"NOTE: exact text not found (already patched?): {POOL_OLD_1}")

    count2 = content.count(POOL_OLD_2)
    if count2:
        content = content.replace(POOL_OLD_2, POOL_NEW_2)
        changed += count2
        print(f"Patched {count2} occurrence(s) of Pool(_n_para2).")
    else:
        print(f"NOTE: exact text not found (already patched?): {POOL_OLD_2}")

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
