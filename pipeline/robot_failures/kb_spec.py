"""Knowledge base for the UCI Robot Execution Failures data, authored for this repository.

The dataset gives only class names per learning problem (LP1-LP5) and the wrist force/torque
signals after failure detection. The symptom model below is our reading of those class names
with elementary contact mechanics; every assumption it rests on is listed in ASSUMPTIONS and
travels with the exported knowledge base. It is a structural model: it says which symptoms a
failure can switch on, never how large they are.

Evidence levels (cumulative):
  L1 task context    which motion the robot was executing (known from the robot program)
  L2 load change     any deviation of force/torque from the normal profile of that motion
  L3 force axis      the task-frame axis of the force change (front-back, left-right, vertical)
  L4 force sense     which side the contact pushes from, or whether the payload got lighter
  L5 moment pattern  where the contact is (tool vs carried part) or a payload moment shift,
                     read from the torque-to-force ratio at the wrist sensor
  L6 time course     transient (impact, then decay) vs sustained (blocked motion, static change)
"""
from __future__ import annotations

PROBLEMS = {
    "LP1": "failures in approach to grasp position",
    "LP2": "failures in transfer of a part",
    "LP3": "position of part after a transfer failure",
    "LP4": "failures in approach to ungrasp position",
    "LP5": "failures in motion with part",
}
NORMAL_LABEL = {"LP1": "normal", "LP2": "normal", "LP3": "ok", "LP4": "normal", "LP5": "normal"}

ASSUMPTIONS = {
    "A1": "Approach motions (LP1, LP4) end with a vertical descent, so a blocked approach (obstruction) "
          "loads the wrist from below.",
    "A2": "No part is held while approaching the grasp position (LP1); a part is held in LP2-LP5.",
    "A3": "A class named only 'collision' does not fix the side of contact: any side is possible, "
          "including the side of a more specific class of the same problem.",
    "A4": "Contact on the carried part acts at a longer moment arm from the wrist sensor than contact "
          "on the tool, so the torque-to-force ratio tells the two apart.",
    "A5": "'moved' and 'slightly_moved' (LP3) describe the same physical change, a shift of the part in "
          "the gripper, at different magnitudes.",
    "A6": "Collisions are impacts (force rises, then decays within the window); obstructions block the "
          "motion (force persists or grows); a changed payload is a static change.",
}

SIDES = ("front", "back", "left", "right", "below", "above")
LEVELS = [
    {"id": "L1", "label": "Task context", "adds": "which motion the robot was executing",
     "rows": [f"task:{p}" for p in PROBLEMS]},
    {"id": "L2", "label": "+ load change", "adds": "any deviation from the normal force/torque profile",
     "rows": ["load_change"]},
    {"id": "L3", "label": "+ force axis", "adds": "task-frame axis of the force change",
     "rows": ["axis:front_back", "axis:left_right", "axis:vertical"]},
    {"id": "L4", "label": "+ force sense", "adds": "side the contact pushes from, or a lighter payload",
     "rows": [f"push_from:{s}" for s in SIDES] + ["payload:lighter"]},
    {"id": "L5", "label": "+ moment pattern", "adds": "contact on the tool or on the part, or a payload moment shift",
     "rows": ["contact:tool", "contact:part", "moment:payload_shift"]},
    {"id": "L6", "label": "+ time course", "adds": "transient impact vs sustained change",
     "rows": ["time:transient", "time:sustained"]},
]
for _lv in LEVELS:
    _lv["read_by_deployed_score"] = None   # no deployed diagnoser for this dataset

ANY = set(SIDES)
AXIS_OF = {"front": "front_back", "back": "front_back", "left": "left_right", "right": "left_right",
           "below": "vertical", "above": "vertical"}

