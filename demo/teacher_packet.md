# Teacher packet: why does Gemma 2 9B misprice fruit?

You are reading this offline. A language model (Gemma 2 9B instruction-tuned) answers a multiple-choice buying decision. It plays a buyer who can resell fruit for V coins; the seller's farm cost is uniform on 1-5 coins unless the seller states it; a seller accepts any offer at or above their farm cost. The buyer's payoff is V minus the offer if accepted, otherwise 0.

## The shared prompt (identical for every case except the {placeholders})

```text
The instructions for how to play the role of {BUYER} are as follows. This is a social science experiment studying how well you play the role of a character named {BUYER}. The experiment is structured as a tabletop roleplaying game (like dungeons and dragons). However, in this case it is a serious social science experiment and simulation. The goal is to be realistic. It is important to play the role of a person like {BUYER} as accurately as possible, i.e., by responding in ways that you think it is likely a person like {BUYER} would respond, and taking into account all information about {BUYER} that you have. Always use third-person limited perspective.

Memories:
Fruits are sold by weight.
The price of one kilogram of fruit is, on average, 3 coins. 1 coin is really cheap and 5 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed.
Sellers at this market pay between 1 and 5 coins per kilogram at the farm, and each amount is equally likely.
A seller accepts any offer at or above their farm cost and refuses anything lower.
When a seller states their farm cost, it is true.
{BUYER} always drives a hard bargain.

Observations:
{OPENING} {BUYER} is trying to buy some fruit from {SELLER}. They are negotiating a price. {BUYER} can sell the fruit for {V} coins back in her home town.
{BUYER} -- "Good morning! I'm interested in your fruit. What can you tell me about it?"
{SELLER} -- "Good morning! It was picked this week and it's ripe and sweet."
{BUYER} -- "It looks good. Let's talk about the price."
{SELLER} -- "{SELLER_LAST_LINE}"
{BUYER} is ready to make an offer.

Question: What price would {BUYER} propose?:
  (a) 1 coin
  (b) 2 coins
  (c) 3 coins
  (d) 4 coins
  (e) 5 coins
Answer: (
```

The five options are shown in five rotated orders; the model's probabilities below are averaged over the orders.

## Cases where the model's top offer was not a best offer (19 cases)

Only the lines that differ are shown. The model's offer distribution follows each case.

### v15-V2-information-C1
- buyer: Opal Apricot; seller: Orion Apricotwood
- resale line: "Opal Apricot can sell the fruit for 2 coins back in her home town."
- seller's last line: "To be honest, this fruit cost me 1 coins at the farm, so price accordingly."
- model's offer probabilities: 1 coin: 0.03, 2 coins: 0.30, 3 coins: 0.66, 4 coins: 0.01, 5 coins: 0.00

### v15-V3-information-C2
- buyer: Opal Apricot; seller: Orion Apricotwood
- resale line: "Opal Apricot can sell the fruit for 3 coins back in her home town."
- seller's last line: "To be honest, this fruit cost me 2 coins at the farm, so price accordingly."
- model's offer probabilities: 1 coin: 0.39, 2 coins: 0.21, 3 coins: 0.05, 4 coins: 0.34, 5 coins: 0.00

### v15-V4-information-C1
- buyer: Opal Apricot; seller: Orion Apricotwood
- resale line: "Opal Apricot can sell the fruit for 4 coins back in her home town."
- seller's last line: "To be honest, this fruit cost me 1 coins at the farm, so price accordingly."
- model's offer probabilities: 1 coin: 0.00, 2 coins: 0.94, 3 coins: 0.05, 4 coins: 0.00, 5 coins: 0.00

### v15-V4-information-C3
- buyer: Opal Apricot; seller: Orion Apricotwood
- resale line: "Opal Apricot can sell the fruit for 4 coins back in her home town."
- seller's last line: "To be honest, this fruit cost me 3 coins at the farm, so price accordingly."
- model's offer probabilities: 1 coin: 0.00, 2 coins: 0.99, 3 coins: 0.01, 4 coins: 0.00, 5 coins: 0.00

