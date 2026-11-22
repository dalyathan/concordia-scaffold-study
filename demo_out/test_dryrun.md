# test_dryrun: 24 cases, 6 cells (DRY RUN on held-out TUNE cases, not a result)

**Outcome label: PARTIAL: lower bound > 0 vs plain and neutral; SUPPORT not met because: wrong_rule**

frozen development verdict: NOT PASSED (owner's rule, wrong-rule lower bound -0.003); this test look is a separate exploratory-derived question

| Arm | Soft regret |
| --- | --- |
| method | 0.193 |
| wrong_rule | 0.405 |
| neutral | 0.527 |
| plain | 0.577 |
| always2 | 0.333 |
| method_text_in_prompt | 0.171 |

Comparator table: difference control - method (paired cell bootstrap 10,000, seed 0; threshold D >= 0.10 and lower bound > 0 for wrong-rule, neutral, plain):

| Control | D [95% interval], cells better | D >= 0.10 | lower bound > 0 |
| --- | --- | --- | --- |
| plain | +0.383 [+0.034, +0.762], 5 of 6 cells | yes | yes |
| neutral | +0.333 [+0.021, +0.696], 4 of 6 cells | yes | yes |
| wrong_rule | +0.211 [-0.032, +0.503], 4 of 6 cells | yes | no |
| always2 | +0.140 [-0.110, +0.452], 2 of 6 cells | yes | no |

Split of the difference by cell type (descriptive): C<V: plain +0.790, neutral +0.703, wrong_rule +0.499, always2 +0.377; C>=V: plain -0.122, neutral -0.113, wrong_rule -0.119, always2 -0.123; no cost: plain +0.025, neutral +0.002, wrong_rule -0.056, always2 -0.084

Declared secondary, C<V stratum (cells: 3), control - method: plain +0.790 [+0.391, +1.076], 3 of 3 cells; neutral +0.703 [+0.371, +1.064], 3 of 3 cells; wrong_rule +0.499 [+0.282, +0.820], 3 of 3 cells; always2 +0.377 [-0.095, +0.828], 2 of 3 cells

Harm check (plain - method over C>=V cells): None
Leave-one-cell-out (wrong-rule - method): {"(3, 'C', 2)": 0.1968610591192858, "(3, 'C', 4)": 0.27701467233660126, "(3, 'neutral')": 0.2515585541492979, "(5, 'C', 4)": 0.17424937958813183, "(5, 'pressure')": 0.27753554477243514, "(6, 'C', 1)": 0.08929138528019043}
Slope of expected offer on stated cost, C<V cells (descriptive): {'method': 0.4993925827497952, 'wrong_rule': -0.010050218008386352, 'neutral': 0.0745264313031362, 'plain': 0.05265374336729446, 'always2': 7.190743900312752e-17, 'method_text_in_prompt': 0.5303845453484508}
C<V cells where the method's expected offer is closer to the best offer than plain's: [3, 3]
Per-run soft regret: {'method_lr1e-04_s0': 0.15510958211242618, 'method_lr1e-04_s1': 0.21645377809817246, 'method_lr1e-04_s2': 0.20883872866374162, 'wrong_rule_lr1e-03_s0': 0.4302789099455991, 'wrong_rule_lr1e-03_s1': 0.35461104252414094, 'wrong_rule_lr1e-03_s2': 0.42876743402757156, 'neutral_lr1e-04_s0': 0.5361319527424564, 'neutral_lr1e-04_s1': 0.5293765945934643, 'neutral_lr1e-04_s2': 0.5150853917921789}
Letter mass method / plain: 1.56
Free-text hard regret (descriptive): {'plain': 0.5, 'method_seeds': [0.4666666666666666, 0.44166666666666665, 0.5666666666666667], 'method_mean': 0.49166666666666664, 'parse_failure_rate': {'method_lr1e-04_s0': 0.0, 'method_lr1e-04_s1': 0.0, 'method_lr1e-04_s2': 0.0, 'plain': 0.0}}
Adapter-off check max abs diff vs saved plain (all cases): 0.00e+00
