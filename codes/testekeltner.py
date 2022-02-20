from binance import Client
import pandas as pd
import numpy as np
import time
import ta
import matplotlib

from binance.enums import *
from binance.exceptions import BinanceAPIException, BinanceOrderException

client = Client("N1rc9N8fYRn1Oyb9yoKIGwUIf3tUwVBxI5EyhkpC1blxeFG451qoCfMVNO0ES6Kl", "DZXKpom2aQ0lL0r9r9vXufvDBsRXV5vkP1L9IxsbQ5wg9CMJLSzJzTMLltQ80Yfo")

def get_minute_data(ticker, interval, lookback):
      dados =  pd.DataFrame(client.get_historical_klines(ticker, interval , lookback +' ago UTC'))
      dados = dados.iloc[:,:6]
      dados.columns = ['Time','Open','High','Low','Close','Volume']
      dados = dados.set_index('Time')
      dados.index = pd.to_datetime(dados.index, unit='ms')
      dados = dados.astype(float)
    
      return dados

def dadoscandle():
    df = get_minute_data('ATOMUSDT','1h', '10 hours')

    ind = ta.volatility.keltner_channel_hband_indicator(high = df['High'],low = df['Low'], close = df['Close'])
    donchianlow= ta.volatility.donchian_channel_lband(high = df['High'],low = df['Low'], close = df['Close'],window = 3)
    donchianlow.columns = ['Time','Khband']
    donchianhigh = ta.volatility.donchian_channel_hband(high = df['High'],low = df['Low'], close = df['Close'],window = 2)
    final = pd.merge(df, donchianlow,how = 'left', on = 'Time')
    final = pd.merge(final, donchianhigh, how='left', on='Time')
    qty_compra = round(58/final['dclband'][-1],4)
    return final
def keltner():
  df = get_minute_data('ATOMUSDT','1h', '30 hours')
  ATR = ta.volatility.average_true_range(high = df['High'],low = df['Low'], close = df['Close'],window = 10)
  EMA = ta.trend.ema_indicator(df['Close'], 20)
  keltnerhigh = EMA[-1] + (ATR[-1]*0.38)
  keltnerlow = EMA[-1] - (ATR[-1]*0.38)
  return keltnerlow,keltnerhigh


print(keltner())
kt = keltner()
print(type(kt))
print(kt[-1])