### v15-V5-information-C2
- buyer: Opal Apricot; seller: Orion Apricotwood
- resale line: "Opal Apricot can sell the fruit for 5 coins back in her home town."
- seller's last line: "To be honest, this fruit cost me 2 coins at the farm, so price accordingly."
- model's offer probabilities: 1 coin: 0.02, 2 coins: 0.01, 3 coins: 0.44, 4 coins: 0.53, 5 coins: 0.00

### v15-V5-information-C4
- buyer: Opal Apricot; seller: Orion Apricotwood
- resale line: "Opal Apricot can sell the fruit for 5 coins back in her home town."
- seller's last line: "To be honest, this fruit cost me 4 coins at the farm, so price accordingly."
- model's offer probabilities: 1 coin: 0.00, 2 coins: 0.64, 3 coins: 0.35, 4 coins: 0.00, 5 coins: 0.00

### v15-V6-information-C1
- buyer: Opal Apricot; seller: Orion Apricotwood
- resale line: "Opal Apricot can sell the fruit for 6 coins back in her home town."
- seller's last line: "To be honest, this fruit cost me 1 coins at the farm, so price accordingly."
- model's offer probabilities: 1 coin: 0.00, 2 coins: 0.89, 3 coins: 0.06, 4 coins: 0.04, 5 coins: 0.00

### v15-V6-information-C3
- buyer: Opal Apricot; seller: Orion Apricotwood
- resale line: "Opal Apricot can sell the fruit for 6 coins back in her home town."
- seller's last line: "To be honest, this fruit cost me 3 coins at the farm, so price accordingly."
- model's offer probabilities: 1 coin: 0.01, 2 coins: 0.71, 3 coins: 0.01, 4 coins: 0.27, 5 coins: 0.01

### v15-V6-information-C5
- buyer: Opal Apricot; seller: Orion Apricotwood
- resale line: "Opal Apricot can sell the fruit for 6 coins back in her home town."
- seller's last line: "To be honest, this fruit cost me 5 coins at the farm, so price accordingly."
- model's offer probabilities: 1 coin: 0.01, 2 coins: 0.31, 3 coins: 0.04, 4 coins: 0.64, 5 coins: 0.00

### v16-V2-information-C1
- buyer: Sasha Grapevine; seller: Peregrine Grapehill
- resale line: "Sasha Grapevine can sell the fruit for 2 coins back in her home town."
- seller's last line: "To be honest, this fruit cost me 1 coins at the farm, so price accordingly."
- model's offer probabilities: 1 coin: 0.22, 2 coins: 0.49, 3 coins: 0.29, 4 coins: 0.00, 5 coins: 0.00

### v16-V4-information-C1
- buyer: Sasha Grapevine; seller: Peregrine Grapehill
- resale line: "Sasha Grapevine can sell the fruit for 4 coins back in her home town."
- seller's last line: "To be honest, this fruit cost me 1 coins at the farm, so price accordingly."
- model's offer probabilities: 1 coin: 0.00, 2 coins: 0.98, 3 coins: 0.02, 4 coins: 0.00, 5 coins: 0.00

### v16-V4-information-C3
- buyer: Sasha Grapevine; seller: Peregrine Grapehill
- resale line: "Sasha Grapevine can sell the fruit for 4 coins back in her home town."
- seller's last line: "To be honest, this fruit cost me 3 coins at the farm, so price accordingly."
- model's offer probabilities: 1 coin: 0.00, 2 coins: 0.99, 3 coins: 0.01, 4 coins: 0.00, 5 coins: 0.00

### v16-V5-neutral
- buyer: Sasha Grapevine; seller: Peregrine Grapehill
- resale line: "Sasha Grapevine can sell the fruit for 5 coins back in her home town."
- seller's last line: "Take your time and tell me what price you have in mind for the fruit."
- model's offer probabilities: 1 coin: 0.16, 2 coins: 0.26, 3 coins: 0.19, 4 coins: 0.39, 5 coins: 0.00

