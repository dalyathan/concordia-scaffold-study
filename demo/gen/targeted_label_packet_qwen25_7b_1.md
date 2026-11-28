# Packet: choose the offer in each case

You are helping to build training material for a language model that plays a buyer in a small haggling game. Read everything, then answer with ONE JSON object and nothing else.

## The game
A buyer wants to buy fruit from a seller and can resell it for a known value (in coins) in her home town. The buyer chooses one of five prices to offer; the five prices are shown as lettered options and may differ between cases (for example 1 to 5 coins or 3 to 7 coins). The seller accepts an offer if it is at or above the seller's own farm cost and refuses a lower offer. If the offer is accepted, the buyer's profit is the resale value minus the offer (it can be negative); if it is refused, the profit is zero. When the seller says what the fruit cost at the farm, that is true. When no cost is stated, the prompt says that every whole-number farm cost between two stated limits is equally likely. The buyer wants the highest expected profit.

## The cases
Below are 100 separate cases. Each case lists the resale value, the five prices the buyer may offer (exactly these five), a line about typical prices, the line about what sellers at this market pay at the farm, and the seller's last line. Cases are independent of each other.

### t001
- Value line: "The buyer can sell the fruit for 14 coins back in her home town."
- Listed prices: 4 coins, 5 coins, 6 coins, 7 coins, 8 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 4 coins is really cheap and 8 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Between us, the farm charged me 6 coins for it. Let that guide your offer."

### t002
- Value line: "The buyer can sell the fruit for 8 coins back in her home town."
- Listed prices: 4 coins, 5 coins, 6 coins, 7 coins, 8 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 4 coins is really cheap and 8 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 3 and 7 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Whenever you are ready, say what you would pay for it."

### t003
- Value line: "The buyer can sell the fruit for 14 coins back in her home town."
- Listed prices: 8 coins, 10 coins, 12 coins, 14 coins, 16 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 12 coins. 8 coins is really cheap and 16 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 3 and 7 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Full disclosure, my cost at the farm was 3 coins. Name your price with that in mind."

### t004
- Value line: "The buyer can sell the fruit for 5 coins back in her home town."
- Listed prices: 4 coins, 5 coins, 6 coins, 7 coins, 8 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 4 coins is really cheap and 8 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "I'll be straight with you: I paid 5 coins for this fruit at the farm, so keep that in mind when you name a price."

### t005
- Value line: "The buyer can sell the fruit for 9 coins back in her home town."
- Listed prices: 4 coins, 5 coins, 6 coins, 7 coins, 8 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 4 coins is really cheap and 8 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "For your information, I paid 6 coins for this fruit at the farm. Bear that in mind when you make your offer."

### t006
- Value line: "The buyer can sell the fruit for 13 coins back in her home town."
- Listed prices: 3 coins, 4 coins, 5 coins, 6 coins, 7 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 5 coins. 3 coins is really cheap and 7 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 6 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "For your information, I paid 6 coins for this fruit at the farm. Bear that in mind when you make your offer."

### t007
- Value line: "The buyer can sell the fruit for 14 coins back in her home town."
- Listed prices: 1 coin, 2 coins, 3 coins, 4 coins, 5 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 3 coins. 1 coin is really cheap and 5 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 6 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Whenever you are ready, say what you would pay for it."

### t008
- Value line: "The buyer can sell the fruit for 14 coins back in her home town."
- Listed prices: 2 coins, 4 coins, 6 coins, 8 coins, 10 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 2 coins is really cheap and 10 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 5 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Full disclosure, my cost at the farm was 5 coins. Name your price with that in mind."

### t009
- Value line: "The buyer can sell the fruit for 15 coins back in her home town."
- Listed prices: 3 coins, 4 coins, 5 coins, 6 coins, 7 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 5 coins. 3 coins is really cheap and 7 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 6 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "For your information, I paid 3 coins for this fruit at the farm. Bear that in mind when you make your offer."

