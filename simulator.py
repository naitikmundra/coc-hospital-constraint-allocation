"""
HC-03 local discrete-event simulator.

Generates the development arrival stream with NumPy PCG64(seed=20260911):
  - 500 arrivals, inter-arrival ~ Exponential(mean=2.5 minutes)
  - acuity in {1,2,3} with P = (0.60, 0.30, 0.10)
Runs those arrivals through an online BedAllocationPolicy under the
event rules of the problem:
  - a bed's length-of-stay is drawn ONLY at the moment of admission
    (never known in advance to the policy or to the simulator before
    that point),
  - a patient still waiting 240 minutes after arrival is rejected,
  - an admitted patient can never be evicted.

The simulator is the only component allowed to see "future" information
(it owns the RNG and the event queue); the policy object only ever
receives `free_beds` (current state) and the `patient` under
consideration (whose only known attributes at decision time are its own
id, arrival_time and acuity -- exactly what "arrival" reveals).
"""

import heapq
import itertools
from typing import List, Tuple

import numpy as np

from config import (
    Patient,
    SEED,
    N_PATIENTS,
    MEAN_INTERARRIVAL,
    ACUITY_LEVELS,
    ACUITY_PROBS,
    CAPACITY,
    BED_TYPES,
    LOS_SIGMA,
    LOS_MEDIAN,
    REJECT_AFTER_MINUTES,
    COMPATIBLE_BEDS,
)
from policy import BedAllocationPolicy

# Event type tags
EV_ARRIVAL = 0
EV_DEPARTURE = 1
EV_REJECT_CHECK = 2


