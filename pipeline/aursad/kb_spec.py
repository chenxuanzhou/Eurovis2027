"""Knowledge base for AURSAD (UR3e + OnRobot screwdriver), authored for this repository.

The dataset documents how each anomaly was produced (technical report, arXiv 2102.01409) but not how it
shows in the signals. The symptom model below reads those definitions with the mechanics of a torque-
controlled screwdriving process; every assumption is listed in ASSUMPTIONS and travels with the exported
knowledge base. Entries mean "the mode can switch this symptom on".

Evidence levels (cumulative):
  L1 screwdriver torque      does the torque build up at all
  L2 seating time            when the torque rises relative to a normal rundown
  L3 wrist reaction          axial force and reaction torque the robot feels while screwing
  L4 preceding pick-up       the loosening (pick-up) sample just before the tightening
  L5 history across cycles   whether the fault recurs with a hole or with a screw
"""
from __future__ import annotations

LABEL_MODE = {0: "normal", 1: "damaged_screw", 2: "extra_component", 3: "missing_screw", 4: "damaged_plate_thread"}

ASSUMPTIONS = {
    "B1": "The screwdriver runs to a target torque (0.5 N m in the data); torque builds up only when the screw head "
          "seats, so without a screw it never builds up.",
    "B2": "An extra washer adds thickness under the head, so the screw seats after fewer turns and the torque rises "
          "earlier; the tightening otherwise completes normally.",
    "B3": "A damaged thread (filed screw, or filed/chipped hole) changes engagement and rundown friction, so seating "
          "can come earlier or later, and the screw can jam, raising the reaction torque at the wrist.",
    "B4": "Without a screw nothing engages the thread, so the axial force the robot feels while screwing is lower.",
    "B5": "Missing screws were mostly produced by skipping the pick-up (the robot waits 50 ms instead of loosening a "
          "screw), which shows in the loosening sample that precedes the tightening.",
    "B6": "A damaged screw travels with that screw while a damaged hole stays at its pin, so recurrence over cycles "
          "tells them apart. AURSAD records the pin but not the screw identity, so recurrence with a screw cannot "
          "be observed in the data.",
}

LEVELS = [
    {"id": "L1", "label": "Screwdriver torque", "adds": "whether the torque builds up",
     "rows": ["torque:not_built"]},
    {"id": "L2", "label": "+ seating time", "adds": "torque rises earlier or later than a normal rundown",
     "rows": ["seating:early", "seating:late"]},
    {"id": "L3", "label": "+ wrist reaction", "adds": "axial force and reaction torque while screwing",
     "rows": ["wrist:axial_force_low", "wrist:reaction_torque_high"]},
    {"id": "L4", "label": "+ preceding pick-up", "adds": "the loosening sample before the tightening",
     "rows": ["pickup:skipped"]},
    {"id": "L5", "label": "+ history", "adds": "recurrence of the fault at a hole or with a screw",
     "rows": ["recurs:at_hole", "recurs:with_screw"]},
]
for _lv in LEVELS:
    _lv["read_by_deployed_score"] = None

# mode -> (name, label, column per level, assumptions)
MODES = {
    "normal": ("Normal tightening", 0, {"L1": [0], "L2": [0, 0], "L3": [0, 0], "L4": [0], "L5": [0, 0]}, []),
    "missing_screw": ("Missing screw", 3, {"L1": [1], "L2": [0, 0], "L3": [1, 0], "L4": [1], "L5": [0, 0]}, ["B1", "B4", "B5"]),
    "extra_component": ("Extra assembly component (washer)", 2, {"L1": [0], "L2": [1, 0], "L3": [0, 0], "L4": [0], "L5": [0, 0]}, ["B2"]),
    "damaged_screw": ("Damaged screw thread", 1, {"L1": [0], "L2": [1, 1], "L3": [0, 1], "L4": [0], "L5": [0, 1]}, ["B3", "B6"]),
    "damaged_plate_thread": ("Damaged plate thread", 4, {"L1": [0], "L2": [1, 1], "L3": [0, 1], "L4": [0], "L5": [1, 0]}, ["B3", "B6"]),
}

# measured features (data/aursad/evidence/features_z.csv) per symptom row; sign = expected direction of z
EVIDENCE_MAP = {
    "torque:not_built": [["current_torque_max", -1], ["achieved_torque_final", -1]],
    "seating:early": [["torque_rise_s", -1]],
    "seating:late": [["torque_rise_s", 1]],
    "wrist:axial_force_low": [["fz_mean_screw", -1]],
    "wrist:reaction_torque_high": [["mz_absmax_screw", 1]],
    "pickup:skipped": [["prev_loosen_screw_s", -1], ["prev_loosen_torque_max", -1]],
    "recurs:at_hole": [],          # from the history of pin_to (see samples.csv), not from one sample
    "recurs:with_screw": [],       # not observable: screw identity is not recorded
}


def column(mode: str, level: str) -> list[int]:
    return MODES[mode][2][level]