### t010
- Value line: "The buyer can sell the fruit for 7 coins back in her home town."
- Listed prices: 4 coins, 5 coins, 6 coins, 7 coins, 8 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 4 coins is really cheap and 8 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 5 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "There are other buyers waiting. Give me a real offer right now or step aside."

### t011
- Value line: "The buyer can sell the fruit for 15 coins back in her home town."
- Listed prices: 4 coins, 5 coins, 6 coins, 7 coins, 8 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 4 coins is really cheap and 8 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 5 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "For your information, I paid 2 coins for this fruit at the farm. Bear that in mind when you make your offer."

### t012
- Value line: "The buyer can sell the fruit for 10 coins back in her home town."
- Listed prices: 3 coins, 4 coins, 5 coins, 6 coins, 7 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 5 coins. 3 coins is really cheap and 7 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "For your information, I paid 3 coins for this fruit at the farm. Bear that in mind when you make your offer."

### t013
- Value line: "The buyer can sell the fruit for 7 coins back in her home town."
- Listed prices: 2 coins, 4 coins, 6 coins, 8 coins, 10 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 2 coins is really cheap and 10 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 5 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "I'm busy, so make your best offer immediately or I'll move on to the next customer."

### t014
- Value line: "The buyer can sell the fruit for 12 coins back in her home town."
- Listed prices: 4 coins, 5 coins, 6 coins, 7 coins, 8 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 4 coins is really cheap and 8 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "I'm busy, so make your best offer immediately or I'll move on to the next customer."

### t015
- Value line: "The buyer can sell the fruit for 12 coins back in her home town."
- Listed prices: 3 coins, 4 coins, 5 coins, 6 coins, 7 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 5 coins. 3 coins is really cheap and 7 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "I'm busy, so make your best offer immediately or I'll move on to the next customer."

### t016
- Value line: "The buyer can sell the fruit for 14 coins back in her home town."
- Listed prices: 4 coins, 5 coins, 6 coins, 7 coins, 8 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 4 coins is really cheap and 8 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 5 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "I'll be straight with you: I paid 3 coins for this fruit at the farm, so keep that in mind when you name a price."

### t017
- Value line: "The buyer can sell the fruit for 12 coins back in her home town."
- Listed prices: 3 coins, 4 coins, 5 coins, 6 coins, 7 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 5 coins. 3 coins is really cheap and 7 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 6 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Between us, the farm charged me 1 coin for it. Let that guide your offer."

### t018
- Value line: "The buyer can sell the fruit for 13 coins back in her home town."
- Listed prices: 8 coins, 10 coins, 12 coins, 14 coins, 16 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 12 coins. 8 coins is really cheap and 16 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 5 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Between us, the farm charged me 3 coins for it. Let that guide your offer."

### t019
- Value line: "The buyer can sell the fruit for 14 coins back in her home town."
- Listed prices: 2 coins, 4 coins, 6 coins, 8 coins, 10 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 2 coins is really cheap and 10 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 3 and 7 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Full disclosure, my cost at the farm was 7 coins. Name your price with that in mind."

### t020
- Value line: "The buyer can sell the fruit for 12 coins back in her home town."
- Listed prices: 2 coins, 3 coins, 4 coins, 5 coins, 6 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 4 coins. 2 coins is really cheap and 6 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 3 and 7 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "I'm busy, so make your best offer immediately or I'll move on to the next customer."

### t021
- Value line: "The buyer can sell the fruit for 14 coins back in her home town."
- Listed prices: 2 coins, 4 coins, 6 coins, 8 coins, 10 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 2 coins is really cheap and 10 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 5 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "There are other buyers waiting. Give me a real offer right now or step aside."

### t022
- Value line: "The buyer can sell the fruit for 8 coins back in her home town."
- Listed prices: 3 coins, 4 coins, 5 coins, 6 coins, 7 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 5 coins. 3 coins is really cheap and 7 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 5 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Make it quick: name a serious price now or I turn to the next customer in line."

### t023
- Value line: "The buyer can sell the fruit for 11 coins back in her home town."
- Listed prices: 1 coin, 2 coins, 3 coins, 4 coins, 5 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 3 coins. 1 coin is really cheap and 5 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "I'm listening. What price do you have in mind for the fruit?"

