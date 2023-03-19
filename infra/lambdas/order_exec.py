import alpaca_trade_api as api
from alpaca.trading.client import TradingClient
from keys2 import API_KEY, SECRET_KEY, base_url, smtp_port, smtp_server, sender_email, sender_password, recipient_email
import ta
import time
import threading
import smtplib
from email.mime.text import MIMEText
from rsi_optimizations import optimal_values, symbols
from datetime import datetime, timedelta

alpaca = api.REST(API_KEY, SECRET_KEY, base_url)
trading_client = TradingClient(API_KEY, SECRET_KEY, paper=True)
account = trading_client.get_account()

# Constants
SYMBOLS = symbols
TIMEFRAME = "1Min"
QTY = 6

# Function to get the current price of a list of symbols
def get_current_prices(symbols):
    current_prices = {}
    for symbol in symbols:
        # Get the most recent bar for the symbol
        bars = alpaca.get_bars(symbol, TIMEFRAME, limit=1)
        for bar in bars:
            if symbol in symbols:
                current_price = bar.c
                current_prices[symbol] = current_price
                # print(f"Current price for {symbol}: {current_price}")
                break
        else:
            print(f"No price data available for {symbol}")
    return current_prices

# Function to execute trades based on RSI
def execute_trades(SYMBOLS, current_prices):
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


# Continuously run the bot
if __name__ == '__main__':
    while True:
        current_time = datetime.now()
        # Get the current time
        # current_time = datetime.now()
        print("Current time: ", current_time.time())

        # If it's during market hours, run the bot
        if current_time.time() >= datetime.strptime("09:30", "%H:%M").time() and \
            current_time.time() <= datetime.strptime("16:30", "%H:%M").time():
            print("Current time: ", current_time.time())
            print("Market hours. Running bot...")
            # Get the optimal RSI values for each symbol
            # opt_values = optimal_values

            # Get the current prices for the symbols
            current_prices = get_current_prices(SYMBOLS)

            # Execute trades based on RSI using the current prices and optimal RSI values
            execute_trades(SYMBOLS, current_prices)

        # Wait for 60 seconds before checking prices again
        # print("Sleeping for 60 seconds...")
        # time.sleep(60)
        else:
        # If it's not during market hours, wait for 10 minutes before checking again
            print("Market is closed. Waiting for 10 minutes...")
            time.sleep(600)
