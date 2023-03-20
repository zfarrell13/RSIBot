import numpy as np
import ta
import alpaca_trade_api as api
import datetime
import time
import threading
from datetime import datetime


def lambda_handler(event, context):
    print(event)
