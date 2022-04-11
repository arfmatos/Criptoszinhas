
from binance import Client
import pandas as pd
import time
from binance import BinanceSocketManager,AsyncClient
import nest_asyncio
import talib as ta
from secret import secret1,secret2

#HIGH RISK ,USE BY YOUR OWN RISK ,MADE ONLY FOR STUDY REASONS
client = Client(secret1,secret2)
bsm = BinanceSocketManager(client)


#get the highest up% coin symbol
def get_top_symbol():
    todos_pares = pd.DataFrame(client.get_ticker())
    todos_pares['priceChangePercent'] = todos_pares['priceChangePercent'].astype(float)
    relevantes = todos_pares[todos_pares.symbol.str.contains('USDT')]
    filtrados = relevantes[~((relevantes.symbol.str.contains('UP')) | (relevantes.symbol.str.contains('DOWN')))]
    top_symbol = filtrados[filtrados.priceChangePercent == filtrados.priceChangePercent.max()]
    top_symbol = top_symbol.symbol.values[0]
    return top_symbol
#get the data from binance [Time,Open,High,Low,Close,Volume]
def get_minute_data(ticker, interval, lookback):
    dados = pd.DataFrame(client.get_historical_klines(ticker,interval,lookback+' min ago UTC'))
    dados = dados.iloc[:,:6]
    dados.columns = ['Time','Open','High','Low','Close','Volume']
    dados = dados.set_index('Time')
    dados.index = pd.to_datetime(dados.index, unit='ms')
    dados = dados.astype(float)
    return dados
   
#check if the moving averages i
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
        dfe= get_minute_data(asset, '5m','120')
        asset_ema = calculamedia(dfe)
        print(asset_ema)
    except:
        time.sleep(61)
        asset= get_top_symbol()
        df = get_minute_data(asset, '1m','120')

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
                try:
                    dfo = get_minute_data(asset, '1m','2')
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
                    
                    open_position = False
                    time.sleep(120)

                if dfo.Close[-1] >= buyprice * Target:
                    result = client.get_asset_balance(remove_usdt(asset))['free']
                    order = client.create_order(symbol=asset,
                                                    side='SELL',
                                                    type='MARKET',
                                                    quantity = float(result))
                    print(order)
                    print('venda no alvo realizada')
                    open_position = False
            
        else:
            print('EMA nao estao apontada para cima,aguardando 1min')
            time.sleep(120)
    else:      
        print('Nao esta subindo recentemente,aguardando 60 segundos')
        time.sleep(60)
        
while True:
    strategy(50)


