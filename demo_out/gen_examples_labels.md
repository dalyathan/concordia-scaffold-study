# Claude's example labels vs the oracle (100 LoRA training cases; no label corrected)

claude_labels.json sha256 0b6f0febaa1d32302bf275bab823893db481d0386e1eccb36e52a1cbb7f95839; usable labels 100 of 100; unusable ids after at most one re-ask: []

| Type | n | accuracy (label is an oracle-best price) | mean regret | share labelled cheapest |
| --- | --- | --- | --- | --- |
| all | 100 | 1.00 | 0.000 | 0.65 |
| below | 34 | 1.00 | 0.000 | 0.53 |
| at_or_above | 33 | 1.00 | 0.000 | 1.00 |
| no_cost | 33 | 1.00 | 0.000 | 0.42 |
