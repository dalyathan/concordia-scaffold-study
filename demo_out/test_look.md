# test_look: 72 cases, 18 cells (TEST LOOK)

**Outcome label: SUPPORT (beats always-2 with lower bound > 0: no)**

frozen development verdict: NOT PASSED (owner's rule, wrong-rule lower bound -0.003); this test look is a separate exploratory-derived question

| Arm | Soft regret |
| --- | --- |
| method | 0.263 |
| wrong_rule | 0.482 |
| neutral | 0.549 |
| plain | 0.534 |
| always2 | 0.378 |
| method_text_in_prompt | 0.256 |

Comparator table: difference control - method (paired cell bootstrap 10,000, seed 0; threshold D >= 0.10 and lower bound > 0 for wrong-rule, neutral, plain):

| Control | D [95% interval], cells better | D >= 0.10 | lower bound > 0 |
| --- | --- | --- | --- |
| plain | +0.271 [+0.054, +0.514], 11 of 18 cells | yes | yes |
| neutral | +0.286 [+0.064, +0.536], 11 of 18 cells | yes | yes |
| wrong_rule | +0.219 [+0.048, +0.399], 11 of 18 cells | yes | yes |
| always2 | +0.115 [-0.066, +0.317], 6 of 18 cells | yes | no |

Split of the difference by cell type (descriptive): C<V: plain +0.882, neutral +0.947, wrong_rule +0.699, always2 +0.502; C>=V: plain -0.013, neutral -0.034, wrong_rule -0.028, always2 -0.081; no cost: plain -0.056, neutral -0.054, wrong_rule -0.015, always2 -0.077

Declared secondary, C<V stratum (cells: 6), control - method: plain +0.882 [+0.616, +1.162], 6 of 6 cells; neutral +0.947 [+0.724, +1.183], 6 of 6 cells; wrong_rule +0.699 [+0.526, +0.859], 6 of 6 cells; always2 +0.502 [+0.089, +0.890], 4 of 6 cells

Harm check (plain - method over C>=V cells): [-0.012962193276957286, -0.1947856668217982, 0.15721321674356928, 3]
Leave-one-cell-out (wrong-rule - method): {"(2, 'C', 2)": 0.22021837267591096, "(2, 'C', 4)": 0.25308335715025965, "(2, 'neutral')": 0.2207155163076171, "(2, 'pressure')": 0.2218511323279709, "(3, 'C', 1)": 0.17769973385715707, "(3, 'C', 3)": 0.2316538462333898, "(3, 'C', 5)": 0.2321426353998757, "(4, 'C', 2)": 0.21061025703247213, "(4, 'C', 4)": 0.23180246691992187, "(4, 'neutral')": 0.23664216301398835, "(4, 'pressure')": 0.2361260548361234, "(5, 'C', 1)": 0.17815038678002698, "(5, 'C', 3)": 0.18497143403627858, "(5, 'C', 5)": 0.23180462936580865, "(6, 'C', 2)": 0.202537012459525, "(6, 'C', 4)": 0.18999508054490977, "(6, 'neutral')": 0.24087988479782, "(6, 'pressure')": 0.23979473547969146}
Slope of expected offer on stated cost, C<V cells (descriptive): {'method': 0.5260735405586366, 'wrong_rule': -0.007674836870129208, 'neutral': 0.09571077520470206, 'plain': 0.18149715920252354, 'always2': 4.1629469195826856e-16, 'method_text_in_prompt': 0.41677649795788874}
C<V cells where the method's expected offer is closer to the best offer than plain's: [5, 6]
Per-run soft regret: {'method_lr1e-04_s0': 0.21818150836518804, 'method_lr1e-04_s1': 0.30436068051730025, 'method_lr1e-04_s2': 0.2665263755886716, 'wrong_rule_lr1e-03_s0': 0.5248490569052163, 'wrong_rule_lr1e-03_s1': 0.4241825270663813, 'wrong_rule_lr1e-03_s2': 0.4968167637026869, 'neutral_lr1e-04_s0': 0.540676627883262, 'neutral_lr1e-04_s1': 0.541114618548491, 'neutral_lr1e-04_s2': 0.5664221459768232}
Letter mass method / plain: 1.55
Free-text hard regret (descriptive): {'plain': 0.4388888888888889, 'method_seeds': [0.6694444444444445, 0.6666666666666667, 0.8722222222222222], 'method_mean': 0.7361111111111112, 'parse_failure_rate': {'method_lr1e-04_s0': 0.013888888888888888, 'method_lr1e-04_s1': 0.0, 'method_lr1e-04_s2': 0.0, 'plain': 0.0}}
Adapter-off check max abs diff vs saved plain (all cases): 0.00e+00