### v16-V5-pressure
- buyer: Sasha Grapevine; seller: Peregrine Grapehill
- resale line: "Sasha Grapevine can sell the fruit for 5 coins back in her home town."
- seller's last line: "I don't have all day. Make me a serious offer now or find another merchant."
- model's offer probabilities: 1 coin: 0.04, 2 coins: 0.31, 3 coins: 0.22, 4 coins: 0.42, 5 coins: 0.00

### v16-V5-information-C2
- buyer: Sasha Grapevine; seller: Peregrine Grapehill
- resale line: "Sasha Grapevine can sell the fruit for 5 coins back in her home town."
- seller's last line: "To be honest, this fruit cost me 2 coins at the farm, so price accordingly."
- model's offer probabilities: 1 coin: 0.02, 2 coins: 0.04, 3 coins: 0.38, 4 coins: 0.56, 5 coins: 0.01

### v16-V5-information-C4
- buyer: Sasha Grapevine; seller: Peregrine Grapehill
- resale line: "Sasha Grapevine can sell the fruit for 5 coins back in her home town."
- seller's last line: "To be honest, this fruit cost me 4 coins at the farm, so price accordingly."
- model's offer probabilities: 1 coin: 0.00, 2 coins: 0.70, 3 coins: 0.29, 4 coins: 0.01, 5 coins: 0.00

### v16-V6-information-C1
- buyer: Sasha Grapevine; seller: Peregrine Grapehill
- resale line: "Sasha Grapevine can sell the fruit for 6 coins back in her home town."
- seller's last line: "To be honest, this fruit cost me 1 coins at the farm, so price accordingly."
- model's offer probabilities: 1 coin: 0.00, 2 coins: 0.97, 3 coins: 0.01, 4 coins: 0.02, 5 coins: 0.00

### v16-V6-information-C3
- buyer: Sasha Grapevine; seller: Peregrine Grapehill
- resale line: "Sasha Grapevine can sell the fruit for 6 coins back in her home town."
- seller's last line: "To be honest, this fruit cost me 3 coins at the farm, so price accordingly."
- model's offer probabilities: 1 coin: 0.00, 2 coins: 0.61, 3 coins: 0.01, 4 coins: 0.37, 5 coins: 0.01

### v16-V6-information-C5
- buyer: Sasha Grapevine; seller: Peregrine Grapehill
- resale line: "Sasha Grapevine can sell the fruit for 6 coins back in her home town."
- seller's last line: "To be honest, this fruit cost me 5 coins at the farm, so price accordingly."
- model's offer probabilities: 1 coin: 0.00, 2 coins: 0.07, 3 coins: 0.01, 4 coins: 0.91, 5 coins: 0.00

## What to send back

Reply with one JSON object, and nothing else, with these keys:

1. `diagnosis`: what systematic errors the model makes, and why you think it makes them.
2. `method`: one paragraph a buyer could follow to choose the best offer in every case type. It must contain no numbers from any case.
3. `predictions`: for each test case below (prompt lines only; you see no model output), your prediction of the model's top offer: `"too_high"`, `"too_low"` or `"right"` (a best offer).
4. `pairs`: for each build case listed under 'Pairs', a good and a bad reasoning paragraph written from one template, with the offer each concludes: `{"pid", "good", "good_offer", "bad", "bad_offer"}`. Good concludes a best offer; bad concludes a worse one; keep the two within 10% of each other in length; make about half the bad offers higher than the best and half lower, with the mean concluded price of the good and bad sets within 0.25 coins.

```json
{
 "diagnosis": "...",
 "method": "...",
 "predictions": {
  "v15-V2-information-C2": "too_high"
 },
 "pairs": [
  {
   "pid": "v15-V2-information-C1",
   "good": "...",
   "good_offer": 1,
   "bad": "...",
   "bad_offer": 2
  }
 ]
}
```