# mode id -> (problem, dataset label, name, kind, sides pushed from / payload, contact location, time course, assumptions)
#   kind: "normal" | "contact" | "payload"
MODES = {
    "LP1/normal":             ("LP1", "normal", "Normal approach to grasp", "normal", set(), set(), None, []),
    "LP1/collision":          ("LP1", "collision", "Collision during approach (side unspecified)", "contact", ANY, {"tool"}, "transient", ["A2", "A3", "A6"]),
    "LP1/front_collision":    ("LP1", "fr_collision", "Front collision during approach", "contact", {"front"}, {"tool"}, "transient", ["A2", "A6"]),
    "LP1/obstruction":        ("LP1", "obstruction", "Obstruction of the approach", "contact", {"below"}, {"tool"}, "sustained", ["A1", "A2", "A6"]),
    "LP2/normal":             ("LP2", "normal", "Normal transfer", "normal", set(), set(), None, []),
    "LP2/front_collision":    ("LP2", "front_col", "Front collision during transfer", "contact", {"front"}, {"tool", "part"}, "transient", ["A2", "A6"]),
    "LP2/back_collision":     ("LP2", "back_col", "Back collision during transfer", "contact", {"back"}, {"tool", "part"}, "transient", ["A2", "A6"]),
    "LP2/left_collision":     ("LP2", "left_col", "Collision on the left during transfer", "contact", {"left"}, {"tool", "part"}, "transient", ["A2", "A6"]),
    "LP2/right_collision":    ("LP2", "right_col", "Collision on the right during transfer", "contact", {"right"}, {"tool", "part"}, "transient", ["A2", "A6"]),
    "LP3/ok":                 ("LP3", "ok", "Part still held correctly", "normal", set(), set(), None, []),
    "LP3/slightly_moved":     ("LP3", "slightly_moved", "Part slightly moved in the gripper", "payload", set(), {"shift"}, "sustained", ["A5", "A6"]),
    "LP3/moved":              ("LP3", "moved", "Part moved in the gripper", "payload", set(), {"shift"}, "sustained", ["A5", "A6"]),
    "LP3/lost":               ("LP3", "lost", "Part lost", "payload", {"lighter"}, {"shift"}, "sustained", ["A6"]),
    "LP4/normal":             ("LP4", "normal", "Normal approach to ungrasp", "normal", set(), set(), None, []),
    "LP4/collision":          ("LP4", "collision", "Collision during approach to ungrasp (side unspecified)", "contact", ANY, {"tool", "part"}, "transient", ["A2", "A3", "A6"]),
    "LP4/obstruction":        ("LP4", "obstruction", "Obstruction of the approach to ungrasp", "contact", {"below"}, {"tool", "part"}, "sustained", ["A1", "A2", "A6"]),
    "LP5/normal":             ("LP5", "normal", "Normal motion with part", "normal", set(), set(), None, []),
    "LP5/bottom_collision":   ("LP5", "bottom_collision", "Bottom collision while moving the part", "contact", {"below"}, {"tool", "part"}, "transient", ["A2", "A6"]),
    "LP5/bottom_obstruction": ("LP5", "bottom_obstruction", "Bottom obstruction while moving the part", "contact", {"below"}, {"tool", "part"}, "sustained", ["A2", "A6"]),
    "LP5/collision_in_part":  ("LP5", "collision_in_part", "Collision on the carried part", "contact", ANY, {"part"}, "transient", ["A2", "A3", "A4", "A6"]),
    "LP5/collision_in_tool":  ("LP5", "collision_in_tool", "Collision on the tool", "contact", ANY, {"tool"}, "transient", ["A2", "A3", "A4", "A6"]),
}


def column(mode: str, level: str) -> list[int]:
    problem, _, _, kind, sides, where, course, _ = MODES[mode]
    faulty = kind != "normal"
    if level == "L1":
        return [int(p == problem) for p in PROBLEMS]
    if level == "L2":
        return [int(faulty)]
    if level == "L3":
        axes = {AXIS_OF[s] for s in sides if s in AXIS_OF}
        if "lighter" in sides:
            axes.add("vertical")   # the weight of the part disappears
        return [int(a in axes) for a in ("front_back", "left_right", "vertical")]
    if level == "L4":
        return [int(s in sides) for s in SIDES] + [int("lighter" in sides)]
    if level == "L5":
        return [int("tool" in where), int("part" in where), int("shift" in where)]
    return [int(course == "transient"), int(course == "sustained")]
