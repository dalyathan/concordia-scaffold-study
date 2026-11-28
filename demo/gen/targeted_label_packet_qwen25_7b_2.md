# Packet: choose the offer in each case

You are helping to build training material for a language model that plays a buyer in a small haggling game. Read everything, then answer with ONE JSON object and nothing else.

## The game
A buyer wants to buy fruit from a seller and can resell it for a known value (in coins) in her home town. The buyer chooses one of five prices to offer; the five prices are shown as lettered options and may differ between cases (for example 1 to 5 coins or 3 to 7 coins). The seller accepts an offer if it is at or above the seller's own farm cost and refuses a lower offer. If the offer is accepted, the buyer's profit is the resale value minus the offer (it can be negative); if it is refused, the profit is zero. When the seller says what the fruit cost at the farm, that is true. When no cost is stated, the prompt says that every whole-number farm cost between two stated limits is equally likely. The buyer wants the highest expected profit.

## The cases
Below are 100 separate cases. Each case lists the resale value, the five prices the buyer may offer (exactly these five), a line about typical prices, the line about what sellers at this market pay at the farm, and the seller's last line. Cases are independent of each other.

### t101
- Value line: "The buyer can sell the fruit for 13 coins back in her home town."
- Listed prices: 1 coin, 2 coins, 3 coins, 4 coins, 5 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 3 coins. 1 coin is really cheap and 5 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 6 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "For your information, I paid 2 coins for this fruit at the farm. Bear that in mind when you make your offer."

### t102
- Value line: "The buyer can sell the fruit for 8 coins back in her home town."
- Listed prices: 2 coins, 4 coins, 6 coins, 8 coins, 10 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 2 coins is really cheap and 10 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 6 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Go ahead, tell me what price you are thinking of for this fruit."

### t103
- Value line: "The buyer can sell the fruit for 3 coins back in her home town."
- Listed prices: 8 coins, 10 coins, 12 coins, 14 coins, 16 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 12 coins. 8 coins is really cheap and 16 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Go ahead, tell me what price you are thinking of for this fruit."

### t104
- Value line: "The buyer can sell the fruit for 14 coins back in her home town."
- Listed prices: 4 coins, 5 coins, 6 coins, 7 coins, 8 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 4 coins is really cheap and 8 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 6 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "No rush. What would you like to offer for the fruit?"

### t105
- Value line: "The buyer can sell the fruit for 12 coins back in her home town."
- Listed prices: 4 coins, 5 coins, 6 coins, 7 coins, 8 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 4 coins is really cheap and 8 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 6 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Whenever you are ready, say what you would pay for it."

### t106
- Value line: "The buyer can sell the fruit for 13 coins back in her home town."
- Listed prices: 4 coins, 5 coins, 6 coins, 7 coins, 8 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 4 coins is really cheap and 8 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 3 and 7 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "I'm busy, so make your best offer immediately or I'll move on to the next customer."

### t107
- Value line: "The buyer can sell the fruit for 9 coins back in her home town."
- Listed prices: 8 coins, 10 coins, 12 coins, 14 coins, 16 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 12 coins. 8 coins is really cheap and 16 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 6 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Go ahead, tell me what price you are thinking of for this fruit."

### t108
- Value line: "The buyer can sell the fruit for 15 coins back in her home town."
- Listed prices: 3 coins, 4 coins, 5 coins, 6 coins, 7 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 5 coins. 3 coins is really cheap and 7 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "I'll be straight with you: I paid 4 coins for this fruit at the farm, so keep that in mind when you name a price."

### t109
- Value line: "The buyer can sell the fruit for 7 coins back in her home town."
- Listed prices: 4 coins, 5 coins, 6 coins, 7 coins, 8 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 4 coins is really cheap and 8 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 3 and 7 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Whenever you are ready, say what you would pay for it."

### t110
- Value line: "The buyer can sell the fruit for 4 coins back in her home town."
- Listed prices: 2 coins, 4 coins, 6 coins, 8 coins, 10 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 2 coins is really cheap and 10 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 5 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Time is money here. Put a serious price on the table now, or I'll sell elsewhere."

