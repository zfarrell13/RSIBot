import numpy as np
import ta
import alpaca_trade_api as api
import datetime
import time
import threading
from datetime import datetime
import json
import boto3

client = boto3.client('lambda')

def lambda_handler(event, context):
   inputForInvoker = {'Id': '1', 'rsi': 100 }

	
   response = client.invoke(
		FunctionName='rsi-order-exec-function',
		InvocationType='RequestResponse', # Or Event
		Payload=json.dumps(inputForInvoker)
		)

   responseJson = json.load(response['Payload'])

   print(responseJson)