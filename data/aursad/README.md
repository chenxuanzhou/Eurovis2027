# AURSAD (UR3e screwdriving)

A UR3e cobot with an OnRobot screwdriver loosens a screw from one plate and tightens it into another
(Leporowski et al., arXiv:2102.01409). 125 robot and screwdriver signals at 100 Hz. Labels: normal (0),
damaged screw (1, filed thread), extra assembly component (2, a washer on the hole), missing screw (3,
mostly a skipped pick-up), damaged plate thread (4, a filed or chipped hole) for the 2,045 tightening
samples, and 5 for the 2,049 loosening (pick-up) samples. The raw file (6.4 GB) is not redistributed;
see `raw/README.md`. Licence: `../LICENSE.md` (CC BY 4.0).

## Duplicated recordings with different labels

`AURSAD.h5` contains several recording segments twice. Of the 4,094 samples only **3,127 are distinct**:
967 pairs are byte-identical in every sensor column and timestamp, and in **61 pairs the two copies carry
different labels** (normal vs damaged screw 30, normal vs extra component 17, normal vs missing screw 7,
normal vs damaged plate thread 1, damaged screw vs extra component 4, damaged screw vs missing screw 2).
Of the 2,045 tightening samples, 1,561 are distinct. A random split, as in the original benchmark,
puts copies on both sides; `splits/leave_session_out.json` groups whole recording sessions instead.
`data_quality.json` has the counts, `sample_groups.csv` the per-sample flags.

A possible shortcut: the loosening sample just before an extra-component tightening is about half as
long as usual (median 3.9 s vs 7.8 s; `prev_loosen_screw_s` in the evidence). That sample comes before
the washer is screwed down, so a model that relies on it is not detecting the washer itself.

## Files

| File | Contents |
|---|---|
| `samples.csv` | one row per sample (4,094): `label`, `kind`, pins (`pin_to`, `pin_from`), `t_start`/`t_end`, phase durations (`move_s`, `screw_s`, `return_s`), screwdriver features (target, achieved and peak torque, `torque_rise_s` to half the target, `torque_drops`), wrist features while screwing (`fz_mean_screw`, `mz_absmax_screw`, …), tool z, accelerometer RMS, joint temperature, `signal_hash`, `same_signals_as` |
| `sample_groups.csv` | `run` (continuous recording), `session` (runs merged where they share recordings), `duplicate_group`, `n_copies`, `label_conflict`, `labels_of_copies`, features of the preceding loosening |
| `signals/grid500/tighten_<label>.parquet` | each distinct tightening sample on a phase-aligned grid: 150 points moving to the hole, 250 screwdriving, 100 returning; 20 channels (screwdriver current and achieved torque, tool z and z speed, wrist force/torque estimate, 6 joint currents, tool accelerometer, robot current); float32 rounded to 12 mantissa bits. A copy is stored under the label of its first occurrence |
| `envelope/normal_envelope_grid500.parquet` | normal profile per channel and grid point from distinct, conflict-free normal samples |
| `evidence/features_z.csv` | 16 features per tightening sample: value and robust z against the normal samples of the other sessions |
| `splits/leave_session_out.json` | 5 folds × 5 seeds over 30 sessions |
| `kb/` | knowledge base, see below |

Phases come from the screwdriver registers: the tightening command (`output_bit_register_67`) starts
screwdriving, the end of the last busy period (`output_bit_register_70`) after it ends it.

## Knowledge base (authored for this repository)

`pipeline/aursad/kb_spec.py`, assumptions B1–B6 in `kb/assumptions.json`. Levels: L1 screwdriver torque
→ L2 seating time → L3 wrist reaction → L4 preceding pick-up → L5 history across cycles. Blocks per level:
1, 2, 4, 4, 4, 5. Damaged screw and damaged plate thread are twins from L2 to L4: the same thread damage
on a different part, separable only by whether the fault recurs with a screw or at a hole. AURSAD records
the hole (`pin_to`) but not the screw, so only half of that evidence is observable. Extra component is
nested in both (a washer only makes seating early; a damaged thread can make it early or late).
