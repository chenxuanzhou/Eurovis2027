# Paderborn bearings (KAt-DataCenter)

Ball bearings of type 6203 in the Paderborn test rig (Lessmeier et al., PHM Europe 2016): a 425 W motor
on a frequency converter drives a shaft with the test bearing; vibration of the bearing housing and two
phase currents are sampled at 64 kHz, speed, torque and radial force at 4 kHz, temperature at 1 Hz.
This subset holds the 12 bearings most used for real-damage studies: 4 healthy (K001–K004), 4 with
outer-ring damage (KA04, KA15, KA16, KA22) and 4 with inner-ring damage (KI04, KI14, KI16, KI18), all
damages from accelerated lifetime tests. Each bearing has 20 measurements of 4 s under each of 4
operating conditions: N15_M07_F10 (1500 rpm, 0.7 N m, 1000 N), N09_M07_F10 (900 rpm), N15_M01_F10
(0.1 N m) and N15_M07_F04 (400 N). The raw files (8.4 GB) are not redistributed; see `raw/README.md`.
Licence: `../LICENSE.md` (CC BY-NC 4.0).

## What the fact sheets add

The failure modes follow the damage recorded in each bearing's fact sheet, not the folder code alone:

| Bearing | Folder | Fact-sheet damage | Mode |
|---|---|---|---|
| KA04, KA22 | OR | outer-ring fatigue pitting, single | `OR_pitting` |
| KA16 | OR | outer-ring fatigue pitting, two repetitive pits | `OR_pitting_repetitive` |
| KA15 | OR | outer-ring indentations by particles (< 1 mm) | `OR_indentation` |
| KI16, KI18 | IR | inner-ring fatigue pitting, single | `IR_pitting` |
| KI04, KI14 | IR | inner-ring pitting **and** outer-ring indentations ("multiple damage") | `IR_pitting+OR_indentation` |

KI04 and KI14 are compound faults that the usual three-class labelling (healthy / OR / IR) calls IR.
`bearings.csv` keeps both the folder class and the fact-sheet mode.

Identical signals: seven KA04 files form three groups of exact copies (N09_M07_F10 `_17` = `_18`,
which the KA04 measuring log documents as a replacement; N15_M07_F04 `_6` = `_15` = `_20` and `_5` =
`_19`). Leave-bearing-out folds keep them together. One more KA04 file, N09_M07_F10 `_13`, ran at an
unsteady speed (680–1275 rpm instead of 900); `measurement_groups.csv` flags it (`unsteady_speed`)
because its order-domain spectra are smeared.

## Files

| File | Contents |
|---|---|
| `measurements.csv` | one row per file (960): `measurement_id`, `file`, `bearing`, `condition`, set points, measured `speed_rpm`, `torque_Nm`, `force_N`, `temp_C`, `f_shaft_Hz`, `f_supply_Hz`, bearing geometry and defect frequencies in shaft orders (`FTF`, `BPFO`, `BPFI`, `BSF`), vibration `rms` / `kurtosis` / `crest`, envelope line levels `env_<line>_dB` (fr, FTF, BSF, BPFO, 2BPFO, BPFI, 2BPFI, BPFI ± fr), current RMS and the strongest current sideband at f_supply ± BPFO / BPFI (`cur_*_sb_dB`), `signal_hash` |
| `spectra/envelope_orders.parquet` | envelope spectrum of the vibration (2–16 kHz band), `order` 0–12 in 0.01 steps, per measurement |
| `spectra/current_sidebands.parquet` | phase-current spectrum around the supply frequency, `offset_order` −12…+12 shaft orders in 0.02 steps, dB re the fundamental |
| `bearings.csv` | folder class, fact-sheet mode, maker, damage summary |
| `measurement_groups.csv` | mode per measurement, `same_signals_as`, `quality_flag` |
| `evidence/features_z.csv` | 16 features per measurement: value and robust z against the healthy bearings under the same condition, leaving the measurement's own bearing out |
| `splits/leave_bearing_out.json` | 4 folds × 5 seeds; each fold holds out one healthy, one OR and one IR bearing |
| `kb/` | knowledge base, see below |

Line levels are the maximum within ±1.5 % of the line, in dB above the median of the surrounding ±5 Hz.

## Knowledge base (authored for this repository)

`pipeline/paderborn/kb_spec.py`, assumptions P1–P5 in `kb/assumptions.json`. Levels, ordered by what a
drive-integrated monitor gets first: L1 drive current → L2 current sidebands → L3 vibration → L4
envelope spectrum → L5 raceway inspection (fact sheet). Blocks per level: 1, 2, 4, 4, 4, 6. The three
outer-ring damage types are twins from L2 to L4 and only an inspection separates them; single damage on
one ring is nested in the compound mode (one-way). `kb/evidence_map.json` lists which measured features
speak to each symptom row.

What the data say about it: structurally, current sidebands (L2) already separate outer- from inner-ring
damage, but their measured levels do not move (median |z| < 0.5 for every bearing), while the envelope
lines do for some bearings and not for others (BPFO z ≈ 9 for KA04 and KA16, < 1 for KA15 and KA22).
That is the gap between structural and statistical isolability the project is about.
