from cmath import nan
import alpaca_trade_api as tradeapi
from alpaca_trade_api.rest import REST, TimeFrame
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from alpaca_trade_api.stream import Stream
from alpaca_trade_api.common import URL
import pandas as pd 
import numpy as np
import math
import time
import datetime
from datetime import date, timedelta
from secret import *
import sys
import threading
import asyncio


pap_key = paper_key
pap_secret = paper_secret
SEC_KEY = LIVE_SEC_KEY
PUB_KEY = LIVE_PUB_KEY
BASE_URL = 'https://paper-api.alpaca.markets'
data_feed = "iex"

api = tradeapi.REST(key_id= pap_key, secret_key=pap_secret, base_url=BASE_URL)
recent_buys = []
company = "AAPL"

def get_data(symb):
    # Returns a an numpy array of the closing prices of the past 1 year
    market_data = api.get_bars(symb, TimeFrame.Day,(date.today()-timedelta(weeks=260)), date.today()-timedelta(days=1), adjustment='raw').df
    my_columns = ['Imp vol','200 ema','72 ema','30 ema', '20 ema']
    market_data = market_data.reset_index()
    stock_data = market_data.copy().drop(['trade_count'],axis=1)
    symbol, nulls, tradeable = [], [], []
    for x in range(len(stock_data.index)):
        symbol.append(symb)
        nulls.append(np.nan)
        tradeable.append(True)    
    stock_data.insert(1, "symbol", pd.Series(data=symbol))
    stock_data.insert(2, "tradeable", pd.Series(data=tradeable))
    for x in my_columns:
         stock_data[x] = pd.Series(data=nulls)
    
    return stock_data

def technicals(data):
    MAtime = ['200', '72', '30', '20']
    BB_period = 20
    #Exp Moving Average Calculations:
    for x in MAtime:
        data[x + ' ema'] = data['close'].ewm(span=int(x), adjust=False).mean()
    #pd.set_option('display.max_rows', None)
    #pd.set_option('display.max_columns', None)
    #Bollinger bands Calculations 
    data['std'] = data['close'].rolling(BB_period).std()
    data['upper_bollinger']= data['20 ema'] + (2 * data['std'])
    data['lower_bollinger']= data['20 ema'] - (2 * data['std'])
    return data

def fibonacci(data):
    if 'Primary_Fiblevel' in data.columns:
        data.drop(['Primary_Fiblevel', 'Second_Fiblevel'],axis=1)
    #Fibonacci calculations 
    Fibs = dict()
    Fiblist = []
    yearlyhigh = data['high'].max()
    yearlylow = data['low'].min()
    diff = yearlyhigh - yearlylow
    Fibs['Fib_lvl_max'] = yearlyhigh + (diff * 0.236) #Fib161_lvl
    Fibs['Fib_lvl_one_hundred'] = yearlyhigh #'Fib_100_lvl'
    Fibs['Fib_lvl_seventy_eight'] = yearlyhigh - (diff * .214) #'Fib_78_lvl'
    Fibs['Fib_lvl_sixty_one'] = yearlyhigh - (diff * .382) # 'Fib_61_lvl'
    Fibs['Fib_lvl_fifty'] = yearlyhigh - (diff * .50) # 'Fib_50_lvl'
    Fibs['Fib_lvl_thirty_eight'] = yearlyhigh - (diff  * .618)# 'Fib_38_lvl'
    Fibs['Fib_lvl_twenty_three'] = yearlyhigh - (diff * .763) # 'Fib_23_lvl'
    Fibs['Fib_lvl_zero'] = yearlylow #Fib_zero_lvl
    data['Primary_Fiblevel'] = np.nan 
    data['Second_Fiblevel'] = np.nan
    for key, value in Fibs.items():
        Fiblist.append(value)
    Fiblist = sorted(Fiblist)
    for x in range(len(data.index)):
        for order, level in enumerate(Fiblist):
            if data.at[x, 'close'] < level:
                data.at[x,'Primary_Fiblevel'] = Fiblist[order-1]
                data.at[x,'Second_Fiblevel'] = Fiblist[order-2]
                if data.at[x,'Primary_Fiblevel'] <= data.at[x,'Second_Fiblevel']:
                     data.at[x,'Second_Fiblevel'] = np.nan 
                break 
    return data

def update_data(data, price_bought_at):
    count = 0
    for row in range(len(data)-1, 1 ,-1):
        if data.at[row,'Primary_Fiblevel'] >= price_bought_at:
            data.at[row,'Tradeable'] = False
            count += 1 
            if count >= 10:
                break 
    rev_data = data 
    return rev_data 


    return stuff

def buy(stock, qnty, limitprice):
    try:
        api.submit_order(
            symbol=str(stock),
            side='buy',
            type='limit',
            qty=qnty,
            time_in_force='gtc',
            order_class='bracket',
            limit_price= limitprice,
            take_profit=dict(
                limit_price=int(1.5 * limitprice),
            ),
            stop_loss=dict(
                stop_price=int(.85 * limitprice),
            ))
        print(f'{stock} Buy Order Confirmed')
        confirm = True
    except: 
        print(f'{stock} Buy Order failed....Try again comrade')
        confirm = False 
    return confirm