### t111
- Value line: "The buyer can sell the fruit for 14 coins back in her home town."
- Listed prices: 8 coins, 10 coins, 12 coins, 14 coins, 16 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 12 coins. 8 coins is really cheap and 16 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "I'll be straight with you: I paid 6 coins for this fruit at the farm, so keep that in mind when you name a price."

### t112
- Value line: "The buyer can sell the fruit for 5 coins back in her home town."
- Listed prices: 8 coins, 10 coins, 12 coins, 14 coins, 16 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 12 coins. 8 coins is really cheap and 16 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 3 and 7 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Whenever you are ready, say what you would pay for it."

### t113
- Value line: "The buyer can sell the fruit for 14 coins back in her home town."
- Listed prices: 3 coins, 4 coins, 5 coins, 6 coins, 7 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 5 coins. 3 coins is really cheap and 7 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 3 and 7 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "I'll be straight with you: I paid 5 coins for this fruit at the farm, so keep that in mind when you name a price."

### t114
- Value line: "The buyer can sell the fruit for 11 coins back in her home town."
- Listed prices: 1 coin, 2 coins, 3 coins, 4 coins, 5 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 3 coins. 1 coin is really cheap and 5 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 3 and 7 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Between us, the farm charged me 4 coins for it. Let that guide your offer."

### t115
- Value line: "The buyer can sell the fruit for 10 coins back in her home town."
- Listed prices: 2 coins, 3 coins, 4 coins, 5 coins, 6 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 4 coins. 2 coins is really cheap and 6 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 5 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Whenever you are ready, say what you would pay for it."

### t116
- Value line: "The buyer can sell the fruit for 15 coins back in her home town."
- Listed prices: 3 coins, 4 coins, 5 coins, 6 coins, 7 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 5 coins. 3 coins is really cheap and 7 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Make it quick: name a serious price now or I turn to the next customer in line."

### t117
- Value line: "The buyer can sell the fruit for 9 coins back in her home town."
- Listed prices: 4 coins, 5 coins, 6 coins, 7 coins, 8 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 4 coins is really cheap and 8 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "I'm listening. What price do you have in mind for the fruit?"

### t118
- Value line: "The buyer can sell the fruit for 3 coins back in her home town."
- Listed prices: 4 coins, 5 coins, 6 coins, 7 coins, 8 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 4 coins is really cheap and 8 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "For your information, I paid 1 coin for this fruit at the farm. Bear that in mind when you make your offer."

### t119
- Value line: "The buyer can sell the fruit for 8 coins back in her home town."
- Listed prices: 4 coins, 5 coins, 6 coins, 7 coins, 8 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 4 coins is really cheap and 8 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 6 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Go ahead, tell me what price you are thinking of for this fruit."

### t120
- Value line: "The buyer can sell the fruit for 15 coins back in her home town."
- Listed prices: 1 coin, 2 coins, 3 coins, 4 coins, 5 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 3 coins. 1 coin is really cheap and 5 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 3 and 7 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "I'm busy, so make your best offer immediately or I'll move on to the next customer."

### t121
- Value line: "The buyer can sell the fruit for 13 coins back in her home town."
- Listed prices: 2 coins, 4 coins, 6 coins, 8 coins, 10 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 2 coins is really cheap and 10 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 3 and 7 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Between us, the farm charged me 1 coin for it. Let that guide your offer."

### t122
- Value line: "The buyer can sell the fruit for 6 coins back in her home town."
- Listed prices: 8 coins, 10 coins, 12 coins, 14 coins, 16 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 12 coins. 8 coins is really cheap and 16 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 5 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Go ahead, tell me what price you are thinking of for this fruit."

### t123
- Value line: "The buyer can sell the fruit for 13 coins back in her home town."
- Listed prices: 2 coins, 4 coins, 6 coins, 8 coins, 10 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 2 coins is really cheap and 10 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Full disclosure, my cost at the farm was 6 coins. Name your price with that in mind."

