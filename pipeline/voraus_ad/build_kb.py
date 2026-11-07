"""Export the FMEA knowledge base as the structural layer of the visual analytics system.

Outputs (data/voraus_ad/kb/)
  failure_modes.json      the 14 failure modes with scope, manifest families, phase hint,
                          authored physical signature and the voraus-AD category they map to
  fsm_deployed.csv        fault signature matrix of the representation the deployed score
                          reads: rows = symptom slots (family x joint, robot-level families),
                          columns = failure modes
  refinement_lattice.json the isolability refinement chain L0 -> L4: at each evidence level the
                          partition of the modes into structurally identical blocks, the parent
                          block of every block, the directed isolability relation and the nested
                          (one-way) pairs; drives the refinement diagram of topic 1
  twin_groups.json        the four twin groups of the deployed representation with what would
                          separate them (resolution kind, hint text, certificate result)
  certificates.json       certificate results of the SAFEPROCESS study (copied, with source)

Isolability follows structural FDI: mode i is isolable from mode j at a level when some
symptom row is 1 for i and 0 for j. Equal columns = twins (neither isolable from the
other); a strictly nested column = isolable in one direction only.

Run from the repository root:  python pipeline/build_kb.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter

import pandas as pd

import config as C  # noqa: I001  (puts pipeline/ and vendor/ on sys.path)
import line_kg as KB
from common.lattice import refinement_lattice

OUT = C.DATA / "kb"
JOINT_FAMILIES = ("motor_torque", "torque_sensor_a", "joint_velocity", "joint_position")
ROBOT_FAMILIES = ("robot_current", "system_current")
PHASES = ("pick", "place", "transfer")
TEMPORAL = ("sustained", "drop", "rise", "transient")

# English gloss of distinguishability.TWIN_HINT (the original Chinese text is kept as well)
TWIN_HINT = {
    frozenset({"FM_losecan", "FM_axisweight", "FM_varweight"}): (
        "扭矩偏差方向与跨周期一致性（掉件=骤降 / 加重=持续升高 / 变重=逐件不同）——需产线负载配置或人工判定",
        "Direction and cycle-to-cycle consistency of the torque deviation (lost can = sudden drop, "
        "added weight = sustained rise, varying weight = differs between cycles); needs the line's "
        "payload configuration or a human check.",
        "learned certificate"),
    frozenset({"FM_collision_foam", "FM_collision_card"}): (
        "接触物材质（泡沫 vs 纸板）——信号无法区分，需现场目视/视频",
        "Material of the contacted object (foam vs cardboard); the signals cannot separate them, "
        "needs an on-site look or video.",
        "inspection"),
    frozenset({"FM_misgrip", "FM_invalidgrip"}): (
        "抓取失败模式（漏抓 vs 示教点位置错）——需抓取位姿复核",
        "How the grip failed (missed can vs wrong taught position); needs a check of the grip pose.",
        "inspection"),
    frozenset({"FM_miscommutation", "FM_overtemp"}): (
        "电气 vs 热因——本机无温度传感器，属传感器缺口",
        "Electrical vs thermal cause; the cell has no temperature sensor, so this is a sensor gap.",
        "sensor gap"),
}

LEVELS = [
    ("L1", "Joint scope", "which joints the mode can affect", True),
    ("L2", "+ signal families", "which signal families the deviation shows in (deployed representation)", True),
    ("L3", "+ phase hint", "in which task phases the mode is expected (deployed score, phase term)", True),
    ("L4", "+ physical signature", "authored torque direction and time course (not read by the deployed score)", False),
]


def rows_for_level(level: str) -> list[str]:
    if level == "L1":
        return [f"joint:{j}" for j in C.JOINTS]
    if level == "L2":
        return [f"{fam}@J{j}" for fam in JOINT_FAMILIES for j in C.JOINTS] + list(ROBOT_FAMILIES)
    if level == "L3":
        return [f"phase:{p}" for p in PHASES]
    return ["direction:up", "direction:down"] + [f"temporal:{t}" for t in TEMPORAL]


def column(fm: dict, level: str) -> list[int]:
    joints = set(KB._expand(fm["affects"]))
    fams = set(fm["manifests"])
    if level == "L1":
        return [int(j in joints) for j in C.JOINTS]
    if level == "L2":
        return ([int(fam in fams and j in joints) for fam in JOINT_FAMILIES for j in C.JOINTS]
                + [int(fam in fams) for fam in ROBOT_FAMILIES])
    if level == "L3":
        ok = KB.HINT_PHASE_CLASSES.get(fm["phase_hint"], set()) - {None}
        return [int(p in ok) for p in PHASES]
    sig = KB.FM_SIGNATURE.get(fm["id"], {})
    d, t = sig.get("direction", 0), sig.get("temporal")
    up, down = int(d in (1, 0)), int(d in (-1, 0))
    return [up, down] + [int(t is None or t == x) for x in TEMPORAL]


def failure_modes() -> list[dict]:
    out = []
    for fm in KB.FMEA:
        sig = KB.FM_SIGNATURE.get(fm["id"], {})
        out.append({
            "id": fm["id"], "name": fm["name"], "group": fm["group"],
            "affects": fm["affects"], "joints": sorted(KB._expand(fm["affects"])),
            "manifests": list(fm["manifests"]), "phase_hint": fm["phase_hint"],
            "phase_classes": sorted(p for p in KB.HINT_PHASE_CLASSES.get(fm["phase_hint"], set()) if p),
            "signature": {"direction": sig.get("direction"), "temporal": sig.get("temporal")},
            "voraus_category": fm["voraus_category"],
            "in_dataset": fm["voraus_category"] is not None,
            "cause": fm["cause"], "effect": fm["effect"], "recommendation": fm["recommendation"],
        })
    return out


def lattice(modes: list[dict], cycles_per_mode: Counter) -> dict:
    fm_of = {fm["id"]: fm for fm in KB.FMEA}
    levels = [{"id": lid, "label": label, "adds": adds, "read_by_deployed_score": deployed,
               "rows": rows_for_level(lid)} for lid, label, adds, deployed in LEVELS]
    columns = {lid: {m["id"]: column(fm_of[m["id"]], lid) for m in modes} for lid, *_ in LEVELS}
    return refinement_lattice(
        "voraus_ad", levels, columns, dict(cycles_per_mode),
        description="Isolability refinement chain of the FMEA knowledge base of the SAFEPROCESS 2027 study. "
                    "Each level adds evidence rows to the fault signature matrix; blocks are modes with "
                    "identical cumulative columns (structural twins at that level). The no-fault hypothesis "
                    "is not part of the problem: diagnosis starts from a detected anomaly.",
        mode_label={m["id"]: fm_of[m["id"]]["voraus_category"] for m in modes})


def fsm_deployed(modes: list[dict]) -> pd.DataFrame:
    fm_of = {fm["id"]: fm for fm in KB.FMEA}
    rows = rows_for_level("L2")
    data = {m["id"]: column(fm_of[m["id"]], "L2") for m in modes}
    df = pd.DataFrame(data, index=rows)
    df.index.name = "symptom"
    return df


def certificates() -> dict:
    src = C.SNIS_REPO / "results" / "repair_results.json"
    r = json.loads(src.read_text(encoding="utf-8"))
    return {
        "source": {"repository": "chenxuanzhou/Structural-Non-Isolability-in-Knowledge-Based-Robot-Fault-Diagnosis",
                   "commit": C.SNIS_COMMIT, "file": "results/repair_results.json"},
        "protocol": "five leave-setting-out splits (data/voraus_ad/splits/leave_setting_out.json)",
        "certificates": r["certificates"],
        "untestable": r["untestable"],
        "leave_setting_out_vs_random": r["leakage_check"]["per_cluster"],
        "label_efficiency": r["label_efficiency"],
        "flat_classifier_control": r["control_flat_classifier"],
    }


def twin_groups(lat: dict, certs: dict) -> list[dict]:
    l2 = next(lv for lv in lat["levels"] if lv["id"] == "L2")
    fm_of = {fm["id"]: fm for fm in KB.FMEA}
    by_members = {frozenset(c["members"]): (k, c) for k, c in certs["certificates"].items()}
    untestable = {frozenset(u["members"]): u["reason"] for u in certs["untestable"]}
    out = []
    for block in l2["twin_blocks"]:
        key = frozenset(block)
        zh, en, kind = TWIN_HINT[key]
        cert_key, cert = by_members.get(key, (None, None))
        out.append({
            "members": block,
            "categories": [fm_of[i]["voraus_category"] for i in block],
            "joints": sorted(KB._expand(fm_of[block[0]]["affects"])),
            "families": sorted(fm_of[block[0]]["manifests"]),
            "phase_hints": {i: fm_of[i]["phase_hint"] for i in block},
            "resolution_kind": kind,
            "hint_zh": zh, "hint_en": en,
            "certificate": None if cert is None else {
                "key": cert_key, "adopted": cert.get("adopted"),
                "verdict": cert.get("verdict") or cert.get("wall"),
                "acc_test": cert.get("acc_test"), "acc_majority": cert.get("acc_majority"),
                "acc_deployed_repr": cert.get("acc_deployed_repr"),
                "dims_selected": cert.get("dims_selected"), "cost_class": cert.get("cost_class"),
                "reason": cert.get("reason"),
            },
            "untestable_reason": untestable.get(key),
        })
    return out


def cross_check(lat: dict) -> None:
    """Compare the L2 twin blocks with distinguishability.twin_classes() of the study."""
    pipe = C.SNIS_REPO / "pipeline"
    if not pipe.exists():
        print("cross-check skipped: SAFEPROCESS repository not found")
        return
    code = ("import json,distinguishability as d;"
            "print(json.dumps(sorted(sorted(g) for g in d.twin_classes())))")
    res = subprocess.run([sys.executable, "-c", code], cwd=pipe, capture_output=True, text=True, check=True)
    theirs = json.loads(res.stdout.strip().splitlines()[-1])
    ours = sorted(sorted(b) for b in next(lv for lv in lat["levels"] if lv["id"] == "L2")["twin_blocks"])
    assert theirs == ours, (theirs, ours)
    print("cross-check: L2 twin blocks equal distinguishability.twin_classes()")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    records = json.loads((C.DATA / "evidence" / "records_anomalous.json").read_text(encoding="utf-8"))
    mode_of_cat = {fm["voraus_category"]: fm["id"] for fm in KB.FMEA if fm["voraus_category"] is not None}
    cycles_per_mode = Counter(mode_of_cat[r["detector"]["ground_truth_category"]] for r in records)

    modes = failure_modes()
    lat = lattice(modes, cycles_per_mode)
    certs = certificates()
    (OUT / "failure_modes.json").write_text(json.dumps(modes, indent=1, ensure_ascii=False), encoding="utf-8")
    fsm_deployed(modes).to_csv(OUT / "fsm_deployed.csv", encoding="utf-8")
    (OUT / "refinement_lattice.json").write_text(json.dumps(lat, indent=1), encoding="utf-8")
    (OUT / "certificates.json").write_text(json.dumps(certs, indent=1, ensure_ascii=False), encoding="utf-8")
    groups = twin_groups(lat, certs)
    (OUT / "twin_groups.json").write_text(json.dumps(groups, indent=1, ensure_ascii=False), encoding="utf-8")
    cross_check(lat)
    for lv in lat["levels"]:
        extra = f", true mode in a twin block: {lv['instances_with_true_mode_in_twin_block']}" if lv["id"] != "L0" else ""
        print(f"{lv['id']} {lv['label']:22s} blocks={len(lv['blocks']):2d}{extra}")


if __name__ == "__main__":
    main()
