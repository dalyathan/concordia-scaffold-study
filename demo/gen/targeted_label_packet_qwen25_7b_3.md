# Packet: choose the offer in each case

You are helping to build training material for a language model that plays a buyer in a small haggling game. Read everything, then answer with ONE JSON object and nothing else.

## The game
A buyer wants to buy fruit from a seller and can resell it for a known value (in coins) in her home town. The buyer chooses one of five prices to offer; the five prices are shown as lettered options and may differ between cases (for example 1 to 5 coins or 3 to 7 coins). The seller accepts an offer if it is at or above the seller's own farm cost and refuses a lower offer. If the offer is accepted, the buyer's profit is the resale value minus the offer (it can be negative); if it is refused, the profit is zero. When the seller says what the fruit cost at the farm, that is true. When no cost is stated, the prompt says that every whole-number farm cost between two stated limits is equally likely. The buyer wants the highest expected profit.

## The cases
Below are 83 separate cases. Each case lists the resale value, the five prices the buyer may offer (exactly these five), a line about typical prices, the line about what sellers at this market pay at the farm, and the seller's last line. Cases are independent of each other.

### t201
- Value line: "The buyer can sell the fruit for 7 coins back in her home town."
- Listed prices: 2 coins, 4 coins, 6 coins, 8 coins, 10 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 2 coins is really cheap and 10 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 3 and 7 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Whenever you are ready, say what you would pay for it."

### t202
- Value line: "The buyer can sell the fruit for 14 coins back in her home town."
- Listed prices: 4 coins, 5 coins, 6 coins, 7 coins, 8 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 4 coins is really cheap and 8 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 5 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "No rush. What would you like to offer for the fruit?"

### t203
- Value line: "The buyer can sell the fruit for 11 coins back in her home town."
- Listed prices: 3 coins, 4 coins, 5 coins, 6 coins, 7 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 5 coins. 3 coins is really cheap and 7 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Time is money here. Put a serious price on the table now, or I'll sell elsewhere."

### t204
- Value line: "The buyer can sell the fruit for 4 coins back in her home town."
- Listed prices: 4 coins, 5 coins, 6 coins, 7 coins, 8 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 4 coins is really cheap and 8 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Go ahead, tell me what price you are thinking of for this fruit."

### t205
- Value line: "The buyer can sell the fruit for 14 coins back in her home town."
- Listed prices: 3 coins, 4 coins, 5 coins, 6 coins, 7 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 5 coins. 3 coins is really cheap and 7 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 5 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Between us, the farm charged me 4 coins for it. Let that guide your offer."

### t206
- Value line: "The buyer can sell the fruit for 14 coins back in her home town."
- Listed prices: 2 coins, 4 coins, 6 coins, 8 coins, 10 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 2 coins is really cheap and 10 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 6 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "I'm busy, so make your best offer immediately or I'll move on to the next customer."

### t207
- Value line: "The buyer can sell the fruit for 5 coins back in her home town."
- Listed prices: 4 coins, 5 coins, 6 coins, 7 coins, 8 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 4 coins is really cheap and 8 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 3 and 7 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Go ahead, tell me what price you are thinking of for this fruit."

### t208
- Value line: "The buyer can sell the fruit for 14 coins back in her home town."
- Listed prices: 3 coins, 4 coins, 5 coins, 6 coins, 7 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 5 coins. 3 coins is really cheap and 7 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 6 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Between us, the farm charged me 3 coins for it. Let that guide your offer."

### t209
- Value line: "The buyer can sell the fruit for 15 coins back in her home town."
- Listed prices: 4 coins, 5 coins, 6 coins, 7 coins, 8 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 4 coins is really cheap and 8 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 3 and 7 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "I'll be straight with you: I paid 1 coin for this fruit at the farm, so keep that in mind when you name a price."

### t210
- Value line: "The buyer can sell the fruit for 12 coins back in her home town."
- Listed prices: 4 coins, 5 coins, 6 coins, 7 coins, 8 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 4 coins is really cheap and 8 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "I'll be straight with you: I paid 2 coins for this fruit at the farm, so keep that in mind when you name a price."

### t211
- Value line: "The buyer can sell the fruit for 12 coins back in her home town."
- Listed prices: 2 coins, 4 coins, 6 coins, 8 coins, 10 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 2 coins is really cheap and 10 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 3 and 7 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "I'll be straight with you: I paid 4 coins for this fruit at the farm, so keep that in mind when you name a price."