### t124
- Value line: "The buyer can sell the fruit for 15 coins back in her home town."
- Listed prices: 1 coin, 2 coins, 3 coins, 4 coins, 5 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 3 coins. 1 coin is really cheap and 5 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 6 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Full disclosure, my cost at the farm was 4 coins. Name your price with that in mind."

### t125
- Value line: "The buyer can sell the fruit for 10 coins back in her home town."
- Listed prices: 2 coins, 3 coins, 4 coins, 5 coins, 6 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 4 coins. 2 coins is really cheap and 6 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 6 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Go ahead, tell me what price you are thinking of for this fruit."

### t126
- Value line: "The buyer can sell the fruit for 11 coins back in her home town."
- Listed prices: 8 coins, 10 coins, 12 coins, 14 coins, 16 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 12 coins. 8 coins is really cheap and 16 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 3 and 7 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Go ahead, tell me what price you are thinking of for this fruit."

### t127
- Value line: "The buyer can sell the fruit for 9 coins back in her home town."
- Listed prices: 8 coins, 10 coins, 12 coins, 14 coins, 16 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 12 coins. 8 coins is really cheap and 16 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Go ahead, tell me what price you are thinking of for this fruit."

### t128
- Value line: "The buyer can sell the fruit for 14 coins back in her home town."
- Listed prices: 1 coin, 2 coins, 3 coins, 4 coins, 5 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 3 coins. 1 coin is really cheap and 5 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 5 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "I'm listening. What price do you have in mind for the fruit?"

### t129
- Value line: "The buyer can sell the fruit for 13 coins back in her home town."
- Listed prices: 3 coins, 4 coins, 5 coins, 6 coins, 7 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 5 coins. 3 coins is really cheap and 7 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 5 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Time is money here. Put a serious price on the table now, or I'll sell elsewhere."

### t130
- Value line: "The buyer can sell the fruit for 2 coins back in her home town."
- Listed prices: 4 coins, 5 coins, 6 coins, 7 coins, 8 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 4 coins is really cheap and 8 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "I'm busy, so make your best offer immediately or I'll move on to the next customer."

### t131
- Value line: "The buyer can sell the fruit for 9 coins back in her home town."
- Listed prices: 8 coins, 10 coins, 12 coins, 14 coins, 16 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 12 coins. 8 coins is really cheap and 16 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 3 and 7 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Go ahead, tell me what price you are thinking of for this fruit."

### t132
- Value line: "The buyer can sell the fruit for 6 coins back in her home town."
- Listed prices: 2 coins, 4 coins, 6 coins, 8 coins, 10 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 2 coins is really cheap and 10 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Whenever you are ready, say what you would pay for it."

### t133
- Value line: "The buyer can sell the fruit for 14 coins back in her home town."
- Listed prices: 8 coins, 10 coins, 12 coins, 14 coins, 16 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 12 coins. 8 coins is really cheap and 16 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 5 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Full disclosure, my cost at the farm was 10 coins. Name your price with that in mind."

### t134
- Value line: "The buyer can sell the fruit for 3 coins back in her home town."
- Listed prices: 2 coins, 4 coins, 6 coins, 8 coins, 10 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 2 coins is really cheap and 10 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Go ahead, tell me what price you are thinking of for this fruit."

### t135
- Value line: "The buyer can sell the fruit for 13 coins back in her home town."
- Listed prices: 2 coins, 4 coins, 6 coins, 8 coins, 10 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 2 coins is really cheap and 10 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "I'll be straight with you: I paid 8 coins for this fruit at the farm, so keep that in mind when you name a price."

### t136
- Value line: "The buyer can sell the fruit for 8 coins back in her home town."
- Listed prices: 1 coin, 2 coins, 3 coins, 4 coins, 5 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 3 coins. 1 coin is really cheap and 5 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "For your information, I paid 1 coin for this fruit at the farm. Bear that in mind when you make your offer."

