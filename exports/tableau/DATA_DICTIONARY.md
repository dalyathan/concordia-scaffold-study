# Haggling results: data dictionary

Built by `tools/export_tableau.py` from result files already in the repo (nothing is re-scored; `manifest.json` lists row counts, fingerprints and sources). **Train and tune cases only:** the locked test sets are never read, so patterns found while exploring cannot leak into a test claim.

**The task.** A buyer (Gemma 2 9B) can resell fruit for a known value and must offer one of five prices. The seller accepts any offer at or above their farm cost, which they sometimes state. The best offer can be calculated, so every answer gets an exact score. Money is in coins.

**How to join.** `results.case_id` → `cases.case_id`; `base_per_order.case_id` → `cases.case_id`. `results.run_id` → `training_history.run_id` (adapter rows only).

## cases.csv (684 rows: one per case)
| Column | Meaning |
|---|---|
| case_id | Case. Two cases per cell, differing only in the buyer and seller names (`-n0`, `-n1`). |
| cell_id | The underlying situation (value, prices, seller line, cost, cost range, wording). |
| split | `train` (cases used to build training and selection sets) or `tune` (42 held-out cells × 2 names, used to compare setups). |
| case_type | `below` (stated cost below resale value), `at_or_above` (stated cost at or above resale), `no_cost` (no cost stated). |
| resale_value | What the buyer can resell for. |
| price_list, option1–option5 | The five prices offered, cheapest first. |
| seller_line | `information` (states a cost), `neutral` or `pressure` (no cost). |
| stated_cost | The cost the seller states; blank if none. |
| cost_range_low / high | The range farm costs are drawn from (uniform), stated in the prompt. |
| wording | Which of the seller-line wordings was used (0–2). |
| best_offers | The best offer(s); several when tied. |
| best_payoff | Expected profit of the best offer. |
| in_training_set_100 | 1 if the cell is among the 100 training cells for the adapters. |
| in_selection_set | 1 if the cell is in selection set B (used for early stopping). |

## results.csv (6,876 rows: one per case × setup × seed)
| Column | Meaning |
|---|---|
| family | `base`, `prompt` (text added to the prompt) or `lora` (adapter trained into the weights). |
| setup | Readable name, e.g. "Prompt: written rule", "LoRA: Claude's worked examples". "(control)" marks setups built to fail. |
| run_id, seed, n_training_examples, learning_rate | Adapter rows only: which training run. `n_training_examples` is 10, 25, 50 or 100 cells. |
| offer | The price Gemma puts most probability on (ties go to the cheaper price). |
| offer_position | 1–5: which of the five prices (cheapest = 1). |
| right | 1 if the offer is a best offer. |
| coins_lost | Best payoff minus the payoff of `offer` ("money left on the table"). |
| expected_coins_lost | Best payoff minus the probability-weighted payoff; also counts uncertainty. This is the headline metric in the reports ("soft regret"). |
| confidence | Probability on the offer. |
| expected_offer | Probability-weighted price. |
| p_option1–5 | Probability on each price, cheapest first, averaged over five option orders. |
| letter_mass | Share of next-token probability on the five answer letters (near 1 = the model answers in format). |

Coverage: base and prompt setups have train **and** tune cases; adapters have **tune cases only** (they were scored once on tune, at their best checkpoint).

## training_history.csv (190 rows: one per adapter run × scoring point)
Scores on **selection set B** (42 train cells not used for training) during training. `epoch` 0 is the untrained model. `selection_expected_coins_lost` is the early-stopping metric; `selection_below / at_or_above / no_cost` split it by case type; `selection_offer_slope_on_cost` is how much the offer moves per coin of stated cost (best play: about 0.69); `best_epoch` = 1 marks the checkpoint that was kept.

## base_per_order.csv (17,100 rows)
The base model's probability on each price under each of the five option orders separately, before averaging. Use it to see **position bias**: how much the answer depends on where a price appears in the list.

## Questions worth asking
- Which case types does the base model fail on, and does each fix help all of them?
- Does `confidence` predict `right`?
- How far apart are the three seeds of the same setup?
- In `base_per_order`, how much does the pick change with the order?