### t024
- Value line: "The buyer can sell the fruit for 11 coins back in her home town."
- Listed prices: 2 coins, 4 coins, 6 coins, 8 coins, 10 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 2 coins is really cheap and 10 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 3 and 7 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "There are other buyers waiting. Give me a real offer right now or step aside."

### t025
- Value line: "The buyer can sell the fruit for 11 coins back in her home town."
- Listed prices: 2 coins, 4 coins, 6 coins, 8 coins, 10 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 2 coins is really cheap and 10 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 5 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "I'll be straight with you: I paid 1 coin for this fruit at the farm, so keep that in mind when you name a price."

### t026
- Value line: "The buyer can sell the fruit for 12 coins back in her home town."
- Listed prices: 3 coins, 4 coins, 5 coins, 6 coins, 7 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 5 coins. 3 coins is really cheap and 7 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Time is money here. Put a serious price on the table now, or I'll sell elsewhere."

### t027
- Value line: "The buyer can sell the fruit for 12 coins back in her home town."
- Listed prices: 4 coins, 5 coins, 6 coins, 7 coins, 8 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 4 coins is really cheap and 8 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 3 and 7 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "I'm busy, so make your best offer immediately or I'll move on to the next customer."

### t028
- Value line: "The buyer can sell the fruit for 13 coins back in her home town."
- Listed prices: 1 coin, 2 coins, 3 coins, 4 coins, 5 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 3 coins. 1 coin is really cheap and 5 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 3 and 7 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Full disclosure, my cost at the farm was 4 coins. Name your price with that in mind."

### t029
- Value line: "The buyer can sell the fruit for 15 coins back in her home town."
- Listed prices: 2 coins, 3 coins, 4 coins, 5 coins, 6 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 4 coins. 2 coins is really cheap and 6 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Whenever you are ready, say what you would pay for it."

### t030
- Value line: "The buyer can sell the fruit for 14 coins back in her home town."
- Listed prices: 3 coins, 4 coins, 5 coins, 6 coins, 7 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 5 coins. 3 coins is really cheap and 7 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "I'm listening. What price do you have in mind for the fruit?"

### t031
- Value line: "The buyer can sell the fruit for 14 coins back in her home town."
- Listed prices: 8 coins, 10 coins, 12 coins, 14 coins, 16 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 12 coins. 8 coins is really cheap and 16 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "For your information, I paid 11 coins for this fruit at the farm. Bear that in mind when you make your offer."

### t032
- Value line: "The buyer can sell the fruit for 10 coins back in her home town."
- Listed prices: 3 coins, 4 coins, 5 coins, 6 coins, 7 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 5 coins. 3 coins is really cheap and 7 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "There are other buyers waiting. Give me a real offer right now or step aside."

### t033
- Value line: "The buyer can sell the fruit for 4 coins back in her home town."
- Listed prices: 8 coins, 10 coins, 12 coins, 14 coins, 16 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 12 coins. 8 coins is really cheap and 16 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "I'm busy, so make your best offer immediately or I'll move on to the next customer."

### t034
- Value line: "The buyer can sell the fruit for 7 coins back in her home town."
- Listed prices: 8 coins, 10 coins, 12 coins, 14 coins, 16 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 12 coins. 8 coins is really cheap and 16 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 3 and 7 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "I'll be straight with you: I paid 1 coin for this fruit at the farm, so keep that in mind when you name a price."

### t035
- Value line: "The buyer can sell the fruit for 7 coins back in her home town."
- Listed prices: 2 coins, 4 coins, 6 coins, 8 coins, 10 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 2 coins is really cheap and 10 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "For your information, I paid 1 coin for this fruit at the farm. Bear that in mind when you make your offer."

### t036
- Value line: "The buyer can sell the fruit for 13 coins back in her home town."
- Listed prices: 3 coins, 4 coins, 5 coins, 6 coins, 7 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 5 coins. 3 coins is really cheap and 7 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Time is money here. Put a serious price on the table now, or I'll sell elsewhere."