### t137
- Value line: "The buyer can sell the fruit for 5 coins back in her home town."
- Listed prices: 8 coins, 10 coins, 12 coins, 14 coins, 16 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 12 coins. 8 coins is really cheap and 16 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Between us, the farm charged me 7 coins for it. Let that guide your offer."

### t138
- Value line: "The buyer can sell the fruit for 2 coins back in her home town."
- Listed prices: 8 coins, 10 coins, 12 coins, 14 coins, 16 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 12 coins. 8 coins is really cheap and 16 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Whenever you are ready, say what you would pay for it."

### t139
- Value line: "The buyer can sell the fruit for 14 coins back in her home town."
- Listed prices: 2 coins, 4 coins, 6 coins, 8 coins, 10 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 2 coins is really cheap and 10 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Between us, the farm charged me 2 coins for it. Let that guide your offer."

### t140
- Value line: "The buyer can sell the fruit for 9 coins back in her home town."
- Listed prices: 4 coins, 5 coins, 6 coins, 7 coins, 8 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 4 coins is really cheap and 8 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 5 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "I'm listening. What price do you have in mind for the fruit?"

### t141
- Value line: "The buyer can sell the fruit for 14 coins back in her home town."
- Listed prices: 4 coins, 5 coins, 6 coins, 7 coins, 8 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 4 coins is really cheap and 8 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "I'll be straight with you: I paid 1 coin for this fruit at the farm, so keep that in mind when you name a price."

### t142
- Value line: "The buyer can sell the fruit for 10 coins back in her home town."
- Listed prices: 4 coins, 5 coins, 6 coins, 7 coins, 8 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 4 coins is really cheap and 8 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "I'm busy, so make your best offer immediately or I'll move on to the next customer."

### t143
- Value line: "The buyer can sell the fruit for 12 coins back in her home town."
- Listed prices: 2 coins, 4 coins, 6 coins, 8 coins, 10 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 2 coins is really cheap and 10 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Time is money here. Put a serious price on the table now, or I'll sell elsewhere."

### t144
- Value line: "The buyer can sell the fruit for 15 coins back in her home town."
- Listed prices: 8 coins, 10 coins, 12 coins, 14 coins, 16 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 12 coins. 8 coins is really cheap and 16 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Full disclosure, my cost at the farm was 11 coins. Name your price with that in mind."

### t145
- Value line: "The buyer can sell the fruit for 8 coins back in her home town."
- Listed prices: 4 coins, 5 coins, 6 coins, 7 coins, 8 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 4 coins is really cheap and 8 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 5 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Time is money here. Put a serious price on the table now, or I'll sell elsewhere."

### t146
- Value line: "The buyer can sell the fruit for 11 coins back in her home town."
- Listed prices: 8 coins, 10 coins, 12 coins, 14 coins, 16 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 12 coins. 8 coins is really cheap and 16 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 5 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Time is money here. Put a serious price on the table now, or I'll sell elsewhere."

### t147
- Value line: "The buyer can sell the fruit for 13 coins back in her home town."
- Listed prices: 4 coins, 5 coins, 6 coins, 7 coins, 8 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 4 coins is really cheap and 8 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "I'm listening. What price do you have in mind for the fruit?"

### t148
- Value line: "The buyer can sell the fruit for 15 coins back in her home town."
- Listed prices: 3 coins, 4 coins, 5 coins, 6 coins, 7 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 5 coins. 3 coins is really cheap and 7 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 6 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Make it quick: name a serious price now or I turn to the next customer in line."

### t149
- Value line: "The buyer can sell the fruit for 15 coins back in her home town."
- Listed prices: 4 coins, 5 coins, 6 coins, 7 coins, 8 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 4 coins is really cheap and 8 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 5 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Make it quick: name a serious price now or I turn to the next customer in line."

