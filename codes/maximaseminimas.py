# -*- coding: utf-8 -*-
"""maximaseminimas.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1YVNu6SOus_th83iQL-oxCWr3uFDumisl
"""



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
 
def getmin():
   df = get_minute_data('ATOMUSDT','1h', '10 hours')
   donchianlow= ta.volatility.donchian_channel_lband(high = df['High'],low = df['Low'], close = df['Close'],window = 3)
   donchianlow.columns = ['Time','Khband']
   return donchianlow[-1]


def getmax():
  df = get_minute_data('ATOMUSDT','1h', '10 hours')
  donchianhigh = ta.volatility.donchian_channel_hband(high = df['High'],low = df['Low'], close = df['Close'],window = 3)
  donchianhigh.columns = ['Time','Khband']
  
  return donchianhigh[-1]


def keltner():
  df = get_minute_data('ATOMUSDT','1h', '30 hours')
  ATR = ta.volatility.average_true_range(high = df['High'],low = df['Low'], close = df['Close'],window = 10)
  EMA = ta.trend.ema_indicator(df['Close'], 20)
  keltnerhigh = EMA[-1] + (ATR[-1]*0.38)
  keltnerlow = EMA[-1] - (ATR[-1]*0.38)
  if df['Close'][-1] > keltnerlow and df['Close'][-1] > keltnerhigh:
    return
  else:
    print('preços abaixo das bandas de kelner ,aguardando 60s')
    time.sleep(60)


def maxmin():
    print(getmin())
    getmininicio = getmin()
    qty_compra = round(80/getmin(),2)
    print(qty_compra)

    #estrategia
    #ordem de compra no donchianlow
    if keltner():
      open_position = False
      if open_position == False:
        try:
          buy_limit = client.create_order(symbol='ATOMUSDT', side='BUY', type='LIMIT', timeInForce='GTC', quantity=qty_compra , price= getmininicio)
        #buy_order = client.create_test_order(symbol='ATOMUSDT', side='BUY', type='LIMIT', quantity= qty_compra, price = final['dclband'][-1], timeInForce='GTC')
          print(buy_limit)

          # #ORdem que estava no stack  / order = client.order_limit_sell(symbol=pair,quantity=quantity,price=sellPrice)
          orderId = buy_limit["orderId"]
          print('Buy order placed at {}\n'.format(getmininicio))
          key = True
          while key:
              currentOrder = client.get_order(symbol='ATOMUSDT',orderId=orderId)
              getmin()
              time.sleep(60)
              getmax()
              time.sleep(60)
              #caso onde a ordem é preenchida
              if currentOrder['status']=='FILLED':
                  print("Bought: {} at {}".format(qty_compra,getmininicio))
                  time.sleep(20)
                  open_position = True 
                  #comprado

                  while open_position:
                    #coloca ordem na maxima
                    contador = 0 

                    if contador  >= 5:
                      print('stopado por tempo')
                      market_order = client.create_order(symbol='ATOMUSDT',
                                      side='SELL',
                                      type='MARKET',
                                      quantity = qty_compra)

                    maxinicio = getmax()
                    sell_limit = client.create_order(symbol='ATOMUSDT', side='SELL', type='LIMIT', timeInForce='GTC', quantity=qty_compra , price= maxinicio)
                    print('Sell order placed at {}\n'.format(maxinicio))
                    orderIdComprado = sell_limit["orderId"]
                    ordem_setada = True
                    while ordem_setada:

                        #caso onde a ordem de venda é preenchida
                        currentOrderComprado = client.get_order(symbol='ATOMUSDT',orderId=orderIdComprado)
                        if currentOrderComprado['status'] == 'FILLED':
                          print('Venda feita: {} em {}'.format(qty_compra,sell_limit['price']))
                          open_position = False
                          key = False
                          break

                        #caso onde a ordem de venda tem que se atualizar
                        if getmax() < maxinicio:
                          time.sleep(20)
                          cancelvenda = client.cancel_order(symbol='ATOMUSDT', orderId=sell_limit['orderId'])
                        
                          print(cancelvenda)
                          print(f'Ordem cancelada , preço de saida estava em {maxinicio} e maxima atualizou para {getmax()}')
                          #caso nao funcione, tentar colocar nova ordem dentro desse if e manter o loop
                          contador +=1
                          open_position = True
                          ordem_setada = False
                        
              #caso onde o preço minimo atualiza
              if getmin() > getmininicio:
                time.sleep(20)
                cancel = client.cancel_order(symbol='ATOMUSDT', orderId=buy_limit['orderId'])
                print(cancel)
                print(f'Ordem cancelada , preço de entrada estava em {getmininicio} e minima atualizou para {getmin()}')
                open_position = False
                print(".")
                break
            


        except  BinanceAPIException as e:
              # error handling goes here
                print(e)
        except BinanceOrderException as e:
            # error handling goes here
                print(e)

while True:
    maxmin()