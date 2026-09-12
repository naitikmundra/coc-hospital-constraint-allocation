"""
HC-03: Hospital Bed Allocation Under Capacity Constraints
Shared configuration / problem constants.

These constants encode the PUBLISHED rules of the problem (arrival process,
acuity mix, capacities, compatibility, LOS distributions, waiting weights).
They are legitimately known to the online policy ahead of time -- the
problem statement explicitly allows the policy to use "the published
arrival and length-of-stay distributions". What the policy may NOT use is
any *realized* future draws (future arrivals, future LOS values, future
RNG state).
"""

from dataclasses import dataclass

# ---- Arrival process -------------------------------------------------
SEED = 20260911
N_PATIENTS = 500
MEAN_INTERARRIVAL = 2.5          # minutes, Exp(mean=2.5)
ACUITY_LEVELS = (1, 2, 3)
ACUITY_PROBS = (0.60, 0.30, 0.10)

# ---- Bed types / capacity / compatibility -----------------------------
BED_TYPES = ("general", "monitored", "critical")

CAPACITY = {
    "general": 30,
    "monitored": 10,
    "critical": 5,
}

# level -> the bed type that level "requires" in the narrowest sense
REQUIRED_TYPE = {
    1: "general",
    2: "monitored",
    3: "critical",
}

# level -> ordered list of bed types it can occupy, from LEAST to MOST
# specialized. Order matters: the policy always prefers the least
# specialized compatible bed that is free (this is what makes
# "avoidable specialized assignments" structurally impossible).
COMPATIBLE_BEDS = {
    1: ("general", "monitored", "critical"),
    2: ("monitored", "critical"),
    3: ("critical",),
}

# ---- Length of stay ----------------------------------------------------
LOS_SIGMA = 0.35
LOS_MEDIAN = {
    "general": 120.0,
    "monitored": 180.0,
    "critical": 240.0,
}

# ---- Waiting / scoring --------------------------------------------------
WAIT_WEIGHT = {1: 1.0, 2: 3.0, 3: 8.0}
REJECT_AFTER_MINUTES = 240.0


@dataclass
class Patient:
    """A single patient record, mutated in place as the simulation runs."""
    pid: int
    arrival_time: float
    acuity: int

    required_type: str = None
    status: str = "pending"        # pending -> waiting -> admitted|rejected
    admit_time: float = None
    bed_type: str = None
    los: float = None
    departure_time: float = None
    rejected_time: float = None

    def __post_init__(self):
        if self.required_type is None:
            self.required_type = REQUIRED_TYPE[self.acuity]

    @property
    def wait_time(self) -> float:
        """Time spent waiting before being admitted or rejected."""
        if self.status == "admitted":
            return self.admit_time - self.arrival_time
        if self.status == "rejected":
            return self.rejected_time - self.arrival_time
        return None