### t150
- Value line: "The buyer can sell the fruit for 8 coins back in her home town."
- Listed prices: 8 coins, 10 coins, 12 coins, 14 coins, 16 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 12 coins. 8 coins is really cheap and 16 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 5 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Time is money here. Put a serious price on the table now, or I'll sell elsewhere."

### t151
- Value line: "The buyer can sell the fruit for 15 coins back in her home town."
- Listed prices: 4 coins, 5 coins, 6 coins, 7 coins, 8 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 4 coins is really cheap and 8 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 6 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Go ahead, tell me what price you are thinking of for this fruit."

### t152
- Value line: "The buyer can sell the fruit for 13 coins back in her home town."
- Listed prices: 2 coins, 3 coins, 4 coins, 5 coins, 6 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 4 coins. 2 coins is really cheap and 6 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Between us, the farm charged me 4 coins for it. Let that guide your offer."

### t153
- Value line: "The buyer can sell the fruit for 13 coins back in her home town."
- Listed prices: 1 coin, 2 coins, 3 coins, 4 coins, 5 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 3 coins. 1 coin is really cheap and 5 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "I'm listening. What price do you have in mind for the fruit?"

### t154
- Value line: "The buyer can sell the fruit for 13 coins back in her home town."
- Listed prices: 8 coins, 10 coins, 12 coins, 14 coins, 16 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 12 coins. 8 coins is really cheap and 16 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 5 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "I'll be straight with you: I paid 9 coins for this fruit at the farm, so keep that in mind when you name a price."

### t155
- Value line: "The buyer can sell the fruit for 8 coins back in her home town."
- Listed prices: 2 coins, 4 coins, 6 coins, 8 coins, 10 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 2 coins is really cheap and 10 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 5 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Full disclosure, my cost at the farm was 3 coins. Name your price with that in mind."

### t156
- Value line: "The buyer can sell the fruit for 6 coins back in her home town."
- Listed prices: 2 coins, 4 coins, 6 coins, 8 coins, 10 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 2 coins is really cheap and 10 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "I'll be straight with you: I paid 6 coins for this fruit at the farm, so keep that in mind when you name a price."

### t157
- Value line: "The buyer can sell the fruit for 4 coins back in her home town."
- Listed prices: 2 coins, 3 coins, 4 coins, 5 coins, 6 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 4 coins. 2 coins is really cheap and 6 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 5 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Make it quick: name a serious price now or I turn to the next customer in line."

### t158
- Value line: "The buyer can sell the fruit for 15 coins back in her home town."
- Listed prices: 2 coins, 4 coins, 6 coins, 8 coins, 10 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 2 coins is really cheap and 10 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 6 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Time is money here. Put a serious price on the table now, or I'll sell elsewhere."

### t159
- Value line: "The buyer can sell the fruit for 15 coins back in her home town."
- Listed prices: 8 coins, 10 coins, 12 coins, 14 coins, 16 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 12 coins. 8 coins is really cheap and 16 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 3 and 7 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Full disclosure, my cost at the farm was 13 coins. Name your price with that in mind."

### t160
- Value line: "The buyer can sell the fruit for 3 coins back in her home town."
- Listed prices: 4 coins, 5 coins, 6 coins, 7 coins, 8 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 4 coins is really cheap and 8 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 6 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "I'm busy, so make your best offer immediately or I'll move on to the next customer."

### t161
- Value line: "The buyer can sell the fruit for 12 coins back in her home town."
- Listed prices: 2 coins, 4 coins, 6 coins, 8 coins, 10 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 2 coins is really cheap and 10 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 3 and 7 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "For your information, I paid 2 coins for this fruit at the farm. Bear that in mind when you make your offer."

### t162
- Value line: "The buyer can sell the fruit for 12 coins back in her home town."
- Listed prices: 2 coins, 3 coins, 4 coins, 5 coins, 6 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 4 coins. 2 coins is really cheap and 6 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Go ahead, tell me what price you are thinking of for this fruit."

