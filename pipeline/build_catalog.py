"""Write the lookup tables in data/catalog/: signals, categories, variants, actions.

Needs no raw data: everything comes from the official voraus-AD enums
(vendor/voraus_enums.py), the knowledge base (vendor/line_kg.py) and, for the
variant -> category map of the anomalous settings, the SAFEPROCESS evidence
records copied into data/evidence/ by build_evidence.py.

Run from the repository root:  python pipeline/build_catalog.py
"""
from __future__ import annotations

import json

import pandas as pd

import config as C
import attribution_bridge as AB
import line_kg as KB
from voraus_enums import Action, Category, Signals, Variant

OUT = C.DATA / "catalog"

# Paper names and groups (voraus-AD paper, Table III).
PAPER = {
    Category.AXIS_FRICTION: ("additional friction", "robot axis wear"),
    Category.AXIS_WEIGHT: ("additional axis weight", "process error"),
    Category.COLLISION_FOAM: ("collision with foam", "process error"),
    Category.COLLISION_CABLE: ("collision with cables", "process error"),
    Category.COLLISION_CARTON: ("collision with cardboard", "process error"),
    Category.MISS_CAN: ("misgrip of can", "gripping error"),
    Category.LOSE_CAN: ("losing the can", "gripping error"),
    Category.CAN_WEIGHT: ("varying can weight", "process error"),
    Category.ENTANGLED: ("cable routed at robot", "process error"),
    Category.INVALID_POSITION: ("invalid gripping position", "process error"),
    Category.MOTOR_COMMUTATION: ("miscommutation", "robot axis wear"),
    Category.WOBBLING_STATION: ("unstable platform", "process error"),
    Category.NORMAL_OPERATION: ("normal operation", "normal"),
}

# Units: the four families the knowledge base reads carry the labels used in
# attribution_bridge.JOINT_SIGNALS; every other unit is the SI unit implied by the
# signal name and is marked as inferred.
UNIT_FROM_CODE = {
    "motor_torque": "N·m", "torque_sensor_a": "N·m",
    "joint_velocity": "rad/s", "joint_position": "rad",
}
UNIT_INFERRED = {
    "target_position": "rad", "motor_position": "rad", "target_velocity": "rad/s",
    "motor_velocity": "rad/s", "target_acceleration": "rad/s²", "target_torque": "N·m",
    "computed_torque": "N·m", "torque_sensor_b": "N·m", "computed_inertia": "kg·m²",
    "motor_iq": "A", "motor_id": "A", "motor_voltage": "V", "supply_voltage": "V",
    "brake_voltage": "V", "power_motor_el": "W", "power_motor_mech": "W",
    "power_load_mech": "W", "robot_voltage": "V", "robot_current": "A",
    "io_current": "A", "system_current": "A",
}


def split_name(name: str) -> tuple[str, int | None]:
    head, _, tail = name.rpartition("_")
    if tail.isdigit() and head:
        return head, int(tail)
    return name, None


def signals_table() -> pd.DataFrame:
    measured, electrical = set(Signals.measured()), set(Signals.electrical())
    kb_families = set(KB.SIGNAL_FAMILIES)
    rows = []
    for order, name in enumerate(Signals.machine()):
        family, joint = split_name(name)
        if family in UNIT_FROM_CODE:
            unit, unit_source = UNIT_FROM_CODE[family], "attribution_bridge label"
        else:
            unit, unit_source = UNIT_INFERRED.get(family, ""), "inferred from name"
        rows.append({
            "column_order": order,
            "name": name,
            "family": family,
            "joint": joint,
            "level": "joint" if joint else "robot",
            "source": "measured" if name in measured else "computed",
            "domain": "electrical" if name in electrical else "mechanical",
            "read_by_kb": family in kb_families,
            "in_grid500": name in set(C.grid_channels()),
            "unit": unit,
            "unit_source": unit_source,
        })
    df = pd.DataFrame(rows)
    df["joint"] = df["joint"].astype("Int64")
    return df


def categories_table() -> pd.DataFrame:
    fm_of_cat = {fm["voraus_category"]: fm for fm in KB.FMEA if fm["voraus_category"] is not None}
    rows = []
    for cat in Category:
        name, group = PAPER[cat]
        fm = fm_of_cat.get(int(cat))
        rows.append({
            "category": int(cat), "enum_name": cat.name, "paper_name": name,
            "paper_group": group, "anomaly": cat != Category.NORMAL_OPERATION,
            "kb_mode": fm["id"] if fm else None,
            "kb_mode_name": fm["name"] if fm else None,
            "kb_group": fm["group"] if fm else None,
        })
    return pd.DataFrame(rows)


def variants_table() -> pd.DataFrame:
    cat_of_setting = {}
    records = C.DATA / "evidence" / "records_anomalous.json"
    if records.exists():
        for rec in json.loads(records.read_text(encoding="utf-8")):
            d = rec["detector"]
            cat_of_setting[d["ground_truth_setting"]] = d["ground_truth_category"]
    normal = {Variant.PRE_A, Variant.PRE_B, Variant.BETWEEN_A, Variant.BETWEEN_B, Variant.BETWEEN_C}
    rows = []
    for var in Variant:
        cat = int(Category.NORMAL_OPERATION) if var in normal else cat_of_setting.get(int(var))
        rows.append({
            "setting": int(var), "enum_name": var.name,
            "category": cat,
            "official_split": "train" if int(var) == C.TRAIN_SETTING else "test",
        })
    df = pd.DataFrame(rows)
    df["category"] = df["category"].astype("Int64")
    return df


def actions_table() -> pd.DataFrame:
    rows = []
    for act in Action:
        motion = "VOID" if act.name.startswith("VOID") else act.name.rsplit("_", 1)[-1]
        rows.append({
            "action": int(act), "enum_name": act.name, "motion": motion,
            "phase_class": KB.PHASE_OF_ACTION.get(act.name),
            "can_carried": int(act) in AB.CARRY_ACTIONS,
        })
    return pd.DataFrame(rows)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    tables = {
        "signals.csv": signals_table(),
        "categories.csv": categories_table(),
        "variants.csv": variants_table(),
        "actions.csv": actions_table(),
    }
    for name, df in tables.items():
        df.to_csv(OUT / name, index=False, encoding="utf-8")
        print(f"{name:16s} {len(df):4d} rows")


if __name__ == "__main__":
    main()