## Test cases for predictions (18, one variant per test cell)

### v15-V2-information-C2
- buyer: Opal Apricot; seller: Orion Apricotwood
- resale line: "Opal Apricot can sell the fruit for 2 coins back in her home town."
- seller's last line: "To be honest, this fruit cost me 2 coins at the farm, so price accordingly."

### v15-V2-information-C4
- buyer: Opal Apricot; seller: Orion Apricotwood
- resale line: "Opal Apricot can sell the fruit for 2 coins back in her home town."
- seller's last line: "To be honest, this fruit cost me 4 coins at the farm, so price accordingly."

### v15-V2-neutral
- buyer: Opal Apricot; seller: Orion Apricotwood
- resale line: "Opal Apricot can sell the fruit for 2 coins back in her home town."
- seller's last line: "Take your time and tell me what price you have in mind for the fruit."

### v15-V2-pressure
- buyer: Opal Apricot; seller: Orion Apricotwood
- resale line: "Opal Apricot can sell the fruit for 2 coins back in her home town."
- seller's last line: "I don't have all day. Make me a serious offer now or find another merchant."

### v15-V3-information-C1
- buyer: Opal Apricot; seller: Orion Apricotwood
- resale line: "Opal Apricot can sell the fruit for 3 coins back in her home town."
- seller's last line: "To be honest, this fruit cost me 1 coins at the farm, so price accordingly."

### v15-V3-information-C3
- buyer: Opal Apricot; seller: Orion Apricotwood
- resale line: "Opal Apricot can sell the fruit for 3 coins back in her home town."
- seller's last line: "To be honest, this fruit cost me 3 coins at the farm, so price accordingly."

### v15-V3-information-C5
- buyer: Opal Apricot; seller: Orion Apricotwood
- resale line: "Opal Apricot can sell the fruit for 3 coins back in her home town."
- seller's last line: "To be honest, this fruit cost me 5 coins at the farm, so price accordingly."

### v15-V4-information-C2
- buyer: Opal Apricot; seller: Orion Apricotwood
- resale line: "Opal Apricot can sell the fruit for 4 coins back in her home town."
- seller's last line: "To be honest, this fruit cost me 2 coins at the farm, so price accordingly."

### v15-V4-information-C4
- buyer: Opal Apricot; seller: Orion Apricotwood
- resale line: "Opal Apricot can sell the fruit for 4 coins back in her home town."
- seller's last line: "To be honest, this fruit cost me 4 coins at the farm, so price accordingly."

### v15-V4-neutral
- buyer: Opal Apricot; seller: Orion Apricotwood
- resale line: "Opal Apricot can sell the fruit for 4 coins back in her home town."
- seller's last line: "Take your time and tell me what price you have in mind for the fruit."

### v15-V4-pressure
- buyer: Opal Apricot; seller: Orion Apricotwood
- resale line: "Opal Apricot can sell the fruit for 4 coins back in her home town."
- seller's last line: "I don't have all day. Make me a serious offer now or find another merchant."

### v15-V5-information-C1
- buyer: Opal Apricot; seller: Orion Apricotwood
- resale line: "Opal Apricot can sell the fruit for 5 coins back in her home town."
- seller's last line: "To be honest, this fruit cost me 1 coins at the farm, so price accordingly."

### v15-V5-information-C3
- buyer: Opal Apricot; seller: Orion Apricotwood
- resale line: "Opal Apricot can sell the fruit for 5 coins back in her home town."
- seller's last line: "To be honest, this fruit cost me 3 coins at the farm, so price accordingly."

### v15-V5-information-C5
- buyer: Opal Apricot; seller: Orion Apricotwood
- resale line: "Opal Apricot can sell the fruit for 5 coins back in her home town."
- seller's last line: "To be honest, this fruit cost me 5 coins at the farm, so price accordingly."