### t163
- Value line: "The buyer can sell the fruit for 5 coins back in her home town."
- Listed prices: 2 coins, 4 coins, 6 coins, 8 coins, 10 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 2 coins is really cheap and 10 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 6 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Between us, the farm charged me 2 coins for it. Let that guide your offer."

### t164
- Value line: "The buyer can sell the fruit for 8 coins back in her home town."
- Listed prices: 4 coins, 5 coins, 6 coins, 7 coins, 8 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 4 coins is really cheap and 8 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Time is money here. Put a serious price on the table now, or I'll sell elsewhere."

### t165
- Value line: "The buyer can sell the fruit for 9 coins back in her home town."
- Listed prices: 4 coins, 5 coins, 6 coins, 7 coins, 8 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 4 coins is really cheap and 8 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Make it quick: name a serious price now or I turn to the next customer in line."

### t166
- Value line: "The buyer can sell the fruit for 7 coins back in her home town."
- Listed prices: 4 coins, 5 coins, 6 coins, 7 coins, 8 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 4 coins is really cheap and 8 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 6 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "I'll be straight with you: I paid 1 coin for this fruit at the farm, so keep that in mind when you name a price."

### t167
- Value line: "The buyer can sell the fruit for 14 coins back in her home town."
- Listed prices: 3 coins, 4 coins, 5 coins, 6 coins, 7 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 5 coins. 3 coins is really cheap and 7 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "I'll be straight with you: I paid 1 coin for this fruit at the farm, so keep that in mind when you name a price."

### t168
- Value line: "The buyer can sell the fruit for 9 coins back in her home town."
- Listed prices: 1 coin, 2 coins, 3 coins, 4 coins, 5 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 3 coins. 1 coin is really cheap and 5 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "There are other buyers waiting. Give me a real offer right now or step aside."

### t169
- Value line: "The buyer can sell the fruit for 14 coins back in her home town."
- Listed prices: 1 coin, 2 coins, 3 coins, 4 coins, 5 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 3 coins. 1 coin is really cheap and 5 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "I'll be straight with you: I paid 4 coins for this fruit at the farm, so keep that in mind when you name a price."

### t170
- Value line: "The buyer can sell the fruit for 12 coins back in her home town."
- Listed prices: 4 coins, 5 coins, 6 coins, 7 coins, 8 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 4 coins is really cheap and 8 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Between us, the farm charged me 3 coins for it. Let that guide your offer."

### t171
- Value line: "The buyer can sell the fruit for 12 coins back in her home town."
- Listed prices: 4 coins, 5 coins, 6 coins, 7 coins, 8 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 4 coins is really cheap and 8 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "I'll be straight with you: I paid 8 coins for this fruit at the farm, so keep that in mind when you name a price."

### t172
- Value line: "The buyer can sell the fruit for 13 coins back in her home town."
- Listed prices: 2 coins, 3 coins, 4 coins, 5 coins, 6 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 4 coins. 2 coins is really cheap and 6 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 5 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Full disclosure, my cost at the farm was 1 coin. Name your price with that in mind."

### t173
- Value line: "The buyer can sell the fruit for 13 coins back in her home town."
- Listed prices: 8 coins, 10 coins, 12 coins, 14 coins, 16 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 12 coins. 8 coins is really cheap and 16 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 3 and 7 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Full disclosure, my cost at the farm was 12 coins. Name your price with that in mind."

### t174
- Value line: "The buyer can sell the fruit for 13 coins back in her home town."
- Listed prices: 8 coins, 10 coins, 12 coins, 14 coins, 16 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 12 coins. 8 coins is really cheap and 16 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 6 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "For your information, I paid 6 coins for this fruit at the farm. Bear that in mind when you make your offer."

### t175
- Value line: "The buyer can sell the fruit for 12 coins back in her home town."
- Listed prices: 2 coins, 3 coins, 4 coins, 5 coins, 6 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 4 coins. 2 coins is really cheap and 6 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Full disclosure, my cost at the farm was 6 coins. Name your price with that in mind."