### t037
- Value line: "The buyer can sell the fruit for 13 coins back in her home town."
- Listed prices: 8 coins, 10 coins, 12 coins, 14 coins, 16 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 12 coins. 8 coins is really cheap and 16 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 3 and 7 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "No rush. What would you like to offer for the fruit?"

### t038
- Value line: "The buyer can sell the fruit for 15 coins back in her home town."
- Listed prices: 8 coins, 10 coins, 12 coins, 14 coins, 16 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 12 coins. 8 coins is really cheap and 16 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 5 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Go ahead, tell me what price you are thinking of for this fruit."

### t039
- Value line: "The buyer can sell the fruit for 11 coins back in her home town."
- Listed prices: 8 coins, 10 coins, 12 coins, 14 coins, 16 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 12 coins. 8 coins is really cheap and 16 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "For your information, I paid 2 coins for this fruit at the farm. Bear that in mind when you make your offer."

### t040
- Value line: "The buyer can sell the fruit for 2 coins back in her home town."
- Listed prices: 4 coins, 5 coins, 6 coins, 7 coins, 8 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 4 coins is really cheap and 8 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 3 and 7 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Time is money here. Put a serious price on the table now, or I'll sell elsewhere."

### t041
- Value line: "The buyer can sell the fruit for 3 coins back in her home town."
- Listed prices: 4 coins, 5 coins, 6 coins, 7 coins, 8 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 4 coins is really cheap and 8 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "There are other buyers waiting. Give me a real offer right now or step aside."

### t042
- Value line: "The buyer can sell the fruit for 14 coins back in her home town."
- Listed prices: 3 coins, 4 coins, 5 coins, 6 coins, 7 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 5 coins. 3 coins is really cheap and 7 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 3 and 7 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Make it quick: name a serious price now or I turn to the next customer in line."

### t043
- Value line: "The buyer can sell the fruit for 11 coins back in her home town."
- Listed prices: 1 coin, 2 coins, 3 coins, 4 coins, 5 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 3 coins. 1 coin is really cheap and 5 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "There are other buyers waiting. Give me a real offer right now or step aside."

### t044
- Value line: "The buyer can sell the fruit for 5 coins back in her home town."
- Listed prices: 8 coins, 10 coins, 12 coins, 14 coins, 16 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 12 coins. 8 coins is really cheap and 16 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 6 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Whenever you are ready, say what you would pay for it."

### t045
- Value line: "The buyer can sell the fruit for 7 coins back in her home town."
- Listed prices: 2 coins, 4 coins, 6 coins, 8 coins, 10 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 2 coins is really cheap and 10 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 6 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "I'm listening. What price do you have in mind for the fruit?"

### t046
- Value line: "The buyer can sell the fruit for 7 coins back in her home town."
- Listed prices: 8 coins, 10 coins, 12 coins, 14 coins, 16 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 12 coins. 8 coins is really cheap and 16 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 6 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "There are other buyers waiting. Give me a real offer right now or step aside."

### t047
- Value line: "The buyer can sell the fruit for 14 coins back in her home town."
- Listed prices: 2 coins, 3 coins, 4 coins, 5 coins, 6 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 4 coins. 2 coins is really cheap and 6 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 5 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "I'll be straight with you: I paid 4 coins for this fruit at the farm, so keep that in mind when you name a price."

### t048
- Value line: "The buyer can sell the fruit for 12 coins back in her home town."
- Listed prices: 3 coins, 4 coins, 5 coins, 6 coins, 7 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 5 coins. 3 coins is really cheap and 7 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "For your information, I paid 4 coins for this fruit at the farm. Bear that in mind when you make your offer."

### t049
- Value line: "The buyer can sell the fruit for 9 coins back in her home town."
- Listed prices: 2 coins, 4 coins, 6 coins, 8 coins, 10 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 2 coins is really cheap and 10 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "There are other buyers waiting. Give me a real offer right now or step aside."