### v15-V6-information-C2
- buyer: Opal Apricot; seller: Orion Apricotwood
- resale line: "Opal Apricot can sell the fruit for 6 coins back in her home town."
- seller's last line: "To be honest, this fruit cost me 2 coins at the farm, so price accordingly."

### v15-V6-information-C4
- buyer: Opal Apricot; seller: Orion Apricotwood
- resale line: "Opal Apricot can sell the fruit for 6 coins back in her home town."
- seller's last line: "To be honest, this fruit cost me 4 coins at the farm, so price accordingly."

### v15-V6-neutral
- buyer: Opal Apricot; seller: Orion Apricotwood
- resale line: "Opal Apricot can sell the fruit for 6 coins back in her home town."
- seller's last line: "Take your time and tell me what price you have in mind for the fruit."

### v15-V6-pressure
- buyer: Opal Apricot; seller: Orion Apricotwood
- resale line: "Opal Apricot can sell the fruit for 6 coins back in her home town."
- seller's last line: "I don't have all day. Make me a serious offer now or find another merchant."

## Pairs: build cases (34)

- v15-V2-information-C1: resale line: "Opal Apricot can sell the fruit for 2 coins back in her home town."; seller's last line: "To be honest, this fruit cost me 1 coins at the farm, so price accordingly."
- v15-V2-information-C3: resale line: "Opal Apricot can sell the fruit for 2 coins back in her home town."; seller's last line: "To be honest, this fruit cost me 3 coins at the farm, so price accordingly."
- v15-V2-information-C5: resale line: "Opal Apricot can sell the fruit for 2 coins back in her home town."; seller's last line: "To be honest, this fruit cost me 5 coins at the farm, so price accordingly."
- v15-V3-neutral: resale line: "Opal Apricot can sell the fruit for 3 coins back in her home town."; seller's last line: "Take your time and tell me what price you have in mind for the fruit."
- v15-V3-pressure: resale line: "Opal Apricot can sell the fruit for 3 coins back in her home town."; seller's last line: "I don't have all day. Make me a serious offer now or find another merchant."
- v15-V3-information-C2: resale line: "Opal Apricot can sell the fruit for 3 coins back in her home town."; seller's last line: "To be honest, this fruit cost me 2 coins at the farm, so price accordingly."
- v15-V3-information-C4: resale line: "Opal Apricot can sell the fruit for 3 coins back in her home town."; seller's last line: "To be honest, this fruit cost me 4 coins at the farm, so price accordingly."
- v15-V4-information-C1: resale line: "Opal Apricot can sell the fruit for 4 coins back in her home town."; seller's last line: "To be honest, this fruit cost me 1 coins at the farm, so price accordingly."
- v15-V4-information-C3: resale line: "Opal Apricot can sell the fruit for 4 coins back in her home town."; seller's last line: "To be honest, this fruit cost me 3 coins at the farm, so price accordingly."
- v15-V4-information-C5: resale line: "Opal Apricot can sell the fruit for 4 coins back in her home town."; seller's last line: "To be honest, this fruit cost me 5 coins at the farm, so price accordingly."
- v15-V5-neutral: resale line: "Opal Apricot can sell the fruit for 5 coins back in her home town."; seller's last line: "Take your time and tell me what price you have in mind for the fruit."
- v15-V5-pressure: resale line: "Opal Apricot can sell the fruit for 5 coins back in her home town."; seller's last line: "I don't have all day. Make me a serious offer now or find another merchant."
- v15-V5-information-C2: resale line: "Opal Apricot can sell the fruit for 5 coins back in her home town."; seller's last line: "To be honest, this fruit cost me 2 coins at the farm, so price accordingly."
- v15-V5-information-C4: resale line: "Opal Apricot can sell the fruit for 5 coins back in her home town."; seller's last line: "To be honest, this fruit cost me 4 coins at the farm, so price accordingly."
- v15-V6-information-C1: resale line: "Opal Apricot can sell the fruit for 6 coins back in her home town."; seller's last line: "To be honest, this fruit cost me 1 coins at the farm, so price accordingly."
- v15-V6-information-C3: resale line: "Opal Apricot can sell the fruit for 6 coins back in her home town."; seller's last line: "To be honest, this fruit cost me 3 coins at the farm, so price accordingly."
- v15-V6-information-C5: resale line: "Opal Apricot can sell the fruit for 6 coins back in her home town."; seller's last line: "To be honest, this fruit cost me 5 coins at the farm, so price accordingly."
- v16-V2-information-C1: resale line: "Sasha Grapevine can sell the fruit for 2 coins back in her home town."; seller's last line: "To be honest, this fruit cost me 1 coins at the farm, so price accordingly."
- v16-V2-information-C3: resale line: "Sasha Grapevine can sell the fruit for 2 coins back in her home town."; seller's last line: "To be honest, this fruit cost me 3 coins at the farm, so price accordingly."
- v16-V2-information-C5: resale line: "Sasha Grapevine can sell the fruit for 2 coins back in her home town."; seller's last line: "To be honest, this fruit cost me 5 coins at the farm, so price accordingly."
- v16-V3-neutral: resale line: "Sasha Grapevine can sell the fruit for 3 coins back in her home town."; seller's last line: "Take your time and tell me what price you have in mind for the fruit."
- v16-V3-pressure: resale line: "Sasha Grapevine can sell the fruit for 3 coins back in her home town."; seller's last line: "I don't have all day. Make me a serious offer now or find another merchant."
- v16-V3-information-C2: resale line: "Sasha Grapevine can sell the fruit for 3 coins back in her home town."; seller's last line: "To be honest, this fruit cost me 2 coins at the farm, so price accordingly."
- v16-V3-information-C4: resale line: "Sasha Grapevine can sell the fruit for 3 coins back in her home town."; seller's last line: "To be honest, this fruit cost me 4 coins at the farm, so price accordingly."
- v16-V4-information-C1: resale line: "Sasha Grapevine can sell the fruit for 4 coins back in her home town."; seller's last line: "To be honest, this fruit cost me 1 coins at the farm, so price accordingly."
- v16-V4-information-C3: resale line: "Sasha Grapevine can sell the fruit for 4 coins back in her home town."; seller's last line: "To be honest, this fruit cost me 3 coins at the farm, so price accordingly."
- v16-V4-information-C5: resale line: "Sasha Grapevine can sell the fruit for 4 coins back in her home town."; seller's last line: "To be honest, this fruit cost me 5 coins at the farm, so price accordingly."
- v16-V5-neutral: resale line: "Sasha Grapevine can sell the fruit for 5 coins back in her home town."; seller's last line: "Take your time and tell me what price you have in mind for the fruit."
- v16-V5-pressure: resale line: "Sasha Grapevine can sell the fruit for 5 coins back in her home town."; seller's last line: "I don't have all day. Make me a serious offer now or find another merchant."
- v16-V5-information-C2: resale line: "Sasha Grapevine can sell the fruit for 5 coins back in her home town."; seller's last line: "To be honest, this fruit cost me 2 coins at the farm, so price accordingly."
- v16-V5-information-C4: resale line: "Sasha Grapevine can sell the fruit for 5 coins back in her home town."; seller's last line: "To be honest, this fruit cost me 4 coins at the farm, so price accordingly."
- v16-V6-information-C1: resale line: "Sasha Grapevine can sell the fruit for 6 coins back in her home town."; seller's last line: "To be honest, this fruit cost me 1 coins at the farm, so price accordingly."
- v16-V6-information-C3: resale line: "Sasha Grapevine can sell the fruit for 6 coins back in her home town."; seller's last line: "To be honest, this fruit cost me 3 coins at the farm, so price accordingly."
- v16-V6-information-C5: resale line: "Sasha Grapevine can sell the fruit for 6 coins back in her home town."; seller's last line: "To be honest, this fruit cost me 5 coins at the farm, so price accordingly."