### t176
- Value line: "The buyer can sell the fruit for 12 coins back in her home town."
- Listed prices: 2 coins, 3 coins, 4 coins, 5 coins, 6 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 4 coins. 2 coins is really cheap and 6 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 5 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Full disclosure, my cost at the farm was 4 coins. Name your price with that in mind."

### t177
- Value line: "The buyer can sell the fruit for 5 coins back in her home town."
- Listed prices: 4 coins, 5 coins, 6 coins, 7 coins, 8 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 4 coins is really cheap and 8 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 5 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "I'll be straight with you: I paid 6 coins for this fruit at the farm, so keep that in mind when you name a price."

### t178
- Value line: "The buyer can sell the fruit for 14 coins back in her home town."
- Listed prices: 2 coins, 4 coins, 6 coins, 8 coins, 10 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 2 coins is really cheap and 10 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Time is money here. Put a serious price on the table now, or I'll sell elsewhere."

### t179
- Value line: "The buyer can sell the fruit for 15 coins back in her home town."
- Listed prices: 1 coin, 2 coins, 3 coins, 4 coins, 5 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 3 coins. 1 coin is really cheap and 5 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 5 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "There are other buyers waiting. Give me a real offer right now or step aside."

### t180
- Value line: "The buyer can sell the fruit for 12 coins back in her home town."
- Listed prices: 2 coins, 4 coins, 6 coins, 8 coins, 10 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 2 coins is really cheap and 10 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 5 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Make it quick: name a serious price now or I turn to the next customer in line."

### t181
- Value line: "The buyer can sell the fruit for 8 coins back in her home town."
- Listed prices: 2 coins, 4 coins, 6 coins, 8 coins, 10 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 2 coins is really cheap and 10 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 3 and 7 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "I'll be straight with you: I paid 6 coins for this fruit at the farm, so keep that in mind when you name a price."

### t182
- Value line: "The buyer can sell the fruit for 6 coins back in her home town."
- Listed prices: 2 coins, 4 coins, 6 coins, 8 coins, 10 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 2 coins is really cheap and 10 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Make it quick: name a serious price now or I turn to the next customer in line."

### t183
- Value line: "The buyer can sell the fruit for 15 coins back in her home town."
- Listed prices: 2 coins, 4 coins, 6 coins, 8 coins, 10 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 2 coins is really cheap and 10 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "For your information, I paid 5 coins for this fruit at the farm. Bear that in mind when you make your offer."

### t184
- Value line: "The buyer can sell the fruit for 10 coins back in her home town."
- Listed prices: 3 coins, 4 coins, 5 coins, 6 coins, 7 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 5 coins. 3 coins is really cheap and 7 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 5 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Between us, the farm charged me 7 coins for it. Let that guide your offer."

### t185
- Value line: "The buyer can sell the fruit for 11 coins back in her home town."
- Listed prices: 2 coins, 3 coins, 4 coins, 5 coins, 6 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 4 coins. 2 coins is really cheap and 6 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 6 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Go ahead, tell me what price you are thinking of for this fruit."

### t186
- Value line: "The buyer can sell the fruit for 13 coins back in her home town."
- Listed prices: 1 coin, 2 coins, 3 coins, 4 coins, 5 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 3 coins. 1 coin is really cheap and 5 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 6 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "I'll be straight with you: I paid 1 coin for this fruit at the farm, so keep that in mind when you name a price."

### t187
- Value line: "The buyer can sell the fruit for 15 coins back in her home town."
- Listed prices: 8 coins, 10 coins, 12 coins, 14 coins, 16 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 12 coins. 8 coins is really cheap and 16 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 3 and 7 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "For your information, I paid 5 coins for this fruit at the farm. Bear that in mind when you make your offer."

### t188
- Value line: "The buyer can sell the fruit for 13 coins back in her home town."
- Listed prices: 2 coins, 3 coins, 4 coins, 5 coins, 6 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 4 coins. 2 coins is really cheap and 6 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 5 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Time is money here. Put a serious price on the table now, or I'll sell elsewhere."

