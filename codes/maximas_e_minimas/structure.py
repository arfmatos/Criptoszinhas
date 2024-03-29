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


# def dadoscandle(): 
#     df = get_minute_data('ATOMUSDT','1h', '10 hours')

    # ind = ta.volatility.keltner_channel_hband_indicator(high = df['High'],low = df['Low'], close = df['Close'])
    # donchianlow= ta.volatility.donchian_channel_lband(high = df['High'],low = df['Low'], close = df['Close'],window = 3)
    # donchianlow.columns = ['Time','Khband']
    # donchianhigh = ta.volatility.donchian_channel_hband(high = df['High'],low = df['Low'], close = df['Close'],window = 2)
    # final = pd.merge(df, donchianlow,how = 'left', on = 'Time')
    # final = pd.merge(final, donchianhigh, how='left', on='Time')
    # qty_compra = round(58/final['dclband'][-1],4)
    # return final

def get_minute_data(ticker, interval, lookback):
      dados =  pd.DataFrame(client.get_historical_klines(ticker, interval , lookback +' ago UTC'))
      dados = dados.iloc[:,:6]
      dados.columns = ['Time','Open','High','Low','Close','Volume']
      dados = dados.set_index('Time')
      dados.index = pd.to_datetime(dados.index, unit='ms')
      dados = dados.astype(float)
    
      return dados

def getmin(ticker, timeframe , timeago):
   df = get_minute_data(ticker,timeframe,timeago)
   donchianlow= ta.volatility.donchian_channel_lband(high = df['High'],low = df['Low'], close = df['Close'],window = 5)
   donchianlow.columns = ['Time','Khband']
   return donchianlow[-1]

def getmax(ticker,timeframe,timeago):
  df = get_minute_data(ticker,timeframe,timeago)
  donchianhigh = ta.volatility.donchian_channel_hband(high = df['High'],low = df['Low'], close = df['Close'],window = 4)
  donchianhigh.columns = ['Time','Khband']
  
  return donchianhigh[-1]

def keltner(ticker,timeframe,timeago):
  df = get_minute_data(ticker ,timeframe, timeago)
  ATR = ta.volatility.average_true_range(high = df['High'],low = df['Low'], close = df['Close'],window = 10)
  EMA = ta.trend.ema_indicator(df['Close'], 20)
  keltnerhigh = EMA[-1] + (ATR[-1]*0.20)
  keltnerlow = EMA[-1] - (ATR[-1]*0.20)
  if df['Close'][-1] > keltnerlow and df['Close'][-1] > keltnerhigh:
    return True
  else:
    print('precos abaixo das bandas de keltner ,aguardando 60s')
    time.sleep(60)

def maxmin(ticker,timeframe,timeago):
    getmininicio = getmin(ticker,timeframe,timeago)
    qty_compra = round(79/getmin(ticker,timeframe,timeago),2)
   
    #estrategia
    #ordem de compra no donchianlow
    if keltner(ticker,timeframe,timeago):
      open_position = False
      if open_position == False:
        try:
          buy_limit = client.create_order(symbol= ticker, side='BUY', type='LIMIT', timeInForce='GTC', quantity=qty_compra , price= getmininicio)
        #buy_order = client.create_test_order(symbol='ATOMUSDT', side='BUY', type='LIMIT', quantity= qty_compra, price = final['dclband'][-1], timeInForce='GTC')
          print(buy_limit)

          # #ORdem que estava no stack  / order = client.order_limit_sell(symbol=pair,quantity=quantity,price=sellPrice)
          orderId = buy_limit["orderId"]
          print('Buy order placed at {}\n'.format(getmininicio))
          key = True
          while key:
              currentOrder = client.get_order(symbol= ticker ,orderId=orderId)
              getmin(ticker,timeframe,timeago)
              time.sleep(60)
              getmax(ticker,timeframe,timeago)
              time.sleep(10)
              #caso onde a ordem é preenchida
              if currentOrder['status']=='FILLED':
                  print("Bought: {} at {}".format(qty_compra,getmininicio))
                  time.sleep(20)
                  open_position = True 
                  #comprado

                  while open_position:
                    #coloca ordem na maxima

                    #stop no tempo
                    contador = 0 
                    print(contador)
                    if contador  >= 5:
                      print('stopado por tempo')
                      market_order = client.create_order(symbol= ticker,
                                      side='SELL',
                                      type='MARKET',
                                      quantity = qty_compra)
                      print(f'stopado por tempo {market_order}')
                  #colocando ordem de compra
                    maxinicio = getmax(ticker,timeframe,timeago)
                    time.sleep(10)
                    sell_limit = client.create_order(symbol= ticker, side='SELL', type='LIMIT', timeInForce='GTC', quantity=qty_compra , price= maxinicio)
                    print('Sell order placed at {}\n'.format(maxinicio))
                    orderIdComprado = sell_limit["orderId"]
                    ordem_setada = True
                    while ordem_setada:

                        #caso onde a ordem de venda é preenchida
                        currentOrderComprado = client.get_order(symbol= ticker,orderId=orderIdComprado)
                        if currentOrderComprado['status'] == 'FILLED':
                          print('Venda feita: {} em {}'.format(qty_compra,sell_limit['price']))
                          open_position = False
                          key = False
                          break

                        #caso onde a ordem de venda tem que se atualizar
                        if getmax(ticker,timeframe,timeago) < maxinicio:
                          time.sleep(20)
                          cancelvenda = client.cancel_order(symbol= ticker, orderId=sell_limit['orderId'])
                        
                          print(cancelvenda)
                          print(f'Ordem cancelada , preço de saida estava em {maxinicio} e maxima atualizou para {getmax(ticker,timeframe,timeago)}')
                          #caso nao funcione, tentar colocar nova ordem dentro desse if e manter o loop
                          contador +=1
                          open_position = True
                          ordem_setada = False
                        
              #caso onde o preço minimo atualiza
              if getmin(ticker,timeframe,timeago) > getmininicio:
                time.sleep(20)
                cancel = client.cancel_order(symbol='ATOMUSDT', orderId=buy_limit['orderId'])
                print(cancel)
                print(f'Ordem cancelada , preço de entrada estava em {getmininicio} e minima atualizou para {getmin(ticker,timeframe,timeago)}')
                open_position = False
                print(".")
                break
            


        except  BinanceAPIException as e:
              # error handling goes here
                print(e)
        except BinanceOrderException as e:
            # error handling goes here
                print(e)
