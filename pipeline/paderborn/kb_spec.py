"""Knowledge base for the Paderborn bearing subset (12 bearings with real damage), authored for this repository.

Failure modes follow the damage recorded in the bearing fact sheets of the KAt-DataCenter (one PDF per
bearing), not the folder codes alone: KI04 and KI14 carry inner-ring pitting AND outer-ring indentations
("multiple damage"), although their code names only the inner ring. Symptoms follow rolling-bearing
kinematics; every assumption is listed in ASSUMPTIONS and travels with the exported knowledge base.

Evidence levels (cumulative), ordered by what a drive-integrated monitor gets first:
  L1 drive current, overall          the converter already measures the phase currents
  L2 current at defect frequencies   sidebands f_supply +- f_defect (motor current signature analysis)
  L3 vibration, overall              an accelerometer on the bearing housing: impulsiveness
  L4 vibration envelope spectrum     lines at BPFO / BPFI and shaft-rate sidebands of BPFI
  L5 raceway inspection              the damage geometry recorded in the fact sheet
"""
from __future__ import annotations

ASSUMPTIONS = {
    "P1": "The outer ring is stationary and the inner ring turns with the shaft under a fixed radial load, so an "
          "outer-ring defect repeats at BPFO and an inner-ring defect at BPFI, amplitude-modulated at the shaft "
          "rate as it passes through the load zone.",
    "P2": "A raceway defect modulates the motor's air gap and load torque at the defect frequency, which in "
          "theory shows as sidebands f_supply +- f_defect in the phase currents.",
    "P3": "Defect frequencies follow from the fact-sheet geometry: 8 balls of 6.75 mm, pitch circle 28.55 mm "
          "(FAG) or 29.05 mm (other makers), contact angle 0.",
    "P4": "Single pitting, repetitive pitting and particle indentations on the same ring excite the same defect "
          "frequency; only an inspection of the raceway (the fact sheet) tells them apart.",
    "P5": "KI04 and KI14 have inner-ring pitting and outer-ring indentations (fact sheets, damage combination M).",
}

LEVELS = [
    {"id": "L1", "label": "Drive current", "adds": "any change of the phase-current signal",
     "rows": ["current:changed"]},
    {"id": "L2", "label": "+ current sidebands", "adds": "sidebands at f_supply +- BPFO / BPFI",
     "rows": ["current:BPFO_sidebands", "current:BPFI_sidebands"]},
    {"id": "L3", "label": "+ vibration", "adds": "impulsive vibration at the bearing housing",
     "rows": ["vibration:impulsive"]},
    {"id": "L4", "label": "+ envelope spectrum", "adds": "envelope lines at BPFO, BPFI and shaft-rate sidebands of BPFI",
     "rows": ["envelope:BPFO", "envelope:BPFI", "envelope:BPFI_shaft_sidebands"]},
    {"id": "L5", "label": "+ raceway inspection", "adds": "damage geometry from the fact sheet",
     "rows": ["raceway:single_pit", "raceway:repetitive_pits", "raceway:indentations"]},
]
for _lv in LEVELS:
    _lv["read_by_deployed_score"] = None

# mode -> (name, rings with damage, raceway geometry, assumptions)
MODES = {
    "healthy": ("Healthy bearing", set(), set(), []),
    "OR_pitting": ("Outer-ring fatigue pitting (single)", {"OR"}, {"single_pit"}, ["P1", "P2", "P3"]),
    "OR_pitting_repetitive": ("Outer-ring fatigue pitting (repetitive)", {"OR"}, {"repetitive_pits"}, ["P1", "P2", "P3", "P4"]),
    "OR_indentation": ("Outer-ring particle indentations", {"OR"}, {"indentations"}, ["P1", "P2", "P3", "P4"]),
    "IR_pitting": ("Inner-ring fatigue pitting", {"IR"}, {"single_pit"}, ["P1", "P2", "P3"]),
    "IR_pitting+OR_indentation": ("Inner-ring pitting with outer-ring indentations", {"IR", "OR"},
                                  {"single_pit", "indentations"}, ["P1", "P2", "P3", "P5"]),
}

# bearing -> (folder class, fact-sheet mode, manufacturer, damage summary from the fact sheet)
BEARINGS = {
    "K001": ("healthy", "healthy", "IBU", "run-in > 50 h at 1000-3000 N, 1500-2000 rpm"),
    "K002": ("healthy", "healthy", "IBU", "run-in 19 h at 3000 N, 2900 rpm"),
    "K003": ("healthy", "healthy", "IBU", "run-in 1 h at 3000 N, 3000 rpm"),
    "K004": ("healthy", "healthy", "IBU", "run-in 5 h at 3000 N, 3000 rpm"),
    "KA04": ("OR", "OR_pitting", "FAG", "fatigue pitting, single, 2 x 3 mm, lifetime test 12:01 h"),
    "KA15": ("OR", "OR_indentation", "FAG", "plastic deformation by particles, single, < 1 x < 1 mm, lifetime test 6:01 h"),
    "KA16": ("OR", "OR_pitting_repetitive", "MTK", "fatigue pitting, two repetitive random pits (2 and 3 mm long), lifetime test 9:01 h"),
    "KA22": ("OR", "OR_pitting", "IBU/IBB", "fatigue pitting, single, < 2 x 1 mm, lifetime test 14:01 h"),
    "KI04": ("IR", "IR_pitting+OR_indentation", "MTK", "IR fatigue pitting 2 x 1 mm plus OR plastic deformation (multiple damage), lifetime test 12:01 h"),
    "KI14": ("IR", "IR_pitting+OR_indentation", "MTK", "IR fatigue pitting 1 x 1 mm plus OR plastic deformation 1 x 1 mm (multiple damage), lifetime test 21:01 h"),
    "KI16": ("IR", "IR_pitting", "FAG", "IR fatigue pitting, single, 6 mm long across the raceway, lifetime test 3:01 h"),
    "KI18": ("IR", "IR_pitting", "MTK", "IR fatigue pitting, single, 2.5 mm long across the raceway, lifetime test 7:01 h"),
}

# which measured features (data/paderborn/evidence/features_z.csv) speak to which symptom row
EVIDENCE_MAP = {
    "current:changed": ["cur1_rms", "cur2_rms"],
    "current:BPFO_sidebands": ["cur_BPFO_sb_dB"],
    "current:BPFI_sidebands": ["cur_BPFI_sb_dB"],
    "vibration:impulsive": ["vib_kurtosis", "vib_crest", "vib_rms"],
    "envelope:BPFO": ["env_BPFO_dB", "env_BPFO2_dB"],
    "envelope:BPFI": ["env_BPFI_dB", "env_BPFI2_dB"],
    "envelope:BPFI_shaft_sidebands": ["env_BPFI-fr_dB", "env_BPFI+fr_dB"],
    "raceway:single_pit": [], "raceway:repetitive_pits": [], "raceway:indentations": [],
}


def column(mode: str, level: str) -> list[int]:
    _, rings, geometry, _ = MODES[mode]
    damaged = bool(rings)
    if level == "L1":
        return [int(damaged)]
    if level == "L2":
        return [int("OR" in rings), int("IR" in rings)]
    if level == "L3":
        return [int(damaged)]
    if level == "L4":
        return [int("OR" in rings), int("IR" in rings), int("IR" in rings)]
    return [int(g in geometry) for g in ("single_pit", "repetitive_pits", "indentations")]
