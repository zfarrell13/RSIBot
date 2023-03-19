import numpy as np
import ta
import alpaca_trade_api as api
from keys2 import API_KEY, SECRET_KEY, smtp_port, smtp_server, sender_email, sender_password, recipient_email
import datetime
import time
import threading
import smtplib
from email.mime.text import MIMEText

alpaca = api.REST(API_KEY, SECRET_KEY)

# Setting parameters before calling method
time_sleep = 86400
days = 91
symbols = ["AAPL", "GOOG", "AMZN"]
timeframe = "1Day"
start_date = datetime.date.today() - datetime.timedelta(days=days)
start = start_date.strftime("%Y-%m-%d")
end_date = datetime.date.today() - datetime.timedelta(days=1)
end = end_date.strftime("%Y-%m-%d")

# Retrieve daily bars for all symbols in a dictionary and print the first 5 rows for each symbol
symbol_bars = {}
for symbol in symbols:
    bars = alpaca.get_bars(symbol, timeframe, start, end).df
    symbol_bars[symbol] = bars
    # print(symbol_bars[symbol])

# Create RSI optimization funciton
def optimize_rsi_thresholds(symbol):
    # Define a range of possible values for overbought and oversold thresholds and window sizes
    possible_thresholds = range(30, 70)
    possible_windows = range(5, 21)

    # Initialize variables to store the optimal thresholds and the corresponding total return
    optimal_overbought = None
    optimal_oversold = None
    optimal_window = None
    max_total_return = -np.inf

    # Iterate through all possible combinations of thresholds and window sizes and calculate the total return for each combination
    for overbought in possible_thresholds:
        for oversold in possible_thresholds:
            # Make sure that the overbought threshold is greater than the oversold threshold
            if overbought <= oversold:
                continue
            for window in possible_windows:
                # Calculate RSI using the current threshold and window values
                rsi = ta.momentum.RSIIndicator(symbol_bars[symbol]['close'], window=window).rsi()
                symbol_bars[symbol]['sell_points'] = np.where((rsi > overbought) & (rsi.shift(1) <= overbought), 1, 0)
                symbol_bars[symbol]['buy_points'] = np.where((rsi < oversold) & (rsi.shift(1) >= oversold), 1, 0)

                # Initialize variables
                position = None
                entry_date = None
                entry_price = None
                exit_date = None
                exit_price = None
                returns = []

                # Iterate through each row in the DataFrame
                for i, row in symbol_bars[symbol].iterrows():
                    # If there is a new buy signal and we are not already in a long position
                    if row['buy_points'] == 1 and position is None:
                        position = 'long'
                        entry_date = i
                        entry_price = row['close']
                    # If there is a new sell signal and we are currently in a long position
                    elif row['sell_points'] == 1 and position == 'long':
                        position = None
                        exit_date = i
                        exit_price = row['close']
                        trade_return = (exit_price - entry_price) / entry_price
                        returns.append(trade_return)

                # If we are still in a long position at the end of the DataFrame, calculate returns based on the last price
                if position == 'long':
                    exit_date = symbol_bars[symbol].index[-1]
                    exit_price = symbol_bars[symbol]['close'].iloc[-1]
                    trade_return = (exit_price - entry_price) / entry_price
                    returns.append(trade_return)

                # Calculate total return for the current threshold and window values
                total_return = np.prod(np.array(returns) + 1) - 1

                # Update optimal threshold and window values if current total return is greater than the current maximum
                if total_return > max_total_return:
                    max_total_return = total_return
                    optimal_overbought = overbought
                    optimal_oversold = oversold
                    optimal_window = window

    return optimal_overbought, optimal_oversold, optimal_window

# Call the optimize_rsi_thresholds() function for each symbol and assign its return values to a dictionary
optimal_values = {}
for symbol in symbols:
    optimal_overbought, optimal_oversold, optimal_window = optimize_rsi_thresholds(symbol)
    optimal_values[symbol] = (optimal_overbought, optimal_oversold, optimal_window)

# Define a function to run the optimization function for all symbols every 2.5 minutes
def optimize_rsi():
    while True:
        for symbol in symbols:
            # Retrieve the full amount of bars necessary for the optimization calculation
            start_date = datetime.date.today() - datetime.timedelta(days=days)
            start = start_date.strftime("%Y-%m-%d")
            end_date = datetime.date.today() - datetime.timedelta(days=1)
            end = end_date.strftime("%Y-%m-%d")
            bars = alpaca.get_bars(symbol, timeframe, start, end).df
            
            # Call the optimize_rsi_thresholds() function for the symbol and update optimal_values
            optimal_overbought, optimal_oversold, optimal_window = optimize_rsi_thresholds(symbol)
            optimal_values[symbol] = (optimal_overbought, optimal_oversold, optimal_window)
        # message = f"Here are todays optimal_overbought, optimal_oversold, optimal_window values for {symbols}.  {optimal_values}"
        # print(optimal_values)
        # Set up email message and send using SMTP server
        # msg = MIMEText(message)
        # msg['Subject'] = 'Alpaca Bot Notification'
        # msg['From'] = sender_email
        # msg['To'] = recipient_email

        # server = smtplib.SMTP(smtp_server, smtp_port)
        # server.starttls()
        # server.login(sender_email, sender_password)
        # server.sendmail(sender_email, recipient_email, msg.as_string())
        # server.quit()

        # Wait for 24 hours before running the optimization function again
        time.sleep(time_sleep)

# Start the optimization thread to run the optimization function for all symbols every 10 minutes
optimization_thread = threading.Thread(target=optimize_rsi)
optimization_thread.start()