### t050
- Value line: "The buyer can sell the fruit for 7 coins back in her home town."
- Listed prices: 4 coins, 5 coins, 6 coins, 7 coins, 8 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 4 coins is really cheap and 8 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 6 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "There are other buyers waiting. Give me a real offer right now or step aside."

### t051
- Value line: "The buyer can sell the fruit for 15 coins back in her home town."
- Listed prices: 8 coins, 10 coins, 12 coins, 14 coins, 16 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 12 coins. 8 coins is really cheap and 16 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 6 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Between us, the farm charged me 7 coins for it. Let that guide your offer."

### t052
- Value line: "The buyer can sell the fruit for 13 coins back in her home town."
- Listed prices: 4 coins, 5 coins, 6 coins, 7 coins, 8 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 4 coins is really cheap and 8 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 5 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "I'm listening. What price do you have in mind for the fruit?"

### t053
- Value line: "The buyer can sell the fruit for 11 coins back in her home town."
- Listed prices: 2 coins, 4 coins, 6 coins, 8 coins, 10 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 2 coins is really cheap and 10 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 6 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "There are other buyers waiting. Give me a real offer right now or step aside."

### t054
- Value line: "The buyer can sell the fruit for 4 coins back in her home town."
- Listed prices: 8 coins, 10 coins, 12 coins, 14 coins, 16 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 12 coins. 8 coins is really cheap and 16 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 3 and 7 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "For your information, I paid 5 coins for this fruit at the farm. Bear that in mind when you make your offer."

### t055
- Value line: "The buyer can sell the fruit for 12 coins back in her home town."
- Listed prices: 4 coins, 5 coins, 6 coins, 7 coins, 8 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 4 coins is really cheap and 8 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Whenever you are ready, say what you would pay for it."

### t056
- Value line: "The buyer can sell the fruit for 15 coins back in her home town."
- Listed prices: 4 coins, 5 coins, 6 coins, 7 coins, 8 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 4 coins is really cheap and 8 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "For your information, I paid 3 coins for this fruit at the farm. Bear that in mind when you make your offer."

### t057
- Value line: "The buyer can sell the fruit for 11 coins back in her home town."
- Listed prices: 2 coins, 4 coins, 6 coins, 8 coins, 10 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 2 coins is really cheap and 10 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 3 and 7 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "For your information, I paid 6 coins for this fruit at the farm. Bear that in mind when you make your offer."

### t058
- Value line: "The buyer can sell the fruit for 14 coins back in her home town."
- Listed prices: 2 coins, 4 coins, 6 coins, 8 coins, 10 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 2 coins is really cheap and 10 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 3 and 7 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Between us, the farm charged me 3 coins for it. Let that guide your offer."

### t059
- Value line: "The buyer can sell the fruit for 12 coins back in her home town."
- Listed prices: 1 coin, 2 coins, 3 coins, 4 coins, 5 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 3 coins. 1 coin is really cheap and 5 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 5 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Time is money here. Put a serious price on the table now, or I'll sell elsewhere."

### t060
- Value line: "The buyer can sell the fruit for 2 coins back in her home town."
- Listed prices: 8 coins, 10 coins, 12 coins, 14 coins, 16 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 12 coins. 8 coins is really cheap and 16 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 5 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "No rush. What would you like to offer for the fruit?"

### t061
- Value line: "The buyer can sell the fruit for 11 coins back in her home town."
- Listed prices: 4 coins, 5 coins, 6 coins, 7 coins, 8 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 4 coins is really cheap and 8 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 5 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Go ahead, tell me what price you are thinking of for this fruit."

### t062
- Value line: "The buyer can sell the fruit for 13 coins back in her home town."
- Listed prices: 8 coins, 10 coins, 12 coins, 14 coins, 16 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 12 coins. 8 coins is really cheap and 16 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 6 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "I'll be straight with you: I paid 5 coins for this fruit at the farm, so keep that in mind when you name a price."

### t063
- Value line: "The buyer can sell the fruit for 13 coins back in her home town."
- Listed prices: 2 coins, 4 coins, 6 coins, 8 coins, 10 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 2 coins is really cheap and 10 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 3 and 7 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Between us, the farm charged me 7 coins for it. Let that guide your offer."