### t212
- Value line: "The buyer can sell the fruit for 14 coins back in her home town."
- Listed prices: 1 coin, 2 coins, 3 coins, 4 coins, 5 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 3 coins. 1 coin is really cheap and 5 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 3 and 7 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Whenever you are ready, say what you would pay for it."

### t213
- Value line: "The buyer can sell the fruit for 12 coins back in her home town."
- Listed prices: 8 coins, 10 coins, 12 coins, 14 coins, 16 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 12 coins. 8 coins is really cheap and 16 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "For your information, I paid 2 coins for this fruit at the farm. Bear that in mind when you make your offer."

### t214
- Value line: "The buyer can sell the fruit for 6 coins back in her home town."
- Listed prices: 8 coins, 10 coins, 12 coins, 14 coins, 16 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 12 coins. 8 coins is really cheap and 16 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "No rush. What would you like to offer for the fruit?"

### t215
- Value line: "The buyer can sell the fruit for 6 coins back in her home town."
- Listed prices: 8 coins, 10 coins, 12 coins, 14 coins, 16 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 12 coins. 8 coins is really cheap and 16 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "I'm listening. What price do you have in mind for the fruit?"

### t216
- Value line: "The buyer can sell the fruit for 14 coins back in her home town."
- Listed prices: 1 coin, 2 coins, 3 coins, 4 coins, 5 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 3 coins. 1 coin is really cheap and 5 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Whenever you are ready, say what you would pay for it."

### t217
- Value line: "The buyer can sell the fruit for 12 coins back in her home town."
- Listed prices: 3 coins, 4 coins, 5 coins, 6 coins, 7 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 5 coins. 3 coins is really cheap and 7 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 6 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "For your information, I paid 5 coins for this fruit at the farm. Bear that in mind when you make your offer."

### t218
- Value line: "The buyer can sell the fruit for 12 coins back in her home town."
- Listed prices: 3 coins, 4 coins, 5 coins, 6 coins, 7 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 5 coins. 3 coins is really cheap and 7 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 5 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Make it quick: name a serious price now or I turn to the next customer in line."

### t219
- Value line: "The buyer can sell the fruit for 13 coins back in her home town."
- Listed prices: 2 coins, 4 coins, 6 coins, 8 coins, 10 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 2 coins is really cheap and 10 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "No rush. What would you like to offer for the fruit?"

### t220
- Value line: "The buyer can sell the fruit for 14 coins back in her home town."
- Listed prices: 8 coins, 10 coins, 12 coins, 14 coins, 16 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 12 coins. 8 coins is really cheap and 16 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "I'll be straight with you: I paid 5 coins for this fruit at the farm, so keep that in mind when you name a price."

### t221
- Value line: "The buyer can sell the fruit for 15 coins back in her home town."
- Listed prices: 4 coins, 5 coins, 6 coins, 7 coins, 8 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 4 coins is really cheap and 8 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 3 and 7 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Between us, the farm charged me 6 coins for it. Let that guide your offer."

### t222
- Value line: "The buyer can sell the fruit for 4 coins back in her home town."
- Listed prices: 8 coins, 10 coins, 12 coins, 14 coins, 16 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 12 coins. 8 coins is really cheap and 16 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Time is money here. Put a serious price on the table now, or I'll sell elsewhere."

### t223
- Value line: "The buyer can sell the fruit for 11 coins back in her home town."
- Listed prices: 3 coins, 4 coins, 5 coins, 6 coins, 7 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 5 coins. 3 coins is really cheap and 7 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 6 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "No rush. What would you like to offer for the fruit?"

### t224
- Value line: "The buyer can sell the fruit for 3 coins back in her home town."
- Listed prices: 2 coins, 4 coins, 6 coins, 8 coins, 10 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 2 coins is really cheap and 10 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 5 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Time is money here. Put a serious price on the table now, or I'll sell elsewhere."

### t225
- Value line: "The buyer can sell the fruit for 2 coins back in her home town."
- Listed prices: 2 coins, 4 coins, 6 coins, 8 coins, 10 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 2 coins is really cheap and 10 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "I'm listening. What price do you have in mind for the fruit?"

### t226
- Value line: "The buyer can sell the fruit for 14 coins back in her home town."
- Listed prices: 2 coins, 4 coins, 6 coins, 8 coins, 10 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 2 coins is really cheap and 10 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 3 and 7 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Full disclosure, my cost at the farm was 9 coins. Name your price with that in mind."

