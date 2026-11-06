# Data

Every file here is derived from the voraus-AD dataset (Brockmann et al., IEEE T-RO 2024): a six-axis
collaborative robot (Yu-Cobot, vacuum gripper) repeating one pick-and-place cycle, 130 machine signals,
1,367 anomaly-free and 755 anomalous cycles in 12 anomaly categories from 72 fault instantiations
(`setting` values). The raw file is not redistributed; see `raw/README.md`. Licence: `LICENSE.md`.

## Conventions

- **Cycle id** = the voraus-AD `sample` id. Evidence records call it `cycle_id`.
- **Official split**: training = the 948 anomaly-free cycles with `setting == 72` (Variant `PRE_A`);
  test = the other 1,174 cycles (419 anomaly-free, 755 anomalous).
- **Leave-setting-out splits** (`splits/leave_setting_out.json`): five 50/50 splits of the 755
  anomalous cycles in which every setting is wholly in *fit* or wholly in *test*. Use them for every
  learned component. Cycles of one setting are repeated runs of one physical fault, so a random split
  over cycles leaks (in the SAFEPROCESS study it changed which repair was adopted).
- **Progress grid**: each cycle's time is normalized to [0, 1] and every channel is linearly
  interpolated onto 500 evenly spaced points (`attribution_bridge._resample`). `grid_idx` 0–499.
- **z-scores** in the evidence records: (observed − envelope mean) / envelope scale, where
  scale = max(std, 0.05 × range of the mean curve), computed over the 948 training cycles.
- **Action codes** 0–14 follow the official `Action` enum; odd codes are moves, even codes are
  VOID transitions (`catalog/actions.csv`). The can is carried during actions 7–12.

## Files

### catalog/ (no raw data needed)

| File | Rows | Columns |
|---|---|---|
| `signals.csv` | 130 | `name`, `family`, `joint` (1–6, empty for robot level), `level`, `source` (measured / computed), `domain` (mechanical / electrical), `read_by_kb`, `in_grid500`, `unit`, `unit_source` |
| `categories.csv` | 13 | `category` 0–12, `enum_name`, `paper_name`, `paper_group`, `anomaly`, `kb_mode` (failure-mode id), `kb_mode_name`, `kb_group` |
| `variants.csv` | 77 | `setting` 0–76, `enum_name`, `category`, `official_split` |
| `actions.csv` | 15 | `action`, `enum_name`, `motion` (PTP / LIN / VOID), `phase_class` (pick / place / transfer), `can_carried` |

Units of the four knowledge-base families come from the labels in `attribution_bridge.py`; the other
units are the SI units implied by the signal names (`unit_source` says which).

### kb/ — the FMEA knowledge base as a structural layer (no raw data needed)

| File | Contents |
|---|---|
| `failure_modes.json` | 14 failure modes (12 map to a voraus-AD category, backlash and over-temperature do not): joint scope, manifest families, phase hint, authored physical signature (torque direction, time course), cause, effect, recommendation |
| `fsm_deployed.csv` | Fault signature matrix of the representation the deployed retrieval reads: 26 symptom slots (`family@J<joint>`, `robot_current`, `system_current`) × 14 modes |
| `refinement_lattice.json` | Isolability refinement chain. Levels: L0 no evidence → L1 joint scope → L2 + signal families (deployed) → L3 + phase hint → L4 + physical signature (authored, not read by the deployed score). Per level: `blocks` (modes with identical cumulative columns), `block_parent`, `twin_blocks`, `nested_pairs` (one-way isolability), `isolable[a][b]`, and how many anomalous cycles have their true mode inside a twin block. `modes` gives a display order that keeps every level's blocks contiguous. |
| `twin_groups.json` | The four twin groups of L2 with what would separate them: `resolution_kind` (learned certificate, inspection, sensor gap), hint text in Chinese and English, certificate result |
| `certificates.json` | Certificate results of the SAFEPROCESS study (held-out accuracy, majority and permuted controls, selected dimensions, cost class), copied with source |

Blocks per level: L0 1, L1 4, L2 9, L3 11, L4 13. Anomalous cycles whose true mode sits in a twin
block: L1 718, L2 516, L3 206, L4 94 (only collision with foam vs cardboard remains).

### evidence/

| File | Contents |
|---|---|
| `records_anomalous.json` | Evidence records (schema 0.3) of the 755 anomalous cycles, copied byte for byte from the SAFEPROCESS repository (`SOURCE.json` has commit and sha256). Per record: `localization` (dominant joint and phase, joint rankings), `attributed_signals` (top 5 by peak z), `signature.slots` (26 channels × [z_peak, z_signed, z_step, z_payload, z_std]). No detector score: diagnosis numbers assume perfect detection. |
| `unread_features.json` | The same five statistics for 12 channels the retrieval never reads (`power_load_mech_1..6`, `motor_iq_1..6`), keyed by cycle id |
| `payload_torque.json` | Carried-payload torque per joint measured from normal cycles by pose matching |
| `records_normal_test.json` | *(built from raw)* Evidence records of the 419 anomaly-free test cycles, same builder and envelope |
| `regeneration_check.json` | *(built from raw)* The 755 anomalous records rebuilt from raw and compared slot by slot with the copied ones |

### splits/

`leave_setting_out.json`: per seed 0–4, `fit_settings`, `test_settings`, `fit_cycles`, `test_cycles`, and
the categories absent from either half (categories 5, 8 and 9 have a single setting, so each seed has
them on one side only). The split sizes equal those reported by the SAFEPROCESS study.

### cycles/ *(built from raw)*

| File | Contents |
|---|---|
| `cycles.parquet` / `.csv` | One row per cycle (2,122): `sample`, `category`, `setting`, `anomaly`, `n_rows`, `t_start`, `duration_s`, `dt_median_s`, `active_fraction`, `n_actions`, `official_split`, `lso0`…`lso4` (fit / test / empty) |
| `action_segments.parquet` | One row per contiguous action segment: `sample`, `segment`, `action`, `t_start`, `t_end` (seconds from cycle start), `progress_start`, `progress_end`, `n_rows` |

### envelope/ *(built from raw)*

| File | Contents |
|---|---|
| `normal_envelope_grid500.parquet` | 130 channels × 500 points: `channel`, `grid_idx`, `progress`, `mean`, `std`, `scale`, `q05`, `q25`, `q50`, `q75`, `q95` over the 948 training cycles |
| `normal_phase_grid500.csv` | `grid_idx`, `progress`, `modal_action`, `modal_fraction` across the training cycles |

### signals/grid500/ *(built from raw)*

Per-cycle signals on the progress grid for the 1,174 test cycles (one file per anomaly category,
`anomalous_catNN.parquet`, plus `normal_test.parquet`) and a fixed random sample of 100 training cycles
(`normal_train_sample.parquet`, seed 2027). Columns: `sample`, `grid_idx`, `action`, then 44 channels:
`motor_torque`, `torque_sensor_a`, `joint_velocity`, `joint_position`, `motor_iq`, `power_load_mech`,
`target_torque` for joints 1–6, and `robot_current`, `system_current`. Values are float32 rounded to
12 mantissa bits (relative error ≤ 1.2e-4), which keeps the files small; for analysis at full precision
rebuild from raw. `manifest.json` lists the parts and their cycles.