### t064
- Value line: "The buyer can sell the fruit for 15 coins back in her home town."
- Listed prices: 8 coins, 10 coins, 12 coins, 14 coins, 16 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 12 coins. 8 coins is really cheap and 16 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 5 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Full disclosure, my cost at the farm was 14 coins. Name your price with that in mind."

### t065
- Value line: "The buyer can sell the fruit for 14 coins back in her home town."
- Listed prices: 4 coins, 5 coins, 6 coins, 7 coins, 8 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 4 coins is really cheap and 8 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 5 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "For your information, I paid 4 coins for this fruit at the farm. Bear that in mind when you make your offer."

### t066
- Value line: "The buyer can sell the fruit for 15 coins back in her home town."
- Listed prices: 8 coins, 10 coins, 12 coins, 14 coins, 16 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 12 coins. 8 coins is really cheap and 16 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "For your information, I paid 12 coins for this fruit at the farm. Bear that in mind when you make your offer."

### t067
- Value line: "The buyer can sell the fruit for 8 coins back in her home town."
- Listed prices: 8 coins, 10 coins, 12 coins, 14 coins, 16 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 12 coins. 8 coins is really cheap and 16 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Whenever you are ready, say what you would pay for it."

### t068
- Value line: "The buyer can sell the fruit for 13 coins back in her home town."
- Listed prices: 4 coins, 5 coins, 6 coins, 7 coins, 8 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 4 coins is really cheap and 8 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "I'm listening. What price do you have in mind for the fruit?"

### t069
- Value line: "The buyer can sell the fruit for 8 coins back in her home town."
- Listed prices: 4 coins, 5 coins, 6 coins, 7 coins, 8 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 4 coins is really cheap and 8 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "I'll be straight with you: I paid 4 coins for this fruit at the farm, so keep that in mind when you name a price."

### t070
- Value line: "The buyer can sell the fruit for 12 coins back in her home town."
- Listed prices: 1 coin, 2 coins, 3 coins, 4 coins, 5 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 3 coins. 1 coin is really cheap and 5 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 3 and 7 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "For your information, I paid 3 coins for this fruit at the farm. Bear that in mind when you make your offer."

### t071
- Value line: "The buyer can sell the fruit for 15 coins back in her home town."
- Listed prices: 8 coins, 10 coins, 12 coins, 14 coins, 16 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 12 coins. 8 coins is really cheap and 16 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "There are other buyers waiting. Give me a real offer right now or step aside."

### t072
- Value line: "The buyer can sell the fruit for 10 coins back in her home town."
- Listed prices: 4 coins, 5 coins, 6 coins, 7 coins, 8 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 4 coins is really cheap and 8 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 3 and 7 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "For your information, I paid 1 coin for this fruit at the farm. Bear that in mind when you make your offer."

### t073
- Value line: "The buyer can sell the fruit for 15 coins back in her home town."
- Listed prices: 8 coins, 10 coins, 12 coins, 14 coins, 16 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 12 coins. 8 coins is really cheap and 16 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 5 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Full disclosure, my cost at the farm was 8 coins. Name your price with that in mind."

### t074
- Value line: "The buyer can sell the fruit for 15 coins back in her home town."
- Listed prices: 4 coins, 5 coins, 6 coins, 7 coins, 8 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 4 coins is really cheap and 8 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Make it quick: name a serious price now or I turn to the next customer in line."

### t075
- Value line: "The buyer can sell the fruit for 4 coins back in her home town."
- Listed prices: 2 coins, 3 coins, 4 coins, 5 coins, 6 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 4 coins. 2 coins is really cheap and 6 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 3 and 7 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Whenever you are ready, say what you would pay for it."

### t076
- Value line: "The buyer can sell the fruit for 8 coins back in her home town."
- Listed prices: 8 coins, 10 coins, 12 coins, 14 coins, 16 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 12 coins. 8 coins is really cheap and 16 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 6 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Go ahead, tell me what price you are thinking of for this fruit."