### t227
- Value line: "The buyer can sell the fruit for 11 coins back in her home town."
- Listed prices: 2 coins, 4 coins, 6 coins, 8 coins, 10 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 2 coins is really cheap and 10 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 5 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "No rush. What would you like to offer for the fruit?"

### t228
- Value line: "The buyer can sell the fruit for 11 coins back in her home town."
- Listed prices: 8 coins, 10 coins, 12 coins, 14 coins, 16 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 12 coins. 8 coins is really cheap and 16 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 6 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "I'll be straight with you: I paid 8 coins for this fruit at the farm, so keep that in mind when you name a price."

### t229
- Value line: "The buyer can sell the fruit for 12 coins back in her home town."
- Listed prices: 3 coins, 4 coins, 5 coins, 6 coins, 7 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 5 coins. 3 coins is really cheap and 7 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 3 and 7 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Go ahead, tell me what price you are thinking of for this fruit."

### t230
- Value line: "The buyer can sell the fruit for 10 coins back in her home town."
- Listed prices: 2 coins, 4 coins, 6 coins, 8 coins, 10 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 2 coins is really cheap and 10 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 3 and 7 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "There are other buyers waiting. Give me a real offer right now or step aside."

### t231
- Value line: "The buyer can sell the fruit for 13 coins back in her home town."
- Listed prices: 8 coins, 10 coins, 12 coins, 14 coins, 16 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 12 coins. 8 coins is really cheap and 16 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Full disclosure, my cost at the farm was 4 coins. Name your price with that in mind."

### t232
- Value line: "The buyer can sell the fruit for 14 coins back in her home town."
- Listed prices: 2 coins, 4 coins, 6 coins, 8 coins, 10 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 2 coins is really cheap and 10 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 5 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "For your information, I paid 1 coin for this fruit at the farm. Bear that in mind when you make your offer."

### t233
- Value line: "The buyer can sell the fruit for 13 coins back in her home town."
- Listed prices: 2 coins, 4 coins, 6 coins, 8 coins, 10 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 2 coins is really cheap and 10 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 3 and 7 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "I'll be straight with you: I paid 3 coins for this fruit at the farm, so keep that in mind when you name a price."

### t234
- Value line: "The buyer can sell the fruit for 10 coins back in her home town."
- Listed prices: 2 coins, 4 coins, 6 coins, 8 coins, 10 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 2 coins is really cheap and 10 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 3 and 7 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Between us, the farm charged me 3 coins for it. Let that guide your offer."

### t235
- Value line: "The buyer can sell the fruit for 10 coins back in her home town."
- Listed prices: 4 coins, 5 coins, 6 coins, 7 coins, 8 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 4 coins is really cheap and 8 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 6 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "I'm busy, so make your best offer immediately or I'll move on to the next customer."

### t236
- Value line: "The buyer can sell the fruit for 12 coins back in her home town."
- Listed prices: 4 coins, 5 coins, 6 coins, 7 coins, 8 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 4 coins is really cheap and 8 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 5 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "I'll be straight with you: I paid 6 coins for this fruit at the farm, so keep that in mind when you name a price."

### t237
- Value line: "The buyer can sell the fruit for 14 coins back in her home town."
- Listed prices: 2 coins, 3 coins, 4 coins, 5 coins, 6 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 4 coins. 2 coins is really cheap and 6 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 3 and 7 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Whenever you are ready, say what you would pay for it."

### t238
- Value line: "The buyer can sell the fruit for 14 coins back in her home town."
- Listed prices: 2 coins, 4 coins, 6 coins, 8 coins, 10 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 2 coins is really cheap and 10 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 5 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Between us, the farm charged me 6 coins for it. Let that guide your offer."

### t239
- Value line: "The buyer can sell the fruit for 7 coins back in her home town."
- Listed prices: 8 coins, 10 coins, 12 coins, 14 coins, 16 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 12 coins. 8 coins is really cheap and 16 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "No rush. What would you like to offer for the fruit?"

### t240
- Value line: "The buyer can sell the fruit for 15 coins back in her home town."
- Listed prices: 2 coins, 4 coins, 6 coins, 8 coins, 10 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 2 coins is really cheap and 10 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 3 and 7 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Full disclosure, my cost at the farm was 9 coins. Name your price with that in mind."

