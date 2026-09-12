Development Log 
##Created  Policy 1


The policy allocates patients to the least specialized compatible bed whenever the simulator checks for possible admissions.
* Level 3 patients can only use critical beds.
* Level 2 patients normally use monitored beds. If they have waited at least 120 minutes and no monitored bed is available, they may use a critical bed.
* Level 1 patients normally use general beds. If they have waited at least 120 minutes and no general bed is available, they may use a monitored or critical bed.
* Higher-acuity patients are considered first. Patients with the same acuity are considered in arrival order.
The simulator calls the allocation procedure:
* when a patient arrives;
* when an admitted patient departs and frees a bed;
* at a patient's 240-minute rejection check, immediately before deciding whether the patient must be rejected.
No future arrivals or realized lengths of stay are used by the policy.

RESULT POLICY 1:
L1 rejected: 0
L2 rejected: 68
L3 rejected: 32
seed=20260911  n_patients=500  runtime=0.0117s
{
  "n_total": 500,
  "n_admitted": 400,
  "n_rejected": 100,
  "n_critical": 63,
  "n_avoidable_specialized": 0,
  "U_wait": 0.3300898907672801,
  "U_critical": 0.14066290427801675,
  "U_reject": 0.8,
  "U_specialized": 1.0,
  "score_excl_runtime": 44.66730317008794,
  "score_max_excl_runtime": 95,
  "seed": 20260911,
  "runtime_seconds": 0.011695834000420291
}

Interestingly for this specific seed there is never a point where l2 or l1 patient can use an l3 or l2 bed regardless of waiting time eligiblity

More on this we printed whenever l1 was sent to waiting there was no point where any bed even on higher level was free:
L1 waiting | wait=20.72 min | general=0 | monitored=0 | critical=0
L1 waiting | wait=20.11 min | general=0 | monitored=0 | critical=0
L1 waiting | wait=7.02 min | general=0 | monitored=0 | critical=0
L1 waiting | wait=4.91 min | general=0 | monitored=0 | critical=0
L1 waiting | wait=3.61 min | general=0 | monitored=0 | critical=0
L1 waiting | wait=2.05 min | general=0 | monitored=0 | critical=0
…

##Created Experimental Policy 1

This policy rejects all Level 3 patients by never assigning them a bed.
* Level 1 patients use general beds.
* Level 2 patients use monitored beds first and critical beds if no monitored bed is available.
* Level 3 patients are never admitted.
* Higher-acuity patients are considered first among patients that the policy can admit.
* Patients with the same acuity are considered in arrival order.
The simulator calls the allocation procedure when:
* a patient arrives;
* an admitted patient departs and frees a bed;
* a patient's 240-minute rejection check occurs, immediately before rejection.
This policy is used as an experimental baseline to see whether sacrificing Level 3 patients allows more Level 2 patients to be admitted.

RESULTS EXP POLICY 1:
L1 rejected: 0
L2 rejected: 36
L3 rejected: 63
seed=20260911  n_patients=500  runtime=0.0101s
{
  "n_total": 500,
  "n_admitted": 401,
  "n_rejected": 99,
  "n_critical": 63,
  "n_avoidable_specialized": 0,
  "U_wait": 0.3020303578467112,
  "U_critical": 0.0,
  "U_reject": 0.802,
  "U_specialized": 1.0,
  "score_excl_runtime": 40.621366103102005,
  "score_max_excl_runtime": 95,
  "seed": 20260911,
  "runtime_seconds": 0.010053333000541897
}


###INTRESTING INFERENCE 1

Across the tested seeds, Level 1 patients experienced zero rejections when restricted to general beds. Therefore, specialized beds do not appear necessary for serving Level 1 patients in the tested workloads.


## POLICY 2 (STRICT)

Kept patients restricted to the exact bed type corresponding to their acuity:
* L1 → General only
* L2 → Monitored only
* L3 → Critical only
* No cross-allocation or fallback beds.


Results of POLICY 2:
L1 rejected: 0
L2 rejected: 68
L3 rejected: 32
seed=20260911  n_patients=500  runtime=0.0106s
{
  "n_total": 500,
  "n_admitted": 400,
  "n_rejected": 100,
  "n_critical": 63,
  "n_avoidable_specialized": 0,
  "U_wait": 0.3300898907672801,
  "U_critical": 0.14066290427801675,
  "U_reject": 0.8,
  "U_specialized": 1.0,
  "score_excl_runtime": 44.66730317008794,
  "score_max_excl_runtime": 95,
  "seed": 20260911,
  "runtime_seconds": 0.010552583000389859
}

## POLICY 3 (Reserve)

Reserving 2 beds of l3 for l2 patients made scores worse essentially marking out possibility of trading l2 rejections/waiting for l3

L1 rejected: 0
L2 rejected: 44
L3 rejected: 60
L1 total waiting time: 5236.972660352802
L2 total waiting time: 27881.539088466856
L3 total waiting time: 14400.0
seed=20260911  n_patients=500  runtime=0.0129s
{
  "n_total": 500,
  "n_admitted": 396,
  "n_rejected": 104,
  "n_critical": 63,
  "n_avoidable_specialized": 0,
  "U_wait": 0.30470976449388987,
  "U_critical": 0.04761904761904767,
  "U_reject": 0.792,
  "U_specialized": 1.0,
  "score_excl_runtime": 41.544320354606,
  "score_max_excl_runtime": 95,
  "seed": 20260911,
  "runtime_seconds": 0.012894582999706472
}

###INTRESTING INFERENCE 2

Somewhat basic inference that level3 patient logic can mathematically best best at immediate allotment if bed is free —> allot
Nothing much we can do


##Policy 4
Keeping l1 lmid to l1 beds yet for l2 giving l3 if wait time more than 120 mins (also removing acuity as priority order in queue to make it function)


Produced Results (worse):
L1 rejected: 0
L2 rejected: 55
L3 rejected: 45
L1 total waiting time: 4503.380832854788
L2 total waiting time: 29238.7704336389
L3 total waiting time: 13502.13156827731
seed=20260911  n_patients=500  runtime=0.0119s
{
  "n_total": 500,
  "n_admitted": 400,
  "n_rejected": 100,
  "n_critical": 63,
  "n_avoidable_specialized": 0,
  "U_wait": 0.3178088556827823,
  "U_critical": 0.10700188040493985,
  "U_reject": 0.8,
  "U_specialized": 1.0,
  "score_excl_runtime": 43.441436113824,
  "score_max_excl_runtime": 95,
  "seed": 20260911,
  "runtime_seconds": 0.011882374999913736
}

