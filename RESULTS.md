# Karp–Flatt results

Host: 12th Gen Intel Core i5-12500H (Alder Lake), 12 physical cores, 16 logical processors, 64-byte cache lines. `os.cpu_count()` is 16. Each trial pins workers to four performance cores (logical CPUs 0, 2, 4, 6). The timing process sits on an efficiency core so it does not share those cores.

`S(p) = T(1) / T(p)`

`e(p) = (p · T(p) / T(1) − 1) / (p − 1)`

| Experiment | Mode | T1 (s) | T2 (s) | T4 (s) | e(2) | e(4) | Architectural diagnosis |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A: Serial tail | median of 5 | 5.475 | 2.934 | 1.624 | 0.072 | 0.062 | Constant e → fixed Amdahl serialization |
| B: Lock contention | 1 trial, 500,000 increments | 1.668 | 7.161 | 12.310 | 7.584 | 9.504 | Exploding e → mutex and cache-line thrashing |
| C: Privatized state | 1 trial, 20,000,000 increments | 0.529 | 0.295 | 0.168 | 0.114 | 0.089 | Scaling restored, E(4) = 78.9% |

## Checks

- Experiment A: `e(4) / e(2) = 0.865`, inside [0.80, 1.25]. The 0.40 s sleep is about 7% of T(1) on this run, so e sits near 0.07 rather than the handout’s 0.12 example. It does not grow with worker count.
- Experiment B: T(4) = 12.310 s is much larger than T(1) = 1.668 s, and e(4) = 9.504 is above e(2) = 7.584. Speedup is below 1 at both 2 and 4 workers.
- Experiment C: T(4) = 0.168 s is below T(1) = 0.529 s. Speedup is 3.16, so efficiency is 78.9%, above 70%.

## What the three runs mean

Experiment A spends 0.40 s in the parent before a fixed batch of `sin · cos` work. Adding workers shortens only the math, so the Karp–Flatt value stays put. That is a serial fraction, not cores fighting.

Experiment B splits the same increments across workers and takes one lock on every increment. Two workers are already several times slower than one, and four are slower still. e above 1 means the overhead itself grows as cores are added. The counter still ends at the full increment count.

Experiment C adds into a private variable and sums the four return values once. The lock is gone from the loop, T(4) drops below T(1), and efficiency clears 70%. e does not fall all the way to 0.03 because `Pool.map` still ships the tasks, but the collapse from Experiment B is gone.
