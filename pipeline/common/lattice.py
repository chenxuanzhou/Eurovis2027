"""Structural isolability over a chain of evidence levels, in one schema for every dataset.

A knowledge base gives each failure mode a binary column per evidence level: the symptom rows
the mode is expected to switch on. Levels are cumulative, so level k reads the rows of levels
1..k. Following structural FDI, mode a is isolable from mode b at a level when some cumulative
row is 1 for a and 0 for b. Modes with identical cumulative columns form a block (structural
twins at that level); a column strictly contained in another gives a one-way (nested) pair.

Output schema "refinement-lattice/1" (kb/refinement_lattice.json of every dataset):
  modes                     display order; every level's blocks are contiguous in it
  mode_label                the dataset label each mode corresponds to (None if not in the data)
  null_modes                ids of the no-fault hypotheses when they are part of the problem (else [])
  instances_per_mode        labelled instances of each mode in the data
  levels[]                  L0 (no evidence) then one entry per evidence level:
      rows_added, blocks, block_parent (index into the previous level's blocks), n_blocks,
      twin_blocks, nested_pairs [{inner, outer}], isolable[a][b],
      instances_with_true_mode_in_twin_block
"""
from __future__ import annotations

SCHEMA = "refinement-lattice/1"


def refinement_lattice(dataset: str, levels: list[dict], columns: dict[str, dict[str, list[int]]],
                       instances_per_mode: dict[str, int], *, description: str,
                       mode_label: dict | None = None, null_modes: list[str] | None = None) -> dict:
    """levels: [{id, label, adds, read_by_deployed_score, rows}], columns[level_id][mode] -> 0/1 per row.

    read_by_deployed_score is True/False for a dataset with a deployed diagnoser (voraus-AD) and
    None where there is none.
    """
    modes = list(columns[levels[0]["id"]])
    cum = {m: [] for m in modes}
    keys = {m: [] for m in modes}
    level_cols = {}
    for lv in levels:
        for m in modes:
            col = [int(x) for x in columns[lv["id"]][m]]
            if len(col) != len(lv["rows"]):
                raise ValueError(f"{dataset} {lv['id']} {m}: {len(col)} values for {len(lv['rows'])} rows")
            cum[m] = cum[m] + col
            keys[m].append("".join(map(str, cum[m])))
        level_cols[lv["id"]] = {m: list(cum[m]) for m in modes}
    # lexicographic order over the cumulative keys keeps every level's blocks contiguous
    order = sorted(modes, key=lambda m: tuple(keys[m]))
    n_inst = {m: int(instances_per_mode.get(m, 0)) for m in order}

    def summary(blocks, col):
        isolable = {a: {b: (col is not None and any(x and not y for x, y in zip(col[a], col[b])))
                        for b in order if b != a} for a in order}
        twins = [b for b in blocks if len(b) > 1]
        nested = [{"inner": a, "outer": b} for a in order for b in order
                  if a != b and not isolable[a][b] and isolable[b][a]]
        return {"n_blocks": len(blocks), "twin_blocks": twins, "nested_pairs": nested, "isolable": isolable,
                "instances_with_true_mode_in_twin_block": sum(n_inst[m] for b in twins for m in b)}

    out_levels = [{"id": "L0", "label": "No evidence", "adds": "nothing", "read_by_deployed_score": True,
                   "rows_added": [], "blocks": [order], "block_parent": [None], **summary([order], None)}]
    prev = [order]
    for k, lv in enumerate(levels):
        blocks: list[list[str]] = []
        seen: dict[str, int] = {}
        for m in order:
            key = keys[m][k]
            if key not in seen:
                seen[key] = len(blocks)
                blocks.append([])
            blocks[seen[key]].append(m)
        parent = [next(p for p, pb in enumerate(prev) if b[0] in pb) for b in blocks]
        out_levels.append({"id": lv["id"], "label": lv["label"], "adds": lv["adds"],
                           "read_by_deployed_score": lv["read_by_deployed_score"], "rows_added": list(lv["rows"]),
                           "blocks": blocks, "block_parent": parent, **summary(blocks, level_cols[lv["id"]])})
        prev = blocks
    return {
        "schema": SCHEMA, "dataset": dataset, "description": description,
        "modes": order, "mode_label": {m: (mode_label or {}).get(m) for m in order},
        "null_modes": list(null_modes or []), "instances_per_mode": n_inst, "levels": out_levels,
    }


def fsm_table(levels: list[dict], columns: dict[str, dict[str, list[int]]], order: list[str]) -> list[dict]:
    """The full fault signature matrix as rows {level, symptom, <mode>: 0/1, ...} in level order."""
    out = []
    for lv in levels:
        for r, row in enumerate(lv["rows"]):
            out.append({"level": lv["id"], "symptom": row, **{m: int(columns[lv["id"]][m][r]) for m in order}})
    return out


def twin_resolution(lat: dict, fsm: list[dict]) -> list[dict]:
    """Every twin block that first appears at some level, the level that splits it and the rows that do.

    A block that no level splits is a structural twin of the whole knowledge base: only a
    quantitative (statistical) criterion or evidence outside the knowledge base can separate it.
    """
    levels = lat["levels"]
    out, seen = [], set()
    for k, lv in enumerate(levels[1:], start=1):
        for block in lv["twin_blocks"]:
            key = frozenset(block)
            if key in seen:
                continue
            seen.add(key)
            resolved_at, rows = None, []
            for later in levels[k + 1:]:
                if not any(set(block) <= set(b) for b in later["blocks"]):
                    resolved_at = later["id"]
                    rows = [r["symptom"] for r in fsm if r["level"] == later["id"]
                            and len({r[m] for m in block}) > 1]
                    break
            out.append({"members": block, "twins_from": lv["id"], "resolved_at": resolved_at,
                        "resolving_rows": rows,
                        "instances": sum(lat["instances_per_mode"][m] for m in block)})
    return out


def check_lattice(lat: dict) -> list[str]:
    """Structural invariants every lattice must satisfy; returns a list of problems (empty = fine)."""
    problems = []
    order = lat["modes"]
    pos = {m: i for i, m in enumerate(order)}
    for prev, cur in zip(lat["levels"], lat["levels"][1:]):
        for b, p in zip(cur["blocks"], cur["block_parent"]):
            if not set(b) <= set(prev["blocks"][p]):
                problems.append(f"{cur['id']}: block {b} not inside its parent")
        if sorted(m for b in cur["blocks"] for m in b) != sorted(order):
            problems.append(f"{cur['id']}: blocks do not partition the modes")
        for b in cur["blocks"]:
            idx = sorted(pos[m] for m in b)
            if idx != list(range(idx[0], idx[0] + len(idx))):
                problems.append(f"{cur['id']}: block {b} not contiguous in the display order")
    return problems
