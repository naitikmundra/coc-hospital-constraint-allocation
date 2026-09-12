"""
HC-03 development run.

Runs the online BedAllocationPolicy through the local discrete-event
simulator on the development stream (NumPy PCG64, seed=20260911,
500 arrivals) and writes:

  outputs/decision_log.csv    -- one row per admission/rejection decision
  outputs/occupancy_log.csv   -- one row per occupancy-changing event
  outputs/metrics.json        -- development metrics + runtime

Usage:
    python run_dev.py [seed]

If a seed is given on the command line it overrides config.SEED, so the
same script can be pointed at unseen evaluation seeds without any code
changes (the policy code itself never changes across seeds).
"""

import csv
import json
import os
import sys
import time

from config import SEED, N_PATIENTS
from policy import BedAllocationPolicy
from simulator import HospitalSimulator
from metrics import compute_metrics

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "outputs")


def write_csv(path, rows):
    if not rows:
        with open(path, "w") as f:
            f.write("")
        return
    fieldnames = list(rows[0].keys())
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else SEED
    os.makedirs(OUT_DIR, exist_ok=True)

    policy = BedAllocationPolicy()
    sim = HospitalSimulator(policy=policy, seed=seed, n_patients=N_PATIENTS)

    t0 = time.perf_counter()
    patients, decision_log, occupancy_log = sim.run()
    elapsed = time.perf_counter() - t0

    metrics = compute_metrics(patients, n_total=N_PATIENTS, decision_log=decision_log)
    metrics["seed"] = seed
    metrics["runtime_seconds"] = elapsed

    write_csv(os.path.join(OUT_DIR, "decision_log.csv"), decision_log)
    write_csv(os.path.join(OUT_DIR, "occupancy_log.csv"), occupancy_log)
    with open(os.path.join(OUT_DIR, "metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)

    print(f"seed={seed}  n_patients={N_PATIENTS}  runtime={elapsed:.4f}s")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()