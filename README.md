# Hospital Bed Allocation

## Analysis of PS

The PS asks us to run a simulation, generating 500 patient entries, the random generation is to be done using NumPy PCG64 with seed: 20260911, the patient can be of 3 acuity, 1st is general having a probability of 0.6, then is monitored with prob 0.3 and lastly critical with prob 0.1 . It is defined what kinds of beds can be alloted to what kind of patients, and how many beds are there. We are asked to make a policy such that patients are alloted beds within least amount of time and to admit as many patients as possible. Factors such as LOS per patient is also random.

## What We Were Trying To Do
We tested different rules ("policies") for deciding which hospital bed a patient gets, based on how sick they are (Level 1 = least serious, Level 3 = most serious). The goal was to reduce how many patients get rejected (turned away) and how long they wait, while still treating the sickest patients properly.

All tests used the same 500 fake patients (same seed number), so the results can be fairly compared.

## The Policies We Tried

### Policy 1 — "Use the simplest bed that works"
- Level 3 patients: critical beds only.
- Level 2 patients: monitored beds normally; can use a critical bed only if they've waited 2+ hours and no monitored bed is free.
- Level 1 patients: general beds normally; can use monitored or critical beds only if they've waited 2+ hours and nothing lower is free.
- Sicker patients get priority; same-level patients are served in the order they arrived.

**Result:** 0 Level 1 rejected, 68 Level 2 rejected, 32 Level 3 rejected. 400 out of 500 admitted.
**Score:** 44.67 out of 95

### Experimental Policy 1 — "Give up on Level 3 to help Level 2"
- Level 3 patients are never admitted at all (always rejected).
- Level 1 uses general beds; Level 2 uses monitored beds, then critical beds if needed.

**Result:** 0 Level 1 rejected, 36 Level 2 rejected, 63 Level 3 rejected (all of them). 401 admitted — barely better than Policy 1, and it completely sacrifices the sickest patients. Not a good trade.
**Score:** 40.62 out of 95 (lower than Policy 1)

### Policy 2 — "Strict, no sharing beds"
- Level 1 can only use general beds, Level 2 only monitored, Level 3 only critical. No flexibility at all.

**Result:** Exactly the same numbers as Policy 1 (0 / 68 / 32 rejected). This tells us that in this test, the "flexibility" in Policy 1 (letting patients wait 2 hours then use a higher bed) almost never actually got used — probably because when a patient was stuck waiting, ALL bed types were full anyway, not just their own type.
**Score:** 44.67 out of 95 (tied with Policy 1)

**Revision:** Since acuity 1 patients are not being rejected, and allocating them beds after 2 hours seems bad idea for other seeds, we limited to general only for acuity 1 regardless of wait time.

### Policy 3 — "Hold 2 critical beds in reserve for Level 2"
- Same as Policy 1, but 2 critical beds are kept empty, saved only for Level 2 patients.

**Result:** Worse overall — 44 Level 2 rejected (better than Policy 1's 68) but 60 Level 3 rejected (much worse than Policy 1's 32), and total admissions dropped to 396. Holding beds back for Level 2 ends up hurting Level 3 patients more than it helps Level 2. Not worth it.
**Score:** 41.54 out of 95 (lower than Policy 1)

### Policy 4 — "Let Level 2 jump to Level 3 beds after 2 hours, drop priority order"
- Level 1 stays on general beds. Level 2 can use critical beds after waiting 2+ hours. Also removed the rule that sicker patients get served first.

**Result:** Also worse — 55 Level 2 rejected and 45 Level 3 rejected (400 admitted total). Removing the "treat sicker patients first" rule and letting Level 2 grab critical beds made things worse for Level 3 patients without meaningfully helping Level 2.
**Score:** 43.44 out of 95 (lower than Policy 1)

## Score Comparison (out of 95)

| Policy | Score | Admitted | L1 Rejected | L2 Rejected | L3 Rejected |
|---|---|---|---|---|---|
| Policy 1 (base) | 44.67 | 400 | 0 | 68 | 32 |
| Policy 2 (strict) | 44.67 | 400 | 0 | 68 | 32 |
| Policy 4 (drop priority order) | 43.44 | 400 | 0 | 55 | 45 |
| Policy 3 (reserve beds) | 41.54 | 396 | 0 | 44 | 60 |
| Experimental Policy 1 (drop L3) | 40.62 | 401 | 0 | 36 | 63 |

**Best score so far: Policy 1 / Policy 2, tied at 44.67.** Every change we tried away from the base rule made the score go down.

**Final Policy used is Policy 1 with revision given in ```policy.py``` file.**

## Key Things We Learned

1. **Level 1 patients never got rejected in any policy tested.** They were fine using only general beds — they never actually needed the extra flexibility of monitored/critical beds.
2. **The "wait 2 hours, then use a better bed" flexibility rule barely mattered.** Policy 1 and the strict Policy 2 (no flexibility at all) gave identical results. When patients were stuck waiting, it usually meant ALL bed types were full, not just their own — so having permission to "upgrade" beds didn't actually help.
3. **Sacrificing Level 3 patients to help Level 2 (Experimental Policy 1) is a bad trade.** It only reduced total rejections by 1 patient while completely abandoning all Level 3 (most critical) patients.
4. **Reserving beds for Level 2 (Policy 3) backfired.** It helped Level 2 a bit but hurt Level 3 a lot more, and fewer patients overall got admitted.
5. **Dropping the "treat sicker patients first" rule (Policy 4) also backfired.** It made outcomes worse for Level 3 without real gains for Level 2.

## Bottom Line
**Policy 1 (and the identical Policy 2) is the best of everything tested so far.** It keeps the simple rule of "sicker patients get priority, use the lowest bed that fits, allow overflow only after a 2-hour wait." The other approaches (sacrificing Level 3, reserving beds, dropping priority order) all made total results worse, mainly by hurting the most critical patients without gaining much for less critical ones.

**Next steps to consider:** Since the "wait 2 hours then upgrade" rule isn't actually kicking in (because higher beds are also full when patients wait), the real bottleneck seems to be overall bed supply, not the allocation rule itself. Future tests could look at whether adding capacity, or predicting turnover, helps more than rearranging allocation logic.