### t189
- Value line: "The buyer can sell the fruit for 12 coins back in her home town."
- Listed prices: 8 coins, 10 coins, 12 coins, 14 coins, 16 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 12 coins. 8 coins is really cheap and 16 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Full disclosure, my cost at the farm was 8 coins. Name your price with that in mind."

### t190
- Value line: "The buyer can sell the fruit for 6 coins back in her home town."
- Listed prices: 4 coins, 5 coins, 6 coins, 7 coins, 8 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 4 coins is really cheap and 8 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Make it quick: name a serious price now or I turn to the next customer in line."

### t191
- Value line: "The buyer can sell the fruit for 6 coins back in her home town."
- Listed prices: 8 coins, 10 coins, 12 coins, 14 coins, 16 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 12 coins. 8 coins is really cheap and 16 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 6 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "I'm listening. What price do you have in mind for the fruit?"

### t192
- Value line: "The buyer can sell the fruit for 10 coins back in her home town."
- Listed prices: 1 coin, 2 coins, 3 coins, 4 coins, 5 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 3 coins. 1 coin is really cheap and 5 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 6 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "I'll be straight with you: I paid 2 coins for this fruit at the farm, so keep that in mind when you name a price."

### t193
- Value line: "The buyer can sell the fruit for 10 coins back in her home town."
- Listed prices: 2 coins, 3 coins, 4 coins, 5 coins, 6 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 4 coins. 2 coins is really cheap and 6 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Full disclosure, my cost at the farm was 2 coins. Name your price with that in mind."

### t194
- Value line: "The buyer can sell the fruit for 15 coins back in her home town."
- Listed prices: 1 coin, 2 coins, 3 coins, 4 coins, 5 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 3 coins. 1 coin is really cheap and 5 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 6 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Full disclosure, my cost at the farm was 5 coins. Name your price with that in mind."

### t195
- Value line: "The buyer can sell the fruit for 4 coins back in her home town."
- Listed prices: 4 coins, 5 coins, 6 coins, 7 coins, 8 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 4 coins is really cheap and 8 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 6 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "I'm busy, so make your best offer immediately or I'll move on to the next customer."

### t196
- Value line: "The buyer can sell the fruit for 5 coins back in her home town."
- Listed prices: 8 coins, 10 coins, 12 coins, 14 coins, 16 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 12 coins. 8 coins is really cheap and 16 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 6 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Full disclosure, my cost at the farm was 2 coins. Name your price with that in mind."

### t197
- Value line: "The buyer can sell the fruit for 13 coins back in her home town."
- Listed prices: 3 coins, 4 coins, 5 coins, 6 coins, 7 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 5 coins. 3 coins is really cheap and 7 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Whenever you are ready, say what you would pay for it."

### t198
- Value line: "The buyer can sell the fruit for 12 coins back in her home town."
- Listed prices: 2 coins, 4 coins, 6 coins, 8 coins, 10 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 2 coins is really cheap and 10 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 3 and 7 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "For your information, I paid 3 coins for this fruit at the farm. Bear that in mind when you make your offer."

### t199
- Value line: "The buyer can sell the fruit for 12 coins back in her home town."
- Listed prices: 1 coin, 2 coins, 3 coins, 4 coins, 5 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 3 coins. 1 coin is really cheap and 5 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 6 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "There are other buyers waiting. Give me a real offer right now or step aside."

### t200
- Value line: "The buyer can sell the fruit for 15 coins back in her home town."
- Listed prices: 2 coins, 3 coins, 4 coins, 5 coins, 6 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 4 coins. 2 coins is really cheap and 6 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "No rush. What would you like to offer for the fruit?"

## What to produce
For each case, decide which ONE of the listed prices the buyer should offer to earn the highest expected profit. Output ONE JSON object whose keys are the case ids (for example "t101") and whose values are the chosen price as a whole number taken from that case's listed prices. Include all 100 ids and nothing else; no commentary.
