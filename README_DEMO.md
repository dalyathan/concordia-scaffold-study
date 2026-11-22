# Does your steering vector do anything a prompt or a constant can't? A five-step recipe

This recipe is what the demo does with Gemma 2 9B on a fruit-buying decision. It works for any model that answers a multiple-choice question whose best answer you can compute.

Each step has one command; the demo's own commands are shown. To adapt a step to your model, replace its scoring function (`demo/scoring.py::score`) and its cases (`refimpl/demo.py`).

## 1. Build an oracle

Write down, for every case, the payoff of every answer, so the best answer and the regret of any answer are computable. In the demo, `core.payoff`, `core.oracle_bids` and `core.hard_regret`/`core.soft_regret` do this.

Then split by *cell*: the payoff-relevant inputs, here resale value, seller line and stated cost. Cases that share a cell are never split between building, tuning and testing.

```bash
python demo/make_splits.py          # demo/splits.json: build / tuning / test by cell
```

## 2. Read out order-averaged choices

Score every answer option as the model's next token after the question. Repeat over every rotation of the option order, and average the probabilities. Position bias is large: here the top answer changed with the order in 67% of cases.

Also check that the failure is real:

- does the answer track the input it should (a slope of 1 on the stated cost)?
- how much of the choice is content and how much position?
- does free text agree with the multiple-choice readout?

```bash
python demo/step2_run.py && python demo/step2_report.py
```

## 3. Find the prompt ceiling with neutral and wrong-rule controls

Before steering, find out what text can do. Insert the following rows as notes, on tuning cases only:

- a correct method;
- a same-length neutral text;
- a wrong rule;
- a disposition;
- the bare rule;
- per-case reasoning;
- the answer itself, as an upper bound.

A vector that does less than the method paragraph is not worth deploying. A method that does no better than neutral text of the same length is not doing anything.

```bash
python demo/step4_run.py && python demo/step4_report.py
```

## 4. Test the vector with steercheck

Build candidate vectors from activation differences: good-minus-bad reasoning, a positive control (offer-lower), and a sentence contrast. `steercheck.run_controls` then tunes each over the same grid, picks layer and strength on tuning cases only, and reports one table:

- plain;
- each vector and its negation;
- the vector at matched budget, ranked among random and Gaussian directions tuned the same way;
- the best constant shift of the output distribution;
- the partial Spearman correlation of the shift with each cell's best answer;
- cell-bootstrap intervals.

```bash
python demo/direction.py && python demo/tune_job.py && python demo/steercheck.py --results demo_out/tune_results.json
```

## 5. State the verdict

Read the table in this order:

1. Does the vector beat plain, with a cell-bootstrap interval above zero?
2. Does it beat its own negation?
3. Does it rank in the top few percent of random directions given the same tuning budget?
4. Does it beat the best constant shift, which needs no model?
5. Does its shift correlate with each case's best answer, rather than moving everything one way?
6. Does it come anywhere near the prompt ceiling from step 3?

Say "it works" only if all six hold on held-out test cells. Otherwise say which control it failed.

```bash
python demo/floor.py --serve --model 9b     # then: case <id>, steer <config.json>, table
```
