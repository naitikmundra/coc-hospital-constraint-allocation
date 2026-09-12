"""
HC-03 judging metrics, computed exactly per the problem statement.

    U_wait        = 1 - [ sum_i w_i * min(wait_i, 240) ] / [ 240 * sum_i w_i ]
    U_critical    = 1 - [ sum_{i: acuity=3} min(wait_i, 240) ] / [ 240 * N_critical ]
                    (= 1 if no critical patients in the scenario)
    U_reject      = 1 - N_rejected / N_total
    U_specialized = 1 - N_avoidable_specialized / N_admitted
                    (= 1 if no patient admitted)

All clipped to [0, 1]. Final score = 45*U_wait + 20*U_critical + 15*U_reject
+ 15*U_specialized (+ 5 pts runtime/reproducibility, assessed separately).
"""

from typing import List, Dict
from config import Patient, WAIT_WEIGHT, REJECT_AFTER_MINUTES


def _clip01(x: float) -> float:
    return max(0.0, min(1.0, x))


def compute_metrics(patients: List[Patient], n_total: int = None, decision_log=None) -> Dict:
    n_total = n_total if n_total is not None else len(patients)

    resolved = [p for p in patients if p.status in ("admitted", "rejected")]
    assert len(resolved) == n_total, (
        f"Every patient must be resolved (admitted or rejected) by end of run: "
        f"{len(resolved)} != {n_total}"
    )

    # ---- U_wait ---------------------------------------------------
    num = 0.0
    den = 0.0
    for p in resolved:
        w = WAIT_WEIGHT[p.acuity]
        wait = min(p.wait_time, REJECT_AFTER_MINUTES)
        num += w * wait
        den += w
    u_wait = 1.0 - (num / den if den > 0 else 0.0) / REJECT_AFTER_MINUTES
    u_wait = _clip01(u_wait)

    # ---- U_critical -------------------------------------------------
    critical_patients = [p for p in resolved if p.acuity == 3]
    n_critical = len(critical_patients)
    if n_critical == 0:
        u_critical = 1.0
    else:
        csum = sum(min(p.wait_time, REJECT_AFTER_MINUTES) for p in critical_patients)
        u_critical = 1.0 - csum / (REJECT_AFTER_MINUTES * n_critical)
        u_critical = _clip01(u_critical)

    # ---- U_reject -----------------------------------------------------
    n_rejected = sum(1 for p in resolved if p.status == "rejected")
    u_reject = _clip01(1.0 - n_rejected / n_total)

    # ---- U_specialized --------------------------------------------------
    admitted = [p for p in resolved if p.status == "admitted"]
    n_admitted = len(admitted)
    if decision_log is not None:
        n_avoidable = sum(
            1 for row in decision_log
            if row["decision"] == "admit" and row.get("avoidable_specialized")
        )
    else:
        n_avoidable = 0
    if n_admitted == 0:
        u_specialized = 1.0
    else:
        u_specialized = _clip01(1.0 - n_avoidable / n_admitted)

    score = 45 * u_wait + 20 * u_critical + 15 * u_reject + 15 * u_specialized

    return {
        "n_total": n_total,
        "n_admitted": n_admitted,
        "n_rejected": n_rejected,
        "n_critical": n_critical,
        "n_avoidable_specialized": n_avoidable,
        "U_wait": u_wait,
        "U_critical": u_critical,
        "U_reject": u_reject,
        "U_specialized": u_specialized,
        "score_excl_runtime": score,
        "score_max_excl_runtime": 95,
    }