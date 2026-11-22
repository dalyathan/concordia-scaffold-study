# Demo failure map (plain Gemma, no Notes, 140 demo cases)

Hard regret is that of the top offer (argmax of p(k) averaged over the five option orders); soft regret uses the averaged p(k). Too much / too little: top offer above every best offer / below every best offer. Regret is in coins.

### Overall

| Group | Cases | Mean hard regret | Mean soft regret | Non-zero hard regret | Too much | Too little | Mean (expected − best offer) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| all cases | 140 | 0.621 | 0.618 | 55% | 52 | 25 | +0.32 |

### By resale value V

| Group | Cases | Mean hard regret | Mean soft regret | Non-zero hard regret | Too much | Too little | Mean (expected − best offer) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| V = 2 | 28 | 0.343 | 0.366 | 25% | 7 | 0 | +0.60 |
| V = 3 | 28 | 0.250 | 0.293 | 21% | 5 | 1 | +0.34 |
| V = 4 | 28 | 0.443 | 0.462 | 50% | 10 | 4 | +0.25 |
| V = 5 | 28 | 0.871 | 0.792 | 79% | 16 | 6 | +0.40 |
| V = 6 | 28 | 1.200 | 1.177 | 100% | 14 | 14 | +0.03 |

### By seller line

| Group | Cases | Mean hard regret | Mean soft regret | Non-zero hard regret | Too much | Too little | Mean (expected − best offer) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| neutral | 20 | 0.100 | 0.120 | 35% | 4 | 3 | +0.32 |
| pressure | 20 | 0.200 | 0.156 | 55% | 10 | 1 | +0.54 |
| information | 100 | 0.810 | 0.810 | 59% | 38 | 21 | +0.28 |

### By stated cost C (information cases)

| Group | Cases | Mean hard regret | Mean soft regret | Non-zero hard regret | Too much | Too little | Mean (expected − best offer) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| C = 1 | 20 | 1.150 | 1.195 | 100% | 20 | 0 | +1.19 |
| C = 2 | 20 | 1.200 | 1.146 | 75% | 14 | 1 | +0.99 |
| C = 3 | 20 | 0.900 | 0.916 | 60% | 4 | 8 | -0.09 |
| C = 4 | 20 | 0.600 | 0.592 | 40% | 0 | 8 | -0.53 |
| C = 5 | 20 | 0.200 | 0.202 | 20% | 0 | 4 | -0.18 |

### By case type

| Group | Cases | Mean hard regret | Mean soft regret | Non-zero hard regret | Too much | Too little | Mean (expected − best offer) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| no information | 40 | 0.150 | 0.138 | 45% | 14 | 4 | +0.43 |
| stated cost C < V | 60 | 1.333 | 1.307 | 97% | 37 | 21 | +0.35 |
| stated cost C >= V | 40 | 0.025 | 0.064 | 2% | 1 | 0 | +0.17 |

### By V and seller line

| Group | Cases | Mean hard regret | Mean soft regret | Non-zero hard regret | Too much | Too little | Mean (expected − best offer) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| V = 2, neutral | 4 | 0.000 | 0.114 | 0% | 0 | 0 | +0.47 |
| V = 2, pressure | 4 | 0.400 | 0.286 | 50% | 2 | 0 | +0.80 |
| V = 2, information | 20 | 0.400 | 0.433 | 25% | 5 | 0 | +0.58 |
| V = 3, neutral | 4 | 0.000 | 0.020 | 0% | 0 | 0 | +0.48 |
| V = 3, pressure | 4 | 0.000 | 0.016 | 0% | 0 | 0 | +0.52 |
| V = 3, information | 20 | 0.350 | 0.403 | 30% | 5 | 1 | +0.28 |
| V = 4, neutral | 4 | 0.000 | 0.067 | 0% | 0 | 0 | +0.30 |
| V = 4, pressure | 4 | 0.100 | 0.101 | 50% | 2 | 0 | +0.48 |
| V = 4, information | 20 | 0.600 | 0.613 | 60% | 8 | 4 | +0.19 |
| V = 5, neutral | 4 | 0.300 | 0.218 | 75% | 3 | 0 | +0.43 |
| V = 5, pressure | 4 | 0.300 | 0.199 | 75% | 3 | 0 | +0.65 |
| V = 5, information | 20 | 1.100 | 1.025 | 80% | 10 | 6 | +0.34 |
| V = 6, neutral | 4 | 0.200 | 0.182 | 100% | 1 | 3 | -0.08 |
| V = 6, pressure | 4 | 0.200 | 0.176 | 100% | 3 | 1 | +0.27 |
| V = 6, information | 20 | 1.600 | 1.576 | 100% | 10 | 10 | -0.00 |

### Summary

```json
{
 "n_cases": 140,
 "share_nonzero_hard_regret": 0.55,
 "at_least_30pct_nonzero": true,
 "too_high": 52,
 "too_low": 25,
 "mean_hard_regret": 0.6214285714285714,
 "mean_soft_regret": 0.6179588913838456,
 "top_offer_counts": {
  "1": 11,
  "2": 76,
  "3": 22,
  "4": 31
 },
 "mean_letter_mass": 0.6357240917097235,
 "order_consistent_top_offer": 0.32857142857142857
}
```
