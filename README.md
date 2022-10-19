# Aplaca-Trading-Algo
A live swing trading algorithm named Athena that runs on the Alpaca API. Athena works by taking a perosnalized list of stocks/indices, compiles 5 years of stock trading data for each of those stocks into a dataframe, and generates buy levels based on multiple indicators like the fibonacci retractments, bollinger bands and exponential moving averages. Once the market opens, Athena will connect to real time market data via Alpaca and if the stock price moves below a buy level, athena will intiate a buy order and will wait til another buy level is reached to intiate another buy order. The amount of buys are limited for each asset to ensure proper risk management. Multiple risk management features are built into the trading algo as well. Athena runs continously on Amazon cloud until the user stops it through keyboard interrupt. 


Options-

All these variables can be edited within Athena's code to reflect your tolerances: 

margin: Alpaca API requires you to trade on margin. This can be changed on the Alpcaca trading account 
company: The ticker of the index or stock you want to swing trade.
cashweight: The minimum amount of cash you want your portfolio to have
posweight = max weighting of a position in your portfolio.
never_buy_near_high = A stock price level where Athena will never buy at or above 
risk_per_trade = The percentage of your protfolio your willing to risk on a trade. 
standard_qty = the default amount of shares Athena will buy for a trade. Dependent on your risk per trade value.
    


Requirements/How to set up-

Uses Alpaca https://alpaca.markets/ for trading. You will need an account with Alpaca to use Athena.

You can save your Alpaca authentication api keys to secret.py.

https://api.alpaca.markets (for live)

https://paper-api.alpaca.markets (for paper)

Install requirements Alpaca python library:

pip3 install -r requirements.txt
