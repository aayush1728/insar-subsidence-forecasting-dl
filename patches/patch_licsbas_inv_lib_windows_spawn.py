"""
Windows compatibility patch for LiCSBAS_inv_lib.py.

Same root cause as the bin/ script patches. This library file has THREE
Pool() call sites, all with identical text "p = q.Pool(n_core)":
  - One (line ~236) uses functools.partial() to bind its arguments
    directly — already spawn-safe, no patch needed, since values travel
    with the pickled function rather than relying on inherited memory.
  - Two (lines ~383, ~705) rely on module-level globals (Gall, unw_tmp,
    var_tmp, mask) set inside invert_nsbas()/invert_wls() — these need
    the initializer fix.

Since all three sites share identical text, one replace covers all of
them. Passing the unused globals to the partial-based worker is
harmless — it just never accesses them.

Run once. Safe to re-run.
"""

TARGET = r"D:\Project_resume\tools\LiCSBAS\LiCSBAS_lib\LiCSBAS_inv_lib.py"

GLOBAL_NAMES = ["Gall", "unw_tmp", "var_tmp", "mask"]

_params = ", ".join(f"_{n}" for n in GLOBAL_NAMES)
_globals_line = ", ".join(GLOBAL_NAMES)

INIT_FUNC = f'''
def _init_worker({_params}):
    """Set module-level globals inside each spawned worker process.

    Needed on Windows because 'spawn' workers don't inherit the parent
    process's memory the way Linux 'fork' workers do.
    """
    global {_globals_line}
    {_globals_line} = {_params}


'''

_names_list_literal = ", ".join(f"'{n}'" for n in GLOBAL_NAMES)
_initargs_expr = f"tuple(globals().get(n) for n in [{_names_list_literal}])"

POOL_OLD = "p = q.Pool(n_core)"
POOL_NEW = f"p = q.Pool(n_core, initializer=_init_worker, initargs={_initargs_expr})"

DEF_MARKER = "def censored_lstsq_slow_para_wrapper"


def main():
    with open(TARGET, "r", encoding="utf-8") as f:
        content = f.read()

    changed = 0

    count = content.count(POOL_OLD)
    if count:
        content = content.replace(POOL_OLD, POOL_NEW)
        changed += count
        print(f"Patched {count} occurrence(s) of: {POOL_OLD}")
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
    if changed < 4:
        print("WARNING: expected 4 changes (3 Pool sites + 1 function insert) "
              "— check the NOTE lines above.")


if __name__ == "__main__":
    main()
