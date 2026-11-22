# Demo failure map (plain Gemma, no Notes, 34 demo cases, split: tuning)

Hard regret is that of the top offer (argmax of p(k) averaged over the five option orders); soft regret uses the averaged p(k). Too much / too little: top offer above every best offer / below every best offer. Regret is in coins.

### Overall

| Group | Cases | Mean hard regret | Mean soft regret | Non-zero hard regret | Too much | Too little | Mean (expected − best offer) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| all cases | 34 | 0.694 | 0.714 | 62% | 15 | 6 | +0.41 |

### By resale value V

| Group | Cases | Mean hard regret | Mean soft regret | Non-zero hard regret | Too much | Too little | Mean (expected − best offer) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| V = 2 | 6 | 0.667 | 0.681 | 33% | 2 | 0 | +0.89 |
| V = 3 | 8 | 0.250 | 0.265 | 12% | 1 | 0 | +0.41 |
| V = 4 | 6 | 0.667 | 0.706 | 67% | 2 | 2 | +0.08 |
| V = 5 | 8 | 0.950 | 0.760 | 100% | 6 | 2 | +0.44 |
| V = 6 | 6 | 1.000 | 1.295 | 100% | 4 | 2 | +0.19 |

### By seller line

| Group | Cases | Mean hard regret | Mean soft regret | Non-zero hard regret | Too much | Too little | Mean (expected − best offer) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| neutral | 4 | 0.200 | 0.127 | 50% | 2 | 0 | +0.60 |
| pressure | 4 | 0.200 | 0.123 | 50% | 2 | 0 | +0.74 |
| information | 26 | 0.846 | 0.896 | 65% | 11 | 6 | +0.32 |

### By stated cost C (information cases)

| Group | Cases | Mean hard regret | Mean soft regret | Non-zero hard regret | Too much | Too little | Mean (expected − best offer) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| C = 1 | 6 | 1.333 | 1.409 | 100% | 6 | 0 | +1.41 |
| C = 2 | 4 | 1.500 | 1.302 | 75% | 3 | 0 | +1.08 |
| C = 3 | 6 | 0.667 | 0.938 | 67% | 2 | 2 | -0.00 |
| C = 4 | 4 | 0.500 | 0.497 | 50% | 0 | 2 | -0.72 |
| C = 5 | 6 | 0.333 | 0.336 | 33% | 0 | 2 | -0.24 |

### By case type

| Group | Cases | Mean hard regret | Mean soft regret | Non-zero hard regret | Too much | Too little | Mean (expected − best offer) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| no information | 8 | 0.200 | 0.125 | 50% | 4 | 0 | +0.67 |
| stated cost C < V | 18 | 1.222 | 1.256 | 94% | 11 | 6 | +0.35 |
| stated cost C >= V | 8 | 0.000 | 0.085 | 0% | 0 | 0 | +0.27 |

### By V and seller line

| Group | Cases | Mean hard regret | Mean soft regret | Non-zero hard regret | Too much | Too little | Mean (expected − best offer) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| V = 2, information | 6 | 0.667 | 0.681 | 33% | 2 | 0 | +0.89 |
| V = 3, neutral | 2 | 0.000 | 0.024 | 0% | 0 | 0 | +0.51 |
| V = 3, pressure | 2 | 0.000 | 0.019 | 0% | 0 | 0 | +0.53 |
| V = 3, information | 4 | 0.500 | 0.508 | 25% | 1 | 0 | +0.30 |
| V = 4, information | 6 | 0.667 | 0.706 | 67% | 2 | 2 | +0.08 |
| V = 5, neutral | 2 | 0.400 | 0.230 | 100% | 2 | 0 | +0.69 |
| V = 5, pressure | 2 | 0.400 | 0.227 | 100% | 2 | 0 | +0.95 |
| V = 5, information | 4 | 1.500 | 1.291 | 100% | 2 | 2 | +0.06 |
| V = 6, information | 6 | 1.000 | 1.295 | 100% | 4 | 2 | +0.19 |

### Summary

```json
{
 "n_cases": 34,
 "share_nonzero_hard_regret": 0.6176470588235294,
 "at_least_30pct_nonzero": true,
 "too_high": 15,
 "too_low": 6,
 "mean_hard_regret": 0.6941176470588236,
 "mean_soft_regret": 0.7144527802468577,
 "top_offer_counts": {
  "2": 16,
  "3": 7,
  "4": 11
 },
 "mean_letter_mass": 0.6349332617488388,
 "order_consistent_top_offer": 0.3235294117647059
}
```
