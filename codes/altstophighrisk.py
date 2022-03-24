!pip install python-binance
!pip install talib-binary

import asyncio

from binance import Client

import pandas as pd
import time
from binance import BinanceSocketManager,AsyncClient
import numpy
from pandas.core import frame
import nest_asyncio
import talib as ta
import sys
from secret import secret1,secret2



nest_asyncio.apply()

def createframe(msg):
    df = pd.DataFrame([msg])
    df= df.loc[:,['s','E','p']]
    df.columns =['symbol', 'Time','Price']
    df.Price = df.Price.astype(float)
    df.Time = pd.to_datetime(df.Time, unit = 'ms')
    return df

client = Client(secret1,secret2)
bsm = BinanceSocketManager(client)

#x =pd.DataFrame(client.get_ticker())

#selecionar apenas tickers com USDT
# y= x[x.symbol.str.contains('USDT')]
# tirar os Tickers com UP e Downn
# z = y[~(y.symbol.str.contains('UP') | y.symbol.str.contains('Down'))]
# Pegar as maiores variaçoes nas ultimas 24hrs
# w = z.sort_values(by='priceChangePercent', ascending=False)
# Pegar a maior variação nas ultimas 24hrs
# g = z[z.priceChangePercent == z.priceChangePercent.max()]
# print(w)
# print(g)

def get_top_symbol():
    todos_pares = pd.DataFrame(client.get_ticker())
    todos_pares['priceChangePercent'] = todos_pares['priceChangePercent'].astype(float)
    relevantes = todos_pares[todos_pares.symbol.str.contains('USDT')]
    filtrados = relevantes[~((relevantes.symbol.str.contains('UP')) | (relevantes.symbol.str.contains('DOWN')))]
    top_symbol = filtrados[filtrados.priceChangePercent == filtrados.priceChangePercent.max()]
    top_symbol = top_symbol.symbol.values[0]
    return top_symbol

def get_minute_data(ticker, interval, lookback):
    dados = pd.DataFrame(client.get_historical_klines(ticker,interval,lookback+' min ago UTC'))
    dados = dados.iloc[:,:6]
    dados.columns = ['Time','Open','High','Low','Close','Volume']
    dados = dados.set_index('Time')
    dados.index = pd.to_datetime(dados.index, unit='ms')
    dados = dados.astype(float)
    return dados
def get_minute_data_ema(ticker, interval, lookback):
    dados = pd.DataFrame(client.get_historical_klines(ticker,interval,lookback+' min ago UTC'))
    dados = dados.iloc[:,:6]
    dados.columns = ['Time','Open','High','Low','Close','Volume']
    dados = dados.set_index('Time')
    dados.index = pd.to_datetime(dados.index, unit='ms')
    dados = dados.astype(float)
    return dados

def calculamedia(dados):
    ema = ta.EMA(dados['Close'], timeperiod=20)
    if ema[-1]>ema[-2] and ema[-1]>ema[-4]:
        retorno_media = 'up'
    else:
        retorno_media = 'down'
        
    return retorno_media

def remove_usdt(ticker):
    r = len(ticker)
    assetremoved = ticker[:r-4]
    return assetremoved

def strategy(buy_amt, SL =0.987 , Target = 1.02, open_position = False,):
    try:
        asset = get_top_symbol()
        print(asset)
        df = get_minute_data(asset, '1m','120')
        dfe= get_minute_data_ema(asset, '5m','120')
        asset_ema = calculamedia(dfe)
        print(asset_ema)
    except:
        time.sleep(61)
        asset= get_top_symbol()
        df = get_minute_data(asset, '1m','120')
    #socket = bsm.trade_socket(asset)
    qty = round(buy_amt/df.Close.iloc[-1])
    if ((df.Close.pct_change()+ 1).cumprod()).iloc[-1] > 1:
        print('preço sobe nos ultimos 2 min')
        if calculamedia(df) == 'up':
            print('media subindo')
        
        
            order = client.create_order(symbol=asset,
                                            side='BUY',
                                            type='MARKET',
                                            quantity = qty)
            print(order)
            print(f'Comprado em {asset}')
            buyprice = float(order['fills'][0]['price'])
            open_position = True

            while open_position:
                    #await socket.__aenter__()
                    #msg = await socket.recv()
                    #df = createframe(msg)
                try:
                    dfo = get_minute_data(asset, '1m','2')
                    # print(f'ultimo preço (Close) é:  '+ str(df.Price.values))
                     # print(f'Alvo atual é: '+ str(buyprice*Target))
                    # print(f'StopLoss atual é: '+str(buyprice * SL))
                except:
                    print('Alguma coisa deu errado,Script continua em 1 min')
                    time.sleep(61)
                dfo= get_minute_data(asset,'1m','2')
                print(f'ultimo preço (Close) é:  '+ str(dfo.Close[-1]))
                print(f'Alvo atual é: '+ str(buyprice*Target))
                print(f'StopLoss atual é: '+str(buyprice * SL))
                #if dfo.Close[-1] <= buyprice * SL or dfo.Close[-1] >= buyprice * Target:
                if dfo.Close[-1] <= buyprice * SL:
                    result = client.get_asset_balance(remove_usdt(asset))['free']
                    order = client.create_order(symbol=asset,
                                                    side='SELL',
                                                    type='MARKET',
                                                    quantity = float(result))

                    print(order)
                    print('Stopado')
                    asset_excluir = asset
                    break
                    time.sleep(120)

                if dfo.Close[-1] >= buyprice * Target:
                    result = client.get_asset_balance(remove_usdt(asset))['free']
                    order = client.create_order(symbol=asset,
                                                    side='SELL',
                                                    type='MARKET',
                                                    quantity = float(result))
                    print(order)
                    print('venda no alvo realizada')
                    break
            
        else:
            print('EMA nao estao apontada para cima,aguardando 1min')
            time.sleep(120)
    else:      
        print('Nao esta subindo recentemente,aguardando 60 segundos')
        time.sleep(60)
        
while True:
    strategy(50)
#%%
# async def main():
#     client = await AsyncClient.create()
#     bm = BinanceSocketManager(client)

#     ts = bm.trade_socket('BTCUSDT')

#     async with ts as tscm:
#         while True:
#             res = await tscm.recv()
#             if res:
#                 print(createframe(res))

#     await client.close_connection()

# if __name__ == "__main__":

#     loop = asyncio.get_event_loop()
#     loop.run_until_complete(main())

"""# Nova seção"""
