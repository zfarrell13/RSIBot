import os
import json
import boto3
import numpy as np
import ta
import alpaca_trade_api as api
import datetime
# import smtplib
# from email.mime.text import MIMEText


s3 = boto3.client('s3')

API_KEY = os.environ['API_KEY']
SECRET_KEY = os.environ['SECRET_KEY']
# smtp_port = os.environ['smtp_port']
# smtp_server = os.environ['smtp_server']
# sender_email = os.environ['sender_email']
# sender_password = os.environ['sender_password']
# recipient_email = os.environ['recipient_email']

alpaca = api.REST(API_KEY, SECRET_KEY)

days = 91
symbols = ["AAPL", "GOOG", "AMZN"]
timeframe = "1Day"
start_date = datetime.date.today() - datetime.timedelta(days=days)
start = start_date.strftime("%Y-%m-%d")
end_date = datetime.date.today() - datetime.timedelta(days=1)
end = end_date.strftime("%Y-%m-%d")

symbol_bars = {}
for symbol in symbols:
    bars = alpaca.get_bars(symbol, timeframe, start, end).df
    symbol_bars[symbol] = bars

def optimize_rsi_thresholds(symbol):
    possible_thresholds = range(30, 70)
    possible_windows = range(5, 21)

    optimal_overbought = None
    optimal_oversold = None
    optimal_window = None
    max_total_return = -np.inf

    for overbought in possible_thresholds:
        for oversold in possible_thresholds:
            if overbought <= oversold:
                continue
            for window in possible_windows:
                rsi = ta.momentum.RSIIndicator(symbol_bars[symbol]['close'], window=window).rsi()
                symbol_bars[symbol]['sell_points'] = np.where((rsi > overbought) & (rsi.shift(1) <= overbought), 1, 0)
                symbol_bars[symbol]['buy_points'] = np.where((rsi < oversold) & (rsi.shift(1) >= oversold), 1, 0)

                position = None
                entry_date = None
                entry_price = None
                exit_date = None
                exit_price = None
                returns = []

                for i, row in symbol_bars[symbol].iterrows():
                    if row['buy_points'] == 1 and position is None:
                        position = 'long'
                        entry_date = i
                        entry_price = row['close']
                    elif row['sell_points'] == 1 and position == 'long':
                        position = None
                        exit_date = i
                        exit_price = row['close']
                        trade_return = (exit_price - entry_price) / entry_price
                        returns.append(trade_return)

                if position == 'long':
                    exit_date = symbol_bars[symbol].index[-1]
                    exit_price = symbol_bars[symbol]['close'].iloc[-1]
                    trade_return = (exit_price - entry_price) / entry_price
                    returns.append(trade_return)

                total_return = np.prod(np.array(returns) + 1) - 1

                if total_return > max_total_return:
                    max_total_return = total_return
                    optimal_overbought = overbought
                    optimal_oversold = oversold
                    optimal_window = window

    return optimal_overbought, optimal_oversold, optimal_window

# def invoke_another_lambda(optimal_values, symbols):
#     lambda_client = boto3.client('lambda')

#     payload = {
#         'optimal_values': optimal_values,
#         'symbols': symbols
#     }

#     response = lambda_client.invoke(
#         FunctionName='<ANOTHER_LAMBDA_FUNCTION_NAME>',
#         InvocationType='RequestResponse', # Or Event
#         Payload=json.dumps(payload)
#     )

#     return response

def lambda_handler(event, context):
    optimal_values = {}
    for symbol in symbols:
        optimal_overbought, optimal_oversold, optimal_window = optimize_rsi_thresholds(symbol)
        optimal_values[symbol] = (optimal_overbought, optimal_oversold, optimal_window)

    # message = f"Here are todays optimal_overbought, optimal_oversold, optimal_window values for {symbols}. {optimal_values}"

    # msg = MIMEText(message)
    # msg['Subject'] = 'Alpaca Bot Notification'
    # msg['From'] = sender_email
    # msg['To'] = recipient_email

    # server = smtplib.SMTP(smtp_server, smtp_port)
    # server.starttls()
    # server.login(sender_email, sender_password)
    # server.sendmail(sender_email, recipient_email, msg.as_string())
    # server.quit()

    # invoke_another_lambda(optimal_values, symbols)

    # Serialize the dictionary to a JSON formatted string
    json_data = json.dumps(optimal_values)

    # Save the JSON data to a file
    with open('/tmp/optimal_values.json', 'w') as file:
        file.write(json_data)

    # Upload the file to the specified S3 bucket
    bucket_name = 'rsi-bot-data-bucket'
    s3.upload_file('/tmp/optimal_values.json', bucket_name, 'optimal_values.json')

    # Return a message with the status
    return {
        'statusCode': 200,
        'body': json.dumps('optimal_values.json uploaded to S3 successfully!')
    }