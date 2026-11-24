| Data | Arm | max abs dp | mean abs dp | soft A10G | soft A40 | Δ soft | Δ below | Δ at/above | Δ no-cost | largest cell Δ | argmax changes | 3-dp flips |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| gen | plain | 5.8e-02 | 5.6e-03 | 0.6572 | 0.6608 | +3.5e-03 | +5.4e-03 | +3.6e-03 | +1.7e-03 | +5.9e-02 | 0 | overall,below,at_or_above,no_cost |
| gen | gen_answer_only_lr1e-04_s0 | 2.1e-02 | 1.6e-03 | 0.0258 | 0.0271 | +1.3e-03 | -9.4e-06 | +3.8e-03 | +4.0e-05 | +3.8e-02 | 0 | overall,at_or_above |
| gen | gen_answer_only_lr3e-04_s0 | 1.0e-02 | 9.6e-04 | 0.1184 | 0.1187 | +2.9e-04 | +8.4e-05 | +4.8e-04 | +3.1e-04 | -6.1e-03 | 0 | overall,no_cost |
| gen | gen_cheapest_label_lr1e-04_s0 | 1.8e-06 | 2.1e-07 | 0.4286 | 0.4286 | +3.3e-07 | +6.2e-07 | +3.8e-07 | -1.8e-08 | +4.3e-06 | 0 | - |
| gen | gen_cheapest_label_n25_lr1e-04_s0 | 2.2e-04 | 1.8e-06 | 0.4286 | 0.4286 | +1.2e-06 | +3.8e-06 | -2.5e-07 | +8.2e-08 | +6.1e-05 | 0 | - |
| gen | gen_claude_examples_lr1e-04_s0 | 4.9e-02 | 1.1e-03 | 0.0131 | 0.0131 | +1.7e-05 | +5.5e-05 | -2.7e-06 | -4.0e-07 | -1.1e-03 | 2 | - |
| gen | gen_claude_examples_lr1e-04_s1 | 1.9e-02 | 7.0e-04 | 0.0264 | 0.0265 | +1.1e-04 | +1.8e-05 | -2.4e-04 | +5.5e-04 | -3.4e-03 | 0 | - |
| gen | gen_claude_examples_lr1e-04_s2 | 2.1e-02 | 1.2e-03 | 0.0567 | 0.0576 | +8.7e-04 | +4.1e-04 | +1.6e-03 | +6.1e-04 | +2.2e-02 | 0 | overall,at_or_above |
| gen | gen_claude_examples_lr3e-04_s0 | 4.2e-02 | 1.3e-03 | 0.1194 | 0.1191 | -2.9e-04 | -6.4e-04 | +2.0e-04 | -4.4e-04 | -9.1e-03 | 1 | below,at_or_above |
| gen | gen_claude_examples_n10_lr1e-04_s0 | 3.2e-02 | 1.5e-03 | 0.0711 | 0.0712 | +5.6e-05 | +3.6e-04 | -1.6e-04 | -2.8e-05 | +9.5e-03 | 1 | - |
| gen | gen_claude_examples_n10_lr1e-04_s1 | 7.3e-02 | 2.0e-03 | 0.1513 | 0.1479 | -3.4e-03 | -5.1e-05 | -7.1e-03 | -2.9e-03 | -6.7e-02 | 2 | overall,at_or_above,no_cost |
| gen | gen_claude_examples_n10_lr1e-04_s2 | 2.6e-02 | 8.8e-04 | 0.0537 | 0.0538 | +8.2e-05 | -5.4e-04 | -6.5e-05 | +8.5e-04 | -4.5e-03 | 0 | below,no_cost |
| gen | gen_claude_examples_n25_lr1e-04_s0 | 3.2e-02 | 5.5e-04 | 0.0430 | 0.0427 | -3.1e-04 | -6.2e-05 | -6.1e-04 | -2.4e-04 | -1.2e-02 | 0 | no_cost |
| gen | gen_claude_examples_n25_lr1e-04_s1 | 2.2e-02 | 4.6e-04 | 0.0366 | 0.0371 | +4.8e-04 | -3.9e-05 | +1.6e-03 | -1.4e-04 | +2.3e-02 | 0 | at_or_above |
| gen | gen_claude_examples_n25_lr1e-04_s2 | 5.0e-02 | 7.4e-04 | 0.0453 | 0.0447 | -6.0e-04 | +4.6e-04 | -3.1e-03 | +8.3e-04 | -4.6e-02 | 0 | at_or_above,no_cost |
| gen | gen_claude_examples_n50_lr1e-04_s0 | 1.5e-02 | 5.9e-04 | 0.0144 | 0.0145 | +1.3e-04 | -5.5e-04 | +1.3e-03 | -3.4e-04 | +1.8e-02 | 0 | overall,at_or_above |
| gen | gen_claude_examples_n50_lr1e-04_s1 | 4.0e-02 | 1.7e-03 | 0.0279 | 0.0284 | +4.3e-04 | +2.6e-04 | -5.9e-05 | +1.1e-03 | +8.0e-03 | 1 | no_cost |
| gen | gen_claude_examples_n50_lr1e-04_s2 | 1.3e-02 | 7.7e-04 | 0.0768 | 0.0767 | -5.5e-05 | +1.7e-04 | -6.7e-04 | +3.4e-04 | -6.8e-03 | 0 | - |
| gen | gen_method_original_lr1e-04_s0 | 1.2e-02 | 1.4e-03 | 0.4024 | 0.4015 | -9.2e-04 | -3.4e-03 | -6.2e-04 | +1.2e-03 | -4.1e-02 | 1 | below,no_cost |
| gen | gen_method_original_lr1e-04_s1 | 2.4e-02 | 1.5e-03 | 0.3665 | 0.3660 | -5.4e-04 | -2.6e-03 | +9.3e-04 | +5.0e-05 | -3.7e-02 | 0 | overall,below,at_or_above,no_cost |
| gen | gen_method_original_lr1e-04_s2 | 2.3e-02 | 2.1e-03 | 0.3497 | 0.3487 | -9.8e-04 | -2.8e-03 | -3.5e-04 | +1.9e-04 | -3.0e-02 | 0 | overall,below,at_or_above |
| gen | gen_neutral_lr1e-04_s0 | 5.8e-02 | 5.6e-03 | 0.6572 | 0.6608 | +3.5e-03 | +5.4e-03 | +3.6e-03 | +1.7e-03 | +5.9e-02 | 0 | overall,below,at_or_above,no_cost |
| gen | gen_neutral_lr1e-04_s1 | 5.8e-02 | 5.6e-03 | 0.6572 | 0.6608 | +3.5e-03 | +5.4e-03 | +3.6e-03 | +1.7e-03 | +5.9e-02 | 0 | overall,below,at_or_above,no_cost |
| gen | gen_neutral_lr1e-04_s2 | 5.8e-02 | 5.6e-03 | 0.6572 | 0.6608 | +3.5e-03 | +5.4e-03 | +3.6e-03 | +1.7e-03 | +5.9e-02 | 0 | overall,below,at_or_above,no_cost |
| gen | gen_rule_hard_lr1e-04_s0 | 2.3e-02 | 2.1e-03 | 0.3511 | 0.3508 | -2.2e-04 | +3.0e-04 | -1.1e-03 | +1.6e-04 | +2.0e-02 | 0 | below,at_or_above |
| gen | gen_rule_hard_n25_lr1e-04_s0 | 5.2e-02 | 4.2e-03 | 0.3426 | 0.3431 | +5.2e-04 | +4.6e-03 | -1.4e-03 | -1.6e-03 | +7.0e-02 | 2 | below,at_or_above,no_cost |
| gen | gen_shuffled_claude_lr1e-04_s0 | 1.5e-02 | 1.4e-03 | 0.6946 | 0.6954 | +8.6e-04 | +2.8e-03 | -1.6e-04 | -3.0e-05 | +1.2e-02 | 0 | below |
| gen | gen_teacher_lr1e-03_s0 | 5.8e-02 | 5.6e-03 | 0.6572 | 0.6608 | +3.5e-03 | +5.4e-03 | +3.6e-03 | +1.7e-03 | +5.9e-02 | 0 | overall,below,at_or_above,no_cost |
| gen | gen_teacher_lr1e-04_s0 | 1.7e-02 | 2.2e-03 | 0.3804 | 0.3792 | -1.2e-03 | -4.8e-03 | +1.2e-04 | +9.4e-04 | -1.7e-02 | 0 | overall,below,no_cost |
| gen | gen_teacher_lr1e-04_s1 | 1.9e-02 | 1.9e-03 | 0.3516 | 0.3517 | +4.4e-05 | -1.9e-04 | +1.6e-04 | +1.6e-04 | +7.5e-03 | 0 | below |
| gen | gen_teacher_lr1e-04_s2 | 2.8e-02 | 2.3e-03 | 0.3950 | 0.3943 | -7.4e-04 | -1.8e-03 | -8.7e-04 | +5.0e-04 | -1.8e-02 | 0 | overall,below,at_or_above,no_cost |
| gen | gen_teacher_lr3e-04_s0 | 7.0e-03 | 1.2e-03 | 0.3838 | 0.3837 | -1.1e-04 | -1.4e-03 | +4.9e-04 | +5.4e-04 | -7.8e-03 | 1 | below,at_or_above,no_cost |
| gen | gen_teacher_n25_lr1e-04_s0 | 2.7e-02 | 2.7e-03 | 0.3780 | 0.3773 | -6.6e-04 | +1.6e-03 | -3.9e-03 | +2.5e-04 | -3.6e-02 | 2 | overall,below,at_or_above |
| gen | gen_wrong_rule_lr1e-04_s0 | 2.2e-02 | 1.8e-03 | 0.5894 | 0.5891 | -2.6e-04 | -1.5e-03 | +9.4e-04 | -2.0e-04 | +1.2e-02 | 0 | below,at_or_above |
| orig | plain | 0.0e+00 | 0.0e+00 | 0.5767 | 0.5767 | +0.0e+00 | +0.0e+00 | +0.0e+00 | +0.0e+00 | +0.0e+00 | 0 | - |
| orig | answer_only_lr1e-04_s0 | 0.0e+00 | 0.0e+00 | 0.0015 | 0.0015 | +0.0e+00 | +0.0e+00 | +0.0e+00 | +0.0e+00 | +0.0e+00 | 0 | - |
| orig | answer_only_lr3e-04_s0 | 0.0e+00 | 0.0e+00 | 0.0002 | 0.0002 | +0.0e+00 | +0.0e+00 | +0.0e+00 | +0.0e+00 | +0.0e+00 | 0 | - |
| orig | method_lr1e-03_s0 | 0.0e+00 | 0.0e+00 | 0.4203 | 0.4203 | +0.0e+00 | +0.0e+00 | +0.0e+00 | +0.0e+00 | +0.0e+00 | 0 | - |
| orig | method_lr1e-04_s0 | 0.0e+00 | 0.0e+00 | 0.1551 | 0.1551 | +0.0e+00 | +0.0e+00 | +0.0e+00 | +0.0e+00 | +0.0e+00 | 0 | - |
| orig | method_lr1e-04_s1 | 0.0e+00 | 0.0e+00 | 0.2167 | 0.2167 | +0.0e+00 | +0.0e+00 | +0.0e+00 | +0.0e+00 | +0.0e+00 | 0 | - |
| orig | method_lr1e-04_s2 | 0.0e+00 | 0.0e+00 | 0.2095 | 0.2095 | +0.0e+00 | +0.0e+00 | +0.0e+00 | +0.0e+00 | +0.0e+00 | 0 | - |
| orig | method_lr3e-04_s0 | 0.0e+00 | 0.0e+00 | 0.2315 | 0.2315 | +0.0e+00 | +0.0e+00 | +0.0e+00 | +0.0e+00 | +0.0e+00 | 0 | - |
| orig | neutral_lr1e-03_s0 | 0.0e+00 | 0.0e+00 | 0.5767 | 0.5767 | +0.0e+00 | +0.0e+00 | +0.0e+00 | +0.0e+00 | +0.0e+00 | 0 | - |
| orig | neutral_lr1e-04_s0 | 0.0e+00 | 0.0e+00 | 0.5336 | 0.5336 | +0.0e+00 | +0.0e+00 | +0.0e+00 | +0.0e+00 | +0.0e+00 | 0 | - |
| orig | neutral_lr1e-04_s1 | 0.0e+00 | 0.0e+00 | 0.5274 | 0.5274 | +0.0e+00 | +0.0e+00 | +0.0e+00 | +0.0e+00 | +0.0e+00 | 0 | - |
| orig | neutral_lr1e-04_s2 | 0.0e+00 | 0.0e+00 | 0.5164 | 0.5164 | +0.0e+00 | +0.0e+00 | +0.0e+00 | +0.0e+00 | +0.0e+00 | 0 | - |
| orig | neutral_lr3e-04_s0 | 0.0e+00 | 0.0e+00 | 0.5767 | 0.5767 | +0.0e+00 | +0.0e+00 | +0.0e+00 | +0.0e+00 | +0.0e+00 | 0 | - |
| orig | shuffled0_lr1e-04_s0 | 0.0e+00 | 0.0e+00 | 0.5767 | 0.5767 | +0.0e+00 | +0.0e+00 | +0.0e+00 | +0.0e+00 | +0.0e+00 | 0 | - |
| orig | wrong_rule_lr1e-03_s0 | 0.0e+00 | 0.0e+00 | 0.4301 | 0.4301 | +0.0e+00 | +0.0e+00 | +0.0e+00 | +0.0e+00 | +0.0e+00 | 0 | - |
| orig | wrong_rule_lr1e-03_s1 | 0.0e+00 | 0.0e+00 | 0.3542 | 0.3542 | +0.0e+00 | +0.0e+00 | +0.0e+00 | +0.0e+00 | +0.0e+00 | 0 | - |
| orig | wrong_rule_lr1e-03_s2 | 0.0e+00 | 0.0e+00 | 0.4284 | 0.4284 | +0.0e+00 | +0.0e+00 | +0.0e+00 | +0.0e+00 | +0.0e+00 | 0 | - |
| orig | wrong_rule_lr1e-04_s0 | 0.0e+00 | 0.0e+00 | 0.4476 | 0.4476 | +0.0e+00 | +0.0e+00 | +0.0e+00 | +0.0e+00 | +0.0e+00 | 0 | - |
| orig | wrong_rule_lr3e-04_s0 | 0.0e+00 | 0.0e+00 | 0.4735 | 0.4735 | +0.0e+00 | +0.0e+00 | +0.0e+00 | +0.0e+00 | +0.0e+00 | 0 | - |
{
 "all_scored": true,
 "max_abs_d_soft": 0.003548949397951917,
 "max_abs_d_soft_by_type": 0.0071162509602069185,
 "arms_over_threshold": [],
 "arms_with_3dp_flips": {
  "gen:plain": [
   "overall",
   "below",
   "at_or_above",
   "no_cost"
  ],
  "gen:gen_answer_only_lr1e-04_s0": [
   "overall",
   "at_or_above"
  ],
  "gen:gen_answer_only_lr3e-04_s0": [
   "overall",
   "no_cost"
  ],
  "gen:gen_claude_examples_lr1e-04_s2": [
   "overall",
   "at_or_above"
  ],
  "gen:gen_claude_examples_lr3e-04_s0": [
   "below",
   "at_or_above"
  ],
  "gen:gen_claude_examples_n10_lr1e-04_s1": [
   "overall",
   "at_or_above",
   "no_cost"
  ],
  "gen:gen_claude_examples_n10_lr1e-04_s2": [
   "below",
   "no_cost"
  ],
  "gen:gen_claude_examples_n25_lr1e-04_s0": [
   "no_cost"
  ],
  "gen:gen_claude_examples_n25_lr1e-04_s1": [
   "at_or_above"
  ],
  "gen:gen_claude_examples_n25_lr1e-04_s2": [
   "at_or_above",
   "no_cost"
  ],
  "gen:gen_claude_examples_n50_lr1e-04_s0": [
   "overall",
   "at_or_above"
  ],
  "gen:gen_claude_examples_n50_lr1e-04_s1": [
   "no_cost"
  ],
  "gen:gen_method_original_lr1e-04_s0": [
   "below",
   "no_cost"
  ],
  "gen:gen_method_original_lr1e-04_s1": [
   "overall",
   "below",
   "at_or_above",
   "no_cost"
  ],
  "gen:gen_method_original_lr1e-04_s2": [
   "overall",
   "below",
   "at_or_above"
  ],
  "gen:gen_neutral_lr1e-04_s0": [
   "overall",
   "below",
   "at_or_above",
   "no_cost"
  ],
  "gen:gen_neutral_lr1e-04_s1": [
   "overall",
   "below",
   "at_or_above",
   "no_cost"
  ],
  "gen:gen_neutral_lr1e-04_s2": [
   "overall",
   "below",
   "at_or_above",
   "no_cost"
  ],
  "gen:gen_rule_hard_lr1e-04_s0": [
   "below",
   "at_or_above"
  ],
  "gen:gen_rule_hard_n25_lr1e-04_s0": [
   "below",
   "at_or_above",
   "no_cost"
  ],
  "gen:gen_shuffled_claude_lr1e-04_s0": [
   "below"
  ],
  "gen:gen_teacher_lr1e-03_s0": [
   "overall",
   "below",
   "at_or_above",
   "no_cost"
  ],
  "gen:gen_teacher_lr1e-04_s0": [
   "overall",
   "below",
   "no_cost"
  ],
  "gen:gen_teacher_lr1e-04_s1": [
   "below"
  ],
  "gen:gen_teacher_lr1e-04_s2": [
   "overall",
   "below",
   "at_or_above",
   "no_cost"
  ],
  "gen:gen_teacher_lr3e-04_s0": [
   "below",
   "at_or_above",
   "no_cost"
  ],
  "gen:gen_teacher_n25_lr1e-04_s0": [
   "overall",
   "below",
   "at_or_above"
  ],
  "gen:gen_wrong_rule_lr1e-04_s0": [
   "below",
   "at_or_above"
  ]
 },
 "repeat_teacher_bit_identical": true,
 "orig_plain_reference_spread_a10g": 0.0
}