def check_sell_orders(stock_name):
    sell_order_present = False
    open_orders = api.list_orders(
       status='open',
       limit=100,
       nested=True)# show nested multi-leg orders
    for order in open_orders:
        if order.symbol == stock_name and order.side =='sell':
            sell_order_present = True
            break 
    return sell_order_present

def sell(stock, qty) :
   #Checking if a sell order or trailing order already present
   if check_sell_orders(stock):
        confirm = f'Sell order for {stock} already present'
   else:
    api.submit_order(
        symbol= stock,
        qty= qty,
        side='buy',
        type='market',
        time_in_force='day')
    confirm = f'Sell Order for {stock} submitted'

    return confirm 
    
def account():
    account = api.get_account()
    portfolio =  api.list_positions()
    if account.trading_blocked:
        print('Account is currently restricted from trading.')
    else:
        #print("SEE ACCOUNT DETAILS BELOW:")
        balance_change = float(account.equity) - float(account.last_equity)
        balance_change = "{:.2f}".format(balance_change)
       # print(f'Today portfolio P/L: {balance_change}')
    return account and portfolio
    
def market_hours():
    clock = api.get_clock()
    clock.is_open
    while not clock.is_open:
        time_to_open = (clock.next_open - clock.timestamp).total_seconds()
        hours_minutes = str(datetime.timedelta(seconds =time_to_open))
        print(f'The market is closed.. Market will open in {hours_minutes}....Athena will take a nap')
        time.sleep(60)
    else:
        print("Market is open...we are live")
        return  clock.is_open


def run_connection(conn):
    try:
        conn.run()
    except KeyboardInterrupt:
        print("Interrupted execution by user")
        loop.run_until_complete(conn.stop_ws())
        exit(0)
    except Exception as e:
        print(f'Exception from websocket connection: {e}')
    finally:
        print("Trying to re-establish connection")
        time.sleep(3)
        run_connection(conn)

def backtest():
    print("Backtest feature still under construction")


def Trading_logic(asset: str):
    global conn
    stock_name = asset
    conn = Stream(pap_key,
                    pap_secret,
                    base_url=BASE_URL,
                    data_feed=data_feed)
    risk_per_trade = float(.01)
    account_info = api.get_account()
    standard_qty =math.ceil(risk_per_trade * int(float(account_info.non_marginable_buying_power)))
    stock_info = get_data(asset) 
    stock_data = technicals(stock_info)
    data = fibonacci(stock_data)
    first_fib_level = round(data.at[len(data.index)-1, 'Primary_Fiblevel'])
    if first_fib_level <= 0.0 or first_fib_level == np.nan:
        first_fib_level = round(data.at[len(data.index)-15, 'Primary_Fiblevel'])
    global recent_buys 



    async def bar_callback(asset):
        nonlocal data, first_fib_level, standard_qty, stock_name
        print("number of recent buys:", len(recent_buys))
        #print("Primary Fib level: ",first_fib_level )
        if len(recent_buys) <= 2:
            if asset.low <= round(data.at[len(data.index)-1, '200 ema']) or asset.low <= first_fib_level:
                print(data.at[len(data.index)-1, 'tradeable'])
                if data.at[len(data.index)-1, 'tradeable'] == True:
                    print("trade conditions met")
                    status = buy(stock_name, standard_qty, first_fib_level)
                    if status:
                        recent_buys.append(1)
                        print("added trade to Recent_buys...Recent_buys now:",len(recent_buys))
                        new_data = update_data(data, first_fib_level)
                        data = fibonacci(new_data)
                    else:
                        pass 
            else:
                print("Condition not met....waiting")
        else: 
            print("too many recent buys for this position...athena will no longer trade this")
        
    conn.subscribe_bars(bar_callback, asset)
    run_connection(conn)
        

'''CODE TO RUN TRADING ALGO'''

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s  %(levelname)s %(message)s',
                        level=logging.INFO)
    while True:
        try:
            Market_hours = market_hours()
            if Market_hours: 
                pool = ThreadPoolExecutor(1)
                pool.submit(Trading_logic(company))
                time.sleep(20)
                conn.stop
                time.sleep(20)
            else: 
                print("Market is temporarily closed or an error occurred")
            
        except Exception as e:
            print("Error found within Trading Algo", e)
            exception_type, exception_object, exception_traceback = sys.exc_info()
            filename = exception_traceback.tb_frame.f_code.co_filename
            line_number = exception_traceback.tb_lineno

            print("Exception type: ", exception_type)
            print("File name: ", filename)
            print("Line number: ", line_number)
            break

        except KeyboardInterrupt:
            print("Algo interrupted by keyboard")
            try: 
                conn.stop()
            except: 
                quit()
            value = input("What stock would you like info on: ")
            if value == "repair" or value == "exit":
                print('Exiting Algo...Please peform upgrades or repairs on trading algo')
                break
            elif value == "account":
                print(account())
            else:
                try:
                    asset = api.get_asset(f'{value}')
                    if  asset.tradable: 
                        company = str(value)
                        recent_buys.clear()
                    else:
                        print(f'asset {value} not tradeable')
                except: 
                    print("command invalid...restarting algo")