class HospitalSimulator:
    def __init__(
        self,
        policy: BedAllocationPolicy,
        seed: int = SEED,
        n_patients: int = N_PATIENTS,
        mean_interarrival: float = MEAN_INTERARRIVAL,
        acuity_levels: Tuple[int, ...] = ACUITY_LEVELS,
        acuity_probs: Tuple[float, ...] = ACUITY_PROBS,
        capacity: dict = None,
    ):
        self.policy = policy
        self.seed = seed
        self.n_patients = n_patients
        self.mean_interarrival = mean_interarrival
        self.acuity_levels = acuity_levels
        self.acuity_probs = acuity_probs
        self.capacity = dict(capacity) if capacity else dict(CAPACITY)

        self.rng = np.random.Generator(np.random.PCG64(self.seed))

        self.patients: List[Patient] = []
        self.free_beds = dict(self.capacity)
        self.occupied = {bt: set() for bt in BED_TYPES}
        self.waiting: List[Patient] = []
        self.lvl3_reject = 0
        self.lvl2_reject = 0
        self.lvl1_reject = 0

        self.decision_log = []     # admissions + rejections
        self.occupancy_log = []    # a row every time free-bed counts change

        self._event_seq = itertools.count()
        self._events = []          # heap of (time, seq, type, payload)

    # -------------------------------------------------------------
    def _generate_arrivals(self):
        """Pre-generate the arrival stream (times + acuities) with the
        development RNG. This is legitimate simulator-side state -- the
        policy never sees a patient's acuity or arrival time before that
        patient's arrival event actually fires."""
        interarrivals = self.rng.exponential(
            self.mean_interarrival, size=self.n_patients
        )
        arrival_times = np.cumsum(interarrivals)
        acuities = self.rng.choice(
            self.acuity_levels, size=self.n_patients, p=self.acuity_probs
        )
        for i in range(self.n_patients):
            p = Patient(pid=i, arrival_time=float(arrival_times[i]), acuity=int(acuities[i]))
            self.patients.append(p)
            heapq.heappush(
                self._events, (p.arrival_time, next(self._event_seq), EV_ARRIVAL, p.pid)
            )

    def _draw_los(self, bed_type: str) -> float:
        """Draw a realized length of stay for a NEWLY admitted patient.
        Only called at the instant of admission -- this is what makes the
        realized LOS invisible to the policy in advance."""
        median = LOS_MEDIAN[bed_type]
        mu = np.log(median)
        return float(self.rng.lognormal(mean=mu, sigma=LOS_SIGMA))

    def _log_occupancy(self, now: float, event: str, patient):
        row = {
            "time": now,
            "event": event,
            "patient_id": patient.pid,
            "patient_type": patient.acuity,
            "free_general": self.free_beds["general"],
            "free_monitored": self.free_beds["monitored"],
            "free_critical": self.free_beds["critical"],
            "occ_general": self.capacity["general"] - self.free_beds["general"],
            "occ_monitored": self.capacity["monitored"] - self.free_beds["monitored"],
            "occ_critical": self.capacity["critical"] - self.free_beds["critical"],
            "n_waiting": len(self.waiting),
        }
        self.occupancy_log.append(row)

    # -------------------------------------------------------------
    def _try_admit(self, now: float):
        """Scan the waiting queue in priority order and admit whoever the
        policy is willing to place, given the CURRENT free-bed counts.
        Re-scans after each admission since state changes."""
        progressed = True
        while progressed:
            progressed = False
            self.waiting.sort(key=self.policy.priority_key)
            for patient in list(self.waiting):
                free_before = dict(self.free_beds)
                bed_type = self.policy.choose_bed(patient, self.free_beds, now)
                if bed_type is None:
                    continue
                # sanity: never assign a bed type not compatible / not free
                if self.free_beds.get(bed_type, 0) <= 0:
                    continue
                self._admit(patient, bed_type, now, free_before)
                progressed = True
                break  # restart scan from highest priority w/ updated state

    def _admit(self, patient: Patient, bed_type: str, now: float, free_before: dict):
        self.free_beds[bed_type] -= 1
        self.occupied[bed_type].add(patient.pid)
        self.waiting.remove(patient)

        patient.status = "admitted"
        patient.admit_time = now
        patient.bed_type = bed_type
        los = self._draw_los(bed_type)
        patient.los = los
        patient.departure_time = now + los

        heapq.heappush(
            self._events,
            (patient.departure_time, next(self._event_seq), EV_DEPARTURE, patient.pid),
        )

        # was a less-specialized compatible bed free at decision time?
        required_order = COMPATIBLE_BEDS[patient.acuity]
        avoidable = False
        for bt in required_order:
            if bt == bed_type:
                break
            if free_before.get(bt, 0) > 0:
                avoidable = True
                break

        self.decision_log.append(
            {
                "patient_id": patient.pid,
                "arrival_time": patient.arrival_time,
                "acuity": patient.acuity,
                "decision": "admit",
                "decision_time": now,
                "bed_type": bed_type,
                "wait_time": now - patient.arrival_time,
                "los": los,
                "departure_time": patient.departure_time,
                "free_general_before": free_before["general"],
                "free_monitored_before": free_before["monitored"],
                "free_critical_before": free_before["critical"],
                "avoidable_specialized": avoidable,
            }
        )
        self._log_occupancy(now, "admit", patient)

    def _reject(self, patient: Patient, now: float):
        if patient not in self.waiting:
            return

        self.waiting.remove(patient)
        patient.status = "rejected"
        patient.rejected_time = now

        if patient.acuity == 1:
            self.lvl1_reject += 1
        elif patient.acuity == 2:
            self.lvl2_reject += 1
        elif patient.acuity == 3:
            self.lvl3_reject += 1

        self.decision_log.append(
            {
                "patient_id": patient.pid,
                "arrival_time": patient.arrival_time,
                "acuity": patient.acuity,
                "decision": "reject",
                "decision_time": now,
                "bed_type": None,
                "wait_time": now - patient.arrival_time,
                "los": None,
                "departure_time": None,
                "free_general_before": self.free_beds["general"],
                "free_monitored_before": self.free_beds["monitored"],
                "free_critical_before": self.free_beds["critical"],
                "avoidable_specialized": False,
            }
        )

        self._log_occupancy(now, "reject", patient)

    # -------------------------------------------------------------
    def run(self):
        self._generate_arrivals()

        while self._events:
            now, _, etype, pid = heapq.heappop(self._events)
            patient = self.patients[pid]

            if etype == EV_ARRIVAL:
                patient.status = "waiting"
                self.waiting.append(patient)
                heapq.heappush(
                    self._events,
                    (
                        patient.arrival_time + REJECT_AFTER_MINUTES,
                        next(self._event_seq),
                        EV_REJECT_CHECK,
                        pid,
                    ),
                )
                self._try_admit(now)

            elif etype == EV_DEPARTURE:
                bed_type = patient.bed_type
                self.free_beds[bed_type] += 1
                self.occupied[bed_type].discard(pid)
                self._log_occupancy(now, "departure", patient)
                self._try_admit(now)

            elif etype == EV_REJECT_CHECK:
                if patient.status == "waiting":
                    self._try_admit(now)
                    if patient.status == "waiting":
                        self._reject(patient, now)
        print("L1 rejected:", self.lvl1_reject)
        print("L2 rejected:", self.lvl2_reject)
        print("L3 rejected:", self.lvl3_reject)
        total_wait_by_level = {
            1: 0.0,
            2: 0.0,
            3: 0.0,
        }

        for decision in self.decision_log:
            total_wait_by_level[decision["acuity"]] += decision["wait_time"]

        print("L1 total waiting time:", total_wait_by_level[1])
        print("L2 total waiting time:", total_wait_by_level[2])
        print("L3 total waiting time:", total_wait_by_level[3])        
        return self.patients, self.decision_log, self.occupancy_log