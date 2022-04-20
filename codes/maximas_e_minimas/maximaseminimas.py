


from binance import Client
import pandas as pd
import numpy as np
import time
import ta
import matplotlib
from secret import secret1, secret2
from binance.enums import *
from binance.exceptions import BinanceAPIException, BinanceOrderException

client = Client(secret1, secret2)

while True:
    maxmin('ATOMUSDT','1h','30 hours')