### t241
- Value line: "The buyer can sell the fruit for 15 coins back in her home town."
- Listed prices: 1 coin, 2 coins, 3 coins, 4 coins, 5 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 3 coins. 1 coin is really cheap and 5 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Full disclosure, my cost at the farm was 2 coins. Name your price with that in mind."

### t242
- Value line: "The buyer can sell the fruit for 14 coins back in her home town."
- Listed prices: 2 coins, 4 coins, 6 coins, 8 coins, 10 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 2 coins is really cheap and 10 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 3 and 7 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "No rush. What would you like to offer for the fruit?"

### t243
- Value line: "The buyer can sell the fruit for 14 coins back in her home town."
- Listed prices: 8 coins, 10 coins, 12 coins, 14 coins, 16 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 12 coins. 8 coins is really cheap and 16 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 5 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "There are other buyers waiting. Give me a real offer right now or step aside."

### t244
- Value line: "The buyer can sell the fruit for 15 coins back in her home town."
- Listed prices: 2 coins, 4 coins, 6 coins, 8 coins, 10 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 2 coins is really cheap and 10 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 3 and 7 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Go ahead, tell me what price you are thinking of for this fruit."

### t245
- Value line: "The buyer can sell the fruit for 2 coins back in her home town."
- Listed prices: 2 coins, 4 coins, 6 coins, 8 coins, 10 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 2 coins is really cheap and 10 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 3 and 7 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Go ahead, tell me what price you are thinking of for this fruit."

### t246
- Value line: "The buyer can sell the fruit for 4 coins back in her home town."
- Listed prices: 4 coins, 5 coins, 6 coins, 7 coins, 8 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 4 coins is really cheap and 8 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 5 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Whenever you are ready, say what you would pay for it."

### t247
- Value line: "The buyer can sell the fruit for 13 coins back in her home town."
- Listed prices: 3 coins, 4 coins, 5 coins, 6 coins, 7 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 5 coins. 3 coins is really cheap and 7 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 5 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "For your information, I paid 5 coins for this fruit at the farm. Bear that in mind when you make your offer."

### t248
- Value line: "The buyer can sell the fruit for 15 coins back in her home town."
- Listed prices: 8 coins, 10 coins, 12 coins, 14 coins, 16 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 12 coins. 8 coins is really cheap and 16 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 6 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Go ahead, tell me what price you are thinking of for this fruit."

### t249
- Value line: "The buyer can sell the fruit for 14 coins back in her home town."
- Listed prices: 2 coins, 4 coins, 6 coins, 8 coins, 10 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 2 coins is really cheap and 10 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Between us, the farm charged me 4 coins for it. Let that guide your offer."

### t250
- Value line: "The buyer can sell the fruit for 10 coins back in her home town."
- Listed prices: 1 coin, 2 coins, 3 coins, 4 coins, 5 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 3 coins. 1 coin is really cheap and 5 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "I'm busy, so make your best offer immediately or I'll move on to the next customer."

### t251
- Value line: "The buyer can sell the fruit for 14 coins back in her home town."
- Listed prices: 4 coins, 5 coins, 6 coins, 7 coins, 8 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 4 coins is really cheap and 8 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 6 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "I'll be straight with you: I paid 8 coins for this fruit at the farm, so keep that in mind when you name a price."

### t252
- Value line: "The buyer can sell the fruit for 14 coins back in her home town."
- Listed prices: 8 coins, 10 coins, 12 coins, 14 coins, 16 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 12 coins. 8 coins is really cheap and 16 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Full disclosure, my cost at the farm was 7 coins. Name your price with that in mind."

### t253
- Value line: "The buyer can sell the fruit for 11 coins back in her home town."
- Listed prices: 3 coins, 4 coins, 5 coins, 6 coins, 7 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 5 coins. 3 coins is really cheap and 7 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "I'll be straight with you: I paid 3 coins for this fruit at the farm, so keep that in mind when you name a price."

### t254
- Value line: "The buyer can sell the fruit for 14 coins back in her home town."
- Listed prices: 1 coin, 2 coins, 3 coins, 4 coins, 5 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 3 coins. 1 coin is really cheap and 5 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 5 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "For your information, I paid 5 coins for this fruit at the farm. Bear that in mind when you make your offer."

