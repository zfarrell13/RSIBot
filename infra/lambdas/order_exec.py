import os
import boto3
import json
import ta
import time
import alpaca_trade_api as api
from alpaca.trade.client import TradingClient

# Read keys from Lambda environment variables
API_KEY = os.environ['API_KEY']
SECRET_KEY = os.environ['SECRET_KEY']
BASE_URL = os.environ['BASE_URL']

alpaca = api.REST(API_KEY, SECRET_KEY, BASE_URL)
trading_client = TradingClient(API_KEY, SECRET_KEY, paper=True)
account = trading_client.get_account()

TIMEFRAME = "1Min"
QTY = 6

symbols = ["AAPL", "GOOG", "AMZN"]

def get_current_prices(symbols):
    current_prices = {}
    for symbol in symbols:
        bars = alpaca.get_bars(symbol, TIMEFRAME, limit=1)
        for bar in bars:
            if symbol in symbols:
                current_price = bar.c
                current_prices[symbol] = current_price
                break
        else:
            print(f"No price data available for {symbol}")
    return current_prices

def execute_trades(SYMBOLS, current_prices, optimal_values):
        # Get the optimal RSI values for each symbol
        optimal_values_local = optimal_values
        print(f"Current thresholds: {optimal_values_local}")

        for symbol in SYMBOLS:
            # Get the current prices for the symbol
            price = current_prices[symbol]
            print(f"Current price for {symbol}: {price}")

            # Get the current RSI for the symbol
            bars = alpaca.get_bars(symbol, TIMEFRAME, limit=21).df
            rsi = ta.momentum.RSIIndicator(bars['close'], window=optimal_values_local[symbol][2]).rsi()
            current_rsi = rsi.iloc[-1]

            # Get the optimal RSI values for the symbol
            optimal_overbought, optimal_oversold, _ = optimal_values_local[symbol]

            # Get the current position in the symbol
            try:
                position = trading_client.get_open_position(symbol)
            except api.rest.APIError as e:
                print(f"Error getting position for {symbol}: {e}")
                continue

            if not position:
                print(f"No position for {symbol} in SYMBOLS")
                continue

            # Execute a sell order if the current RSI is above the overbought threshold
            if current_rsi > optimal_overbought and position:
                try:
                    alpaca.submit_order(
                        symbol=symbol,
                        qty=QTY,
                        side='sell',
                        type='market',
                        time_in_force='gtc'
                    )
                    message1h = f"Selling {QTY} shares of {symbol} at {current_prices[symbol]} because {symbol} passed above the optimal_overbought threshold of {optimal_overbought}."
                    print(message1h)
                except Exception as e:
                    message1s = f"Error selling {QTY} shares of {symbol}: {str(e)}"
                    print(message1s)
                    continue
            else:
                if not position:
                    print(f"Tried to sell {symbol}, but no position to sell")
                    continue

            # Execute a buy order if the current RSI is below the oversold threshold
                elif current_rsi < optimal_oversold:
                    try:
                        # Get account information
                        account = alpaca.get_account()
                        # Calculate the quantity of shares to buy based on available funds
                        buying_power = float(account.buying_power)
                        price = float(current_prices[symbol])
                        qty_buy = int(buying_power / price)

                        if qty_buy >= 1:
                            alpaca.submit_order(
                                symbol=symbol,
                                qty=qty_buy,
                                side='buy',
                                type='market',
                                time_in_force='gtc'
                            )
                            message2h = f"Buying {qty_buy} shares of {symbol} at {price} because {symbol} passed below the optimal_oversold threshold of {optimal_oversold}"
                            print(message2h)
                        else:
                            message2s = f"Not enough funds to buy {symbol} at {price}. Your current account balance is {buying_power}"
                            print(message2s)
                    except Exception as e:
                        message2e = f"Error buying {symbol}: {str(e)}"
                        print(message2e)

        # Wait for 1 minute before executing trades again
        print("Sleeping for 60 seconds...")
        time.sleep(60)
print('${} is available as buying power.'.format(account.buying_power))


def lambda_handler(event, context):
    # Get the payload from rsi optimization Lambda
    # payload = event['Payload']
    optimal_values = payload['optimal_values']
    # symbols = payload['symbols']
    
    current_prices = get_current_prices(symbols)
    execute_trades(symbols, current_prices, optimal_values)

    return {
        'statusCode': 200,
        'body': json.dumps('Execution completed')
    }