### t077
- Value line: "The buyer can sell the fruit for 7 coins back in her home town."
- Listed prices: 4 coins, 5 coins, 6 coins, 7 coins, 8 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 4 coins is really cheap and 8 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "There are other buyers waiting. Give me a real offer right now or step aside."

### t078
- Value line: "The buyer can sell the fruit for 15 coins back in her home town."
- Listed prices: 2 coins, 4 coins, 6 coins, 8 coins, 10 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 2 coins is really cheap and 10 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Make it quick: name a serious price now or I turn to the next customer in line."

### t079
- Value line: "The buyer can sell the fruit for 12 coins back in her home town."
- Listed prices: 8 coins, 10 coins, 12 coins, 14 coins, 16 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 12 coins. 8 coins is really cheap and 16 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Full disclosure, my cost at the farm was 11 coins. Name your price with that in mind."

### t080
- Value line: "The buyer can sell the fruit for 14 coins back in her home town."
- Listed prices: 4 coins, 5 coins, 6 coins, 7 coins, 8 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 4 coins is really cheap and 8 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Whenever you are ready, say what you would pay for it."

### t081
- Value line: "The buyer can sell the fruit for 7 coins back in her home town."
- Listed prices: 2 coins, 4 coins, 6 coins, 8 coins, 10 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 2 coins is really cheap and 10 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Full disclosure, my cost at the farm was 9 coins. Name your price with that in mind."

### t082
- Value line: "The buyer can sell the fruit for 13 coins back in her home town."
- Listed prices: 3 coins, 4 coins, 5 coins, 6 coins, 7 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 5 coins. 3 coins is really cheap and 7 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 6 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "For your information, I paid 3 coins for this fruit at the farm. Bear that in mind when you make your offer."

### t083
- Value line: "The buyer can sell the fruit for 5 coins back in her home town."
- Listed prices: 8 coins, 10 coins, 12 coins, 14 coins, 16 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 12 coins. 8 coins is really cheap and 16 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Go ahead, tell me what price you are thinking of for this fruit."

### t084
- Value line: "The buyer can sell the fruit for 15 coins back in her home town."
- Listed prices: 1 coin, 2 coins, 3 coins, 4 coins, 5 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 3 coins. 1 coin is really cheap and 5 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "I'll be straight with you: I paid 1 coin for this fruit at the farm, so keep that in mind when you name a price."

### t085
- Value line: "The buyer can sell the fruit for 6 coins back in her home town."
- Listed prices: 4 coins, 5 coins, 6 coins, 7 coins, 8 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 4 coins is really cheap and 8 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 6 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Whenever you are ready, say what you would pay for it."

### t086
- Value line: "The buyer can sell the fruit for 5 coins back in her home town."
- Listed prices: 4 coins, 5 coins, 6 coins, 7 coins, 8 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 4 coins is really cheap and 8 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 6 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Make it quick: name a serious price now or I turn to the next customer in line."

### t087
- Value line: "The buyer can sell the fruit for 13 coins back in her home town."
- Listed prices: 2 coins, 3 coins, 4 coins, 5 coins, 6 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 4 coins. 2 coins is really cheap and 6 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 5 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Between us, the farm charged me 3 coins for it. Let that guide your offer."

### t088
- Value line: "The buyer can sell the fruit for 9 coins back in her home town."
- Listed prices: 4 coins, 5 coins, 6 coins, 7 coins, 8 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 4 coins is really cheap and 8 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "I'll be straight with you: I paid 4 coins for this fruit at the farm, so keep that in mind when you name a price."

### t089
- Value line: "The buyer can sell the fruit for 11 coins back in her home town."
- Listed prices: 2 coins, 4 coins, 6 coins, 8 coins, 10 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 2 coins is really cheap and 10 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "For your information, I paid 8 coins for this fruit at the farm. Bear that in mind when you make your offer."

### t090
- Value line: "The buyer can sell the fruit for 13 coins back in her home town."
- Listed prices: 2 coins, 4 coins, 6 coins, 8 coins, 10 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 2 coins is really cheap and 10 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 5 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "For your information, I paid 10 coins for this fruit at the farm. Bear that in mind when you make your offer."

