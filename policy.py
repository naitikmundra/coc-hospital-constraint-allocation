from typing import Dict, Optional
from config import Patient, REJECT_AFTER_MINUTES


class BedAllocationPolicy:
    @staticmethod
    def priority_key(patient: Patient):
        return (-patient.acuity, patient.arrival_time, patient.pid)

    def choose_bed(self, patient, free_beds, now):
        wait = max(0.0, now - patient.arrival_time)

        # L1: general only
        if patient.acuity == 1:
            if free_beds.get("general", 0) > 0:
                return "general"
            return None

        # L2: monitored first, critical only after waiting 120 min
        if patient.acuity == 2:
            if free_beds.get("monitored", 0) > 0:
                return "monitored"

            if wait >= 120 and free_beds.get("critical", 0) > 0:
                return "critical"

            return None

        # L3: critical only
        if patient.acuity == 3:
            if free_beds.get("critical", 0) > 0:
                return "critical"
            return None

        return None