### t255
- Value line: "The buyer can sell the fruit for 14 coins back in her home town."
- Listed prices: 3 coins, 4 coins, 5 coins, 6 coins, 7 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 5 coins. 3 coins is really cheap and 7 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "I'm busy, so make your best offer immediately or I'll move on to the next customer."

### t256
- Value line: "The buyer can sell the fruit for 12 coins back in her home town."
- Listed prices: 3 coins, 4 coins, 5 coins, 6 coins, 7 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 5 coins. 3 coins is really cheap and 7 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 3 and 7 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Full disclosure, my cost at the farm was 2 coins. Name your price with that in mind."

### t257
- Value line: "The buyer can sell the fruit for 2 coins back in her home town."
- Listed prices: 2 coins, 4 coins, 6 coins, 8 coins, 10 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 2 coins is really cheap and 10 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 6 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Make it quick: name a serious price now or I turn to the next customer in line."

### t258
- Value line: "The buyer can sell the fruit for 13 coins back in her home town."
- Listed prices: 4 coins, 5 coins, 6 coins, 7 coins, 8 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 4 coins is really cheap and 8 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "For your information, I paid 1 coin for this fruit at the farm. Bear that in mind when you make your offer."

### t259
- Value line: "The buyer can sell the fruit for 15 coins back in her home town."
- Listed prices: 3 coins, 4 coins, 5 coins, 6 coins, 7 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 5 coins. 3 coins is really cheap and 7 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 5 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "No rush. What would you like to offer for the fruit?"

### t260
- Value line: "The buyer can sell the fruit for 14 coins back in her home town."
- Listed prices: 4 coins, 5 coins, 6 coins, 7 coins, 8 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 4 coins is really cheap and 8 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Between us, the farm charged me 5 coins for it. Let that guide your offer."

### t261
- Value line: "The buyer can sell the fruit for 13 coins back in her home town."
- Listed prices: 2 coins, 4 coins, 6 coins, 8 coins, 10 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 2 coins is really cheap and 10 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 5 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Make it quick: name a serious price now or I turn to the next customer in line."

### t262
- Value line: "The buyer can sell the fruit for 11 coins back in her home town."
- Listed prices: 3 coins, 4 coins, 5 coins, 6 coins, 7 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 5 coins. 3 coins is really cheap and 7 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Between us, the farm charged me 1 coin for it. Let that guide your offer."

### t263
- Value line: "The buyer can sell the fruit for 12 coins back in her home town."
- Listed prices: 3 coins, 4 coins, 5 coins, 6 coins, 7 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 5 coins. 3 coins is really cheap and 7 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "I'll be straight with you: I paid 7 coins for this fruit at the farm, so keep that in mind when you name a price."

### t264
- Value line: "The buyer can sell the fruit for 15 coins back in her home town."
- Listed prices: 2 coins, 4 coins, 6 coins, 8 coins, 10 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 2 coins is really cheap and 10 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 5 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Make it quick: name a serious price now or I turn to the next customer in line."

### t265
- Value line: "The buyer can sell the fruit for 14 coins back in her home town."
- Listed prices: 2 coins, 3 coins, 4 coins, 5 coins, 6 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 4 coins. 2 coins is really cheap and 6 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 5 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Time is money here. Put a serious price on the table now, or I'll sell elsewhere."

### t266
- Value line: "The buyer can sell the fruit for 15 coins back in her home town."
- Listed prices: 2 coins, 4 coins, 6 coins, 8 coins, 10 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 2 coins is really cheap and 10 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "For your information, I paid 7 coins for this fruit at the farm. Bear that in mind when you make your offer."

### t267
- Value line: "The buyer can sell the fruit for 4 coins back in her home town."
- Listed prices: 2 coins, 4 coins, 6 coins, 8 coins, 10 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 2 coins is really cheap and 10 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Time is money here. Put a serious price on the table now, or I'll sell elsewhere."

### t268
- Value line: "The buyer can sell the fruit for 3 coins back in her home town."
- Listed prices: 1 coin, 2 coins, 3 coins, 4 coins, 5 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 3 coins. 1 coin is really cheap and 5 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "There are other buyers waiting. Give me a real offer right now or step aside."

### t269
- Value line: "The buyer can sell the fruit for 5 coins back in her home town."
- Listed prices: 2 coins, 4 coins, 6 coins, 8 coins, 10 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 2 coins is really cheap and 10 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "There are other buyers waiting. Give me a real offer right now or step aside."