### t091
- Value line: "The buyer can sell the fruit for 15 coins back in her home town."
- Listed prices: 1 coin, 2 coins, 3 coins, 4 coins, 5 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 3 coins. 1 coin is really cheap and 5 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 2 and 6 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "I'm busy, so make your best offer immediately or I'll move on to the next customer."

### t092
- Value line: "The buyer can sell the fruit for 7 coins back in her home town."
- Listed prices: 4 coins, 5 coins, 6 coins, 7 coins, 8 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 4 coins is really cheap and 8 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 5 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "I'll be straight with you: I paid 5 coins for this fruit at the farm, so keep that in mind when you name a price."

### t093
- Value line: "The buyer can sell the fruit for 9 coins back in her home town."
- Listed prices: 2 coins, 4 coins, 6 coins, 8 coins, 10 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 2 coins is really cheap and 10 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 3 and 7 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "For your information, I paid 5 coins for this fruit at the farm. Bear that in mind when you make your offer."

### t094
- Value line: "The buyer can sell the fruit for 4 coins back in her home town."
- Listed prices: 8 coins, 10 coins, 12 coins, 14 coins, 16 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 12 coins. 8 coins is really cheap and 16 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 3 and 7 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "For your information, I paid 6 coins for this fruit at the farm. Bear that in mind when you make your offer."

### t095
- Value line: "The buyer can sell the fruit for 10 coins back in her home town."
- Listed prices: 1 coin, 2 coins, 3 coins, 4 coins, 5 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 3 coins. 1 coin is really cheap and 5 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "I'm listening. What price do you have in mind for the fruit?"

### t096
- Value line: "The buyer can sell the fruit for 5 coins back in her home town."
- Listed prices: 4 coins, 5 coins, 6 coins, 7 coins, 8 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 4 coins is really cheap and 8 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Time is money here. Put a serious price on the table now, or I'll sell elsewhere."

### t097
- Value line: "The buyer can sell the fruit for 12 coins back in her home town."
- Listed prices: 8 coins, 10 coins, 12 coins, 14 coins, 16 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 12 coins. 8 coins is really cheap and 16 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 5 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "Between us, the farm charged me 4 coins for it. Let that guide your offer."

### t098
- Value line: "The buyer can sell the fruit for 13 coins back in her home town."
- Listed prices: 1 coin, 2 coins, 3 coins, 4 coins, 5 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 3 coins. 1 coin is really cheap and 5 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 3 and 7 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "For your information, I paid 5 coins for this fruit at the farm. Bear that in mind when you make your offer."

### t099
- Value line: "The buyer can sell the fruit for 3 coins back in her home town."
- Listed prices: 8 coins, 10 coins, 12 coins, 14 coins, 16 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 12 coins. 8 coins is really cheap and 16 coins is really expensive. The smallest value of transaction is 2 coins, all prices have to be in multiples of 2 coins. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 3 and 7 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "I'm listening. What price do you have in mind for the fruit?"

### t100
- Value line: "The buyer can sell the fruit for 14 coins back in her home town."
- Listed prices: 4 coins, 5 coins, 6 coins, 7 coins, 8 coins
- Price scale line: "The price of one kilogram of fruit is, on average, 6 coins. 4 coins is really cheap and 8 coins is really expensive. The smallest value of transaction is 1 coin, all prices have to be in multiples of 1 coin. No fractional values are allowed."
- Farm cost line: "Sellers at this market pay between 1 and 10 coins per kilogram at the farm, and each amount is equally likely."
- The seller's last line: "I'll be straight with you: I paid 2 coins for this fruit at the farm, so keep that in mind when you name a price."

## What to produce
For each case, decide which ONE of the listed prices the buyer should offer to earn the highest expected profit. Output ONE JSON object whose keys are the case ids (for example "t001") and whose values are the chosen price as a whole number taken from that case's listed prices. Include all 100 ids and nothing else; no commentary.
