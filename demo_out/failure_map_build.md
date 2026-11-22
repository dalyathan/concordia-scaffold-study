# Demo failure map (plain Gemma, no Notes, 34 demo cases, split: build)

Hard regret is that of the top offer (argmax of p(k) averaged over the five option orders); soft regret uses the averaged p(k). Too much / too little: top offer above every best offer / below every best offer. Regret is in coins.

### Overall

| Group | Cases | Mean hard regret | Mean soft regret | Non-zero hard regret | Too much | Too little | Mean (expected − best offer) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| all cases | 34 | 0.729 | 0.699 | 56% | 10 | 9 | +0.12 |

### By resale value V

| Group | Cases | Mean hard regret | Mean soft regret | Non-zero hard regret | Too much | Too little | Mean (expected − best offer) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| V = 2 | 6 | 0.500 | 0.497 | 33% | 2 | 0 | +0.38 |
| V = 3 | 8 | 0.125 | 0.253 | 12% | 0 | 1 | +0.33 |
| V = 4 | 6 | 0.667 | 0.679 | 67% | 2 | 2 | -0.02 |
| V = 5 | 8 | 0.850 | 0.734 | 75% | 4 | 2 | +0.08 |
| V = 6 | 6 | 1.667 | 1.471 | 100% | 2 | 4 | -0.22 |

### By seller line

| Group | Cases | Mean hard regret | Mean soft regret | Non-zero hard regret | Too much | Too little | Mean (expected − best offer) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| neutral | 4 | 0.100 | 0.111 | 25% | 1 | 0 | +0.31 |
| pressure | 4 | 0.100 | 0.092 | 25% | 1 | 0 | +0.43 |
| information | 26 | 0.923 | 0.883 | 65% | 8 | 9 | +0.05 |

### By stated cost C (information cases)

| Group | Cases | Mean hard regret | Mean soft regret | Non-zero hard regret | Too much | Too little | Mean (expected − best offer) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| C = 1 | 6 | 1.167 | 1.170 | 100% | 6 | 0 | +1.17 |
| C = 2 | 4 | 1.250 | 1.274 | 75% | 2 | 1 | +0.92 |
| C = 3 | 6 | 1.333 | 1.141 | 67% | 0 | 4 | -0.34 |
| C = 4 | 4 | 0.500 | 0.498 | 50% | 0 | 2 | -0.82 |
| C = 5 | 6 | 0.333 | 0.335 | 33% | 0 | 2 | -0.67 |

### By case type

| Group | Cases | Mean hard regret | Mean soft regret | Non-zero hard regret | Too much | Too little | Mean (expected − best offer) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| no information | 8 | 0.100 | 0.101 | 25% | 2 | 0 | +0.37 |
| stated cost C < V | 18 | 1.333 | 1.262 | 94% | 8 | 9 | +0.10 |
| stated cost C >= V | 8 | 0.000 | 0.031 | 0% | 0 | 0 | -0.07 |

### By V and seller line

| Group | Cases | Mean hard regret | Mean soft regret | Non-zero hard regret | Too much | Too little | Mean (expected − best offer) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| V = 2, information | 6 | 0.500 | 0.497 | 33% | 2 | 0 | +0.38 |
| V = 3, neutral | 2 | 0.000 | 0.016 | 0% | 0 | 0 | +0.46 |
| V = 3, pressure | 2 | 0.000 | 0.013 | 0% | 0 | 0 | +0.51 |
| V = 3, information | 4 | 0.250 | 0.492 | 25% | 0 | 1 | +0.18 |
| V = 4, information | 6 | 0.667 | 0.679 | 67% | 2 | 2 | -0.02 |
| V = 5, neutral | 2 | 0.200 | 0.206 | 50% | 1 | 0 | +0.16 |
| V = 5, pressure | 2 | 0.200 | 0.171 | 50% | 1 | 0 | +0.35 |
| V = 5, information | 4 | 1.500 | 1.280 | 100% | 2 | 2 | -0.09 |
| V = 6, information | 6 | 1.667 | 1.471 | 100% | 2 | 4 | -0.22 |

### Summary

```json
{
 "n_cases": 34,
 "share_nonzero_hard_regret": 0.5588235294117647,
 "at_least_30pct_nonzero": true,
 "too_high": 10,
 "too_low": 9,
 "mean_hard_regret": 0.7294117647058824,
 "mean_soft_regret": 0.6994901678424762,
 "top_offer_counts": {
  "1": 2,
  "2": 25,
  "3": 1,
  "4": 6
 },
 "mean_letter_mass": 0.6217104951649507,
 "order_consistent_top_offer": 0.35294117647058826
}
```
