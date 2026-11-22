# Demo failure map (plain Gemma, no Notes, 72 demo cases, split: test)

Hard regret is that of the top offer (argmax of p(k) averaged over the five option orders); soft regret uses the averaged p(k). Too much / too little: top offer above every best offer / below every best offer. Regret is in coins.

### Overall

| Group | Cases | Mean hard regret | Mean soft regret | Non-zero hard regret | Too much | Too little | Mean (expected − best offer) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| all cases | 72 | 0.536 | 0.534 | 51% | 27 | 10 | +0.38 |

### By resale value V

| Group | Cases | Mean hard regret | Mean soft regret | Non-zero hard regret | Too much | Too little | Mean (expected − best offer) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| V = 2 | 16 | 0.163 | 0.199 | 19% | 3 | 0 | +0.56 |
| V = 3 | 12 | 0.333 | 0.338 | 33% | 4 | 0 | +0.30 |
| V = 4 | 16 | 0.275 | 0.289 | 38% | 6 | 0 | +0.41 |
| V = 5 | 12 | 0.833 | 0.852 | 67% | 6 | 2 | +0.58 |
| V = 6 | 16 | 1.100 | 1.023 | 100% | 8 | 8 | +0.05 |

### By seller line

| Group | Cases | Mean hard regret | Mean soft regret | Non-zero hard regret | Too much | Too little | Mean (expected − best offer) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| neutral | 12 | 0.067 | 0.121 | 33% | 1 | 3 | +0.23 |
| pressure | 12 | 0.233 | 0.188 | 67% | 7 | 1 | +0.52 |
| information | 48 | 0.729 | 0.724 | 52% | 19 | 6 | +0.38 |

### By stated cost C (information cases)

| Group | Cases | Mean hard regret | Mean soft regret | Non-zero hard regret | Too much | Too little | Mean (expected − best offer) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| C = 1 | 8 | 1.000 | 1.052 | 100% | 8 | 0 | +1.05 |
| C = 2 | 12 | 1.083 | 1.051 | 75% | 9 | 0 | +0.99 |
| C = 3 | 8 | 0.750 | 0.731 | 50% | 2 | 2 | +0.04 |
| C = 4 | 12 | 0.667 | 0.654 | 33% | 0 | 4 | -0.37 |
| C = 5 | 8 | 0.000 | 0.001 | 0% | 0 | 0 | +0.24 |

### By case type

| Group | Cases | Mean hard regret | Mean soft regret | Non-zero hard regret | Too much | Too little | Mean (expected − best offer) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| no information | 24 | 0.150 | 0.154 | 50% | 8 | 4 | +0.38 |
| stated cost C < V | 24 | 1.417 | 1.380 | 100% | 18 | 6 | +0.53 |
| stated cost C >= V | 24 | 0.042 | 0.068 | 4% | 1 | 0 | +0.23 |

### By V and seller line

| Group | Cases | Mean hard regret | Mean soft regret | Non-zero hard regret | Too much | Too little | Mean (expected − best offer) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| V = 2, neutral | 4 | 0.000 | 0.114 | 0% | 0 | 0 | +0.47 |
| V = 2, pressure | 4 | 0.400 | 0.286 | 50% | 2 | 0 | +0.80 |
| V = 2, information | 8 | 0.125 | 0.199 | 12% | 1 | 0 | +0.49 |
| V = 3, information | 12 | 0.333 | 0.338 | 33% | 4 | 0 | +0.30 |
| V = 4, neutral | 4 | 0.000 | 0.067 | 0% | 0 | 0 | +0.30 |
| V = 4, pressure | 4 | 0.100 | 0.101 | 50% | 2 | 0 | +0.48 |
| V = 4, information | 8 | 0.500 | 0.493 | 50% | 4 | 0 | +0.43 |
| V = 5, information | 12 | 0.833 | 0.852 | 67% | 6 | 2 | +0.58 |
| V = 6, neutral | 4 | 0.200 | 0.182 | 100% | 1 | 3 | -0.08 |
| V = 6, pressure | 4 | 0.200 | 0.176 | 100% | 3 | 1 | +0.27 |
| V = 6, information | 8 | 2.000 | 1.866 | 100% | 4 | 4 | +0.01 |

### Summary

```json
{
 "n_cases": 72,
 "share_nonzero_hard_regret": 0.5138888888888888,
 "at_least_30pct_nonzero": true,
 "too_high": 27,
 "too_low": 10,
 "mean_hard_regret": 0.5361111111111111,
 "mean_soft_regret": 0.533891452204181,
 "top_offer_counts": {
  "1": 9,
  "2": 35,
  "3": 14,
  "4": 14
 },
 "mean_letter_mass": 0.642715070892951,
 "order_consistent_top_offer": 0.3194444444444444
}
```