### t270
- Value line: "The buyer can sell the fruit for 3 coins back in her home town."
- Listed prices: 4 coins, 5 coins, 6 coins, 7 coins, 8 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 4 coins is really cheap and 8 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Between us, the farm charged me 2 coins for it. Let that guide your offer."

### t271
- Value line: "The buyer can sell the fruit for 10 coins back in her home town."
- Listed prices: 2 coins, 4 coins, 6 coins, 8 coins, 10 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 2 coins is really cheap and 10 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 5 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Go ahead, tell me what price you are thinking of for this fruit."

### t272
- Value line: "The buyer can sell the fruit for 12 coins back in her home town."
- Listed prices: 8 coins, 10 coins, 12 coins, 14 coins, 16 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 12 coins. 8 coins is really cheap and 16 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Full disclosure, my cost at the farm was 9 coins. Name your price with that in mind."

### t273
- Value line: "The buyer can sell the fruit for 14 coins back in her home town."
- Listed prices: 2 coins, 4 coins, 6 coins, 8 coins, 10 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 2 coins is really cheap and 10 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Go ahead, tell me what price you are thinking of for this fruit."

### t274
- Value line: "The buyer can sell the fruit for 12 coins back in her home town."
- Listed prices: 1 coin, 2 coins, 3 coins, 4 coins, 5 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 3 coins. 1 coin is really cheap and 5 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Go ahead, tell me what price you are thinking of for this fruit."

### t275
- Value line: "The buyer can sell the fruit for 8 coins back in her home town."
- Listed prices: 8 coins, 10 coins, 12 coins, 14 coins, 16 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 12 coins. 8 coins is really cheap and 16 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 6 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Full disclosure, my cost at the farm was 4 coins. Name your price with that in mind."

### t276
- Value line: "The buyer can sell the fruit for 12 coins back in her home town."
- Listed prices: 2 coins, 4 coins, 6 coins, 8 coins, 10 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 2 coins is really cheap and 10 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Full disclosure, my cost at the farm was 10 coins. Name your price with that in mind."

### t277
- Value line: "The buyer can sell the fruit for 13 coins back in her home town."
- Listed prices: 2 coins, 4 coins, 6 coins, 8 coins, 10 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 2 coins is really cheap and 10 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "I'm listening. What price do you have in mind for the fruit?"

### t278
- Value line: "The buyer can sell the fruit for 5 coins back in her home town."
- Listed prices: 4 coins, 5 coins, 6 coins, 7 coins, 8 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 4 coins is really cheap and 8 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 5 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Whenever you are ready, say what you would pay for it."

### t279
- Value line: "The buyer can sell the fruit for 3 coins back in her home town."
- Listed prices: 2 coins, 4 coins, 6 coins, 8 coins, 10 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 2 coins is really cheap and 10 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "No rush. What would you like to offer for the fruit?"

### t280
- Value line: "The buyer can sell the fruit for 10 coins back in her home town."
- Listed prices: 3 coins, 4 coins, 5 coins, 6 coins, 7 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 5 coins. 3 coins is really cheap and 7 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 3 and 7 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Go ahead, tell me what price you are thinking of for this fruit."

### t281
- Value line: "The buyer can sell the fruit for 10 coins back in her home town."
- Listed prices: 3 coins, 4 coins, 5 coins, 6 coins, 7 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 5 coins. 3 coins is really cheap and 7 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 6 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "There are other buyers waiting. Give me a real offer right now or step aside."

### t282
- Value line: "The buyer can sell the fruit for 3 coins back in her home town."
- Listed prices: 8 coins, 10 coins, 12 coins, 14 coins, 16 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 12 coins. 8 coins is really cheap and 16 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 5 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "No rush. What would you like to offer for the fruit?"

### t283
- Value line: "The buyer can sell the fruit for 10 coins back in her home town."
- Listed prices: 3 coins, 4 coins, 5 coins, 6 coins, 7 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 5 coins. 3 coins is really cheap and 7 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "For your information, I paid 4 coins for this fruit at the farm. Bear that in mind when you make your offer."

## What to produce
For each case, decide which ONE of the listed prices the buyer should offer to earn the highest expected profit. Output ONE JSON object whose keys are the case ids (for example "t201") and whose values are the chosen price as a whole number taken from that case's listed prices. Include all 83 ids and nothing else; no commentary.
