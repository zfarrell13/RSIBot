import os
import boto3
import json
import ta
import time
import alpaca_trade_api as tradeapi
import pandas as pd

# Read keys from Lambda environment variables
API_KEY = os.environ['API_KEY']
SECRET_KEY = os.environ['SECRET_KEY']
BASE_URL = os.environ['BASE_URL']
SYMBOLS = os.environ['SYMBOLS']

api = tradeapi.REST(API_KEY, SECRET_KEY, BASE_URL)
account = api.get_account()

TIMEFRAME = "1Min"
QTY = 6

symbols = [symbol for symbol in SYMBOLS.split(",") if symbol]
# symbols = ["AAPL", "GOOG", "AMZN"]

# Initialize a boto3 S3 client
s3 = boto3.client('s3')

def get_current_prices(symbols):
    current_prices = {}
    for symbol in symbols:
        # Get the most recent bar for the symbol
        bars = api.get_bars(symbol, TIMEFRAME, limit=1)
        for bar in bars:
            if symbol in symbols:
                current_price = bar.c
                current_prices[symbol] = current_price
                # print(f"Current price for {symbol}: {current_price}")
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
        bars = api.get_bars(symbol, TIMEFRAME, limit=21)
        if bars:
            close_prices = [bar.c for bar in bars]
            rsi = ta.momentum.RSIIndicator(pd.Series(close_prices), window=optimal_values_local[symbol][2]).rsi()
            
            # Check if the RSI Series is not empty
            if not rsi.empty:
                current_rsi = rsi.iloc[-1]
            else:
                print(f"Insufficient data for RSI calculation for {symbol}")
                continue

            # Get the optimal RSI values for the symbol
            optimal_overbought, optimal_oversold, _ = optimal_values_local[symbol]

            # Get the current position in the symbol
            try:
                position = api.get_position(symbol)
            except tradeapi.rest.APIError as e:
                print(f"Error getting position for {symbol}: {e}")
                continue

            if not position:
                print(f"No position for {symbol} in SYMBOLS")
                continue

            # Execute a sell order if the current RSI is above the overbought threshold
            if current_rsi > optimal_overbought and position:
                try:
                    api.submit_order(
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
                        account = api.get_account()
                        # Calculate the quantity of shares to buy based on available funds
                        buying_power = float(account.buying_power)
                        price = float(current_prices[symbol])
                        qty_buy = int(buying_power / price)

                        if qty_buy >= 1:
                            api.submit_order(
                                symbol=symbol,
                                qty=qty_buy,
                                side='buy',
                                type='market',
                                time_in_force='gtc'
                            )
                            message2h = f"Buying {qty_buy} shares of {symbol} at {price} because {symbol} passed below the optimal_oversold threshold of {optimal_oversold}"
                            print(message2h)
                        else:
                            message2s = f"Not enough buying power to purchase shares of {symbol}"
                            print(message2s)
                    except Exception as e:
                        message2f = f"Error buying {qty_buy} shares of {symbol}: {str(e)}"
                        print(message2f)
                        continue
                else:
                    message3 = f"{symbol} is within RSI thresholds: {optimal_oversold} - {optimal_overbought}. No action taken."
                    print(message3)
        else:
            print(f"No data available for {symbol}")

print(f'${account.buying_power} is available as buying power.')

def get_optimal_values_from_s3(bucket_name, key):
    # Download the JSON file from the S3 bucket
    s3.download_file(bucket_name, key, '/tmp/optimal_values.json')
    
    # Read the JSON data from the file
    with open('/tmp/optimal_values.json', 'r') as file:
        json_data = file.read()
        
    # Deserialize the JSON data into a dictionary
    optimal_values = json.loads(json_data)
    
    return optimal_values

def lambda_handler(event, context):
    # Call the function to get the optimal_values dictionary
    bucket_name = 'rsi-bot-data-bucket'
    key = 'optimal_values.json'
    optimal_values = get_optimal_values_from_s3(bucket_name, key)
    
    current_prices = get_current_prices(symbols)

    execute_trades(symbols, current_prices, optimal_values)
    
    return {
        'statusCode': 200,
        'body': json.dumps('Execution completed')
    }