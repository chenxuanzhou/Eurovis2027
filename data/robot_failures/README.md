# UCI Robot Execution Failures

Wrist force/torque readings of an assembly robot right after a failure was detected (Lopes and
Camarinha-Matos, UCI, 1999): 15 samples of Fx, Fy, Fz, Tx, Ty, Tz over 315 ms per instance, integer
readings (units not documented). Five learning problems, each a different motion:

| Problem | Motion | Instances | Classes |
|---|---|---|---|
| LP1 | approach to grasp position | 88 | normal, collision, fr_collision, obstruction |
| LP2 | transfer of a part | 47 | normal, front_col, back_col, left_col, right_col |
| LP3 | position of part after a transfer failure | 47 | ok, slightly_moved, moved, lost |
| LP4 | approach to ungrasp position | 117 | normal, collision, obstruction |
| LP5 | motion with part | 164 | normal, bottom_collision, bottom_obstruction, collision_in_part, collision_in_tool |

The raw files are small and CC BY 4.0, so they are in `raw/` unchanged. Licence: `../LICENSE.md`.

## The five files reuse the same readings

The 463 instances hold only **251 distinct readings** (`windows.csv`). LP3 relabels the 47 LP2 windows
by where the part ended up; LP5 pools the LP2 and LP4 windows under a location/direction taxonomy
(46 + 117 + 1 of its own). So one physical window can be, say, `left_col` in LP2, `slightly_moved` in
LP3 and `collision_in_part` in LP5. Two windows occur twice inside one problem; one of them is
`collision_in_tool` and `collision_in_part` at the same time in LP5 (`LP5-045`, `LP5-046`). Any
learned component must group by `window_id`, which `splits/grouped_cv.json` does.

## Files

| File | Contents |
|---|---|
| `instances.csv` | `instance_id` (e.g. `LP2-007`), `problem`, `position` in its file, `label`, `mode` (knowledge-base id), `normal`, `window_id`, `shared_with` (instances with identical readings) |
| `windows.csv` | `window_id`, its label in each problem (`|` joins two labels of a repeated window), `primary` problem |
| `signals.csv` | `instance_id`, `step` 0–14, `Fx` … `Tz` |
| `envelope.csv` | normal profile per `problem`, `step`, `channel`: `mean`, `std`, `scale` = max(std, 0.05 × range of the mean, 1), `n` |
| `evidence/slots.csv` | per instance and channel: `z_peak`, `z_signed` (mean z), `z_step` (last third − first third), `z_std`; z against the normal profile of its problem, leave-one-out for normal instances |
| `splits/grouped_cv.json` | 5 folds × 5 seeds, grouped by window, stratified by the label in the primary problem |
| `kb/` | knowledge base, see below |

## Knowledge base (authored for this repository)

The dataset gives class names only. `kb/` reads them with elementary contact mechanics
(`pipeline/robot_failures/kb_spec.py`; assumptions A1–A6 in `kb/assumptions.json`). Evidence levels:
L1 task context → L2 load change → L3 force axis → L4 force sense → L5 moment pattern (tool vs part,
payload shift) → L6 time course (impact vs sustained). Blocks per level: 1, 5, 10, 16, 18, 19, 20;
instances whose true mode sits in a twin block: 463, 463, 334, 171, 144, 71, 24.

| Twins | From | Split by |
|---|---|---|
| LP2 front vs back collision; left vs right | L3 | L4 force sense |
| LP5 collision in part vs in tool | L3 | L5 moment pattern |
| LP5 bottom collision vs bottom obstruction | L3 | L6 time course |
| LP3 moved vs slightly moved | L3 | never: same change at a different magnitude (A5) |

Classes named only "collision" (LP1, LP4) do not fix a side, so the specific classes of the same
problem are nested inside them (one-way isolability, `nested_pairs`). Files: `failure_modes.json`,
`assumptions.json`, `fsm.csv`, `refinement_lattice.json` (schema in `../README.md`), `twin_groups.json`.
