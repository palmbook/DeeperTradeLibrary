name = 'DeeperTradeLibrary'

import numpy as np
import pandas as pd

import ta
import pandas_ta

class Indicators:
    @staticmethod
    def addAllTechnicalIndicators(df):
        
        df = df.copy()
        
        assert all([a == b for a, b in zip(df.columns, ['open', 'high', 'low', 'close', 'volume'])]), "Columns must be open, high, low, close, volume"
        
        df = ta.add_all_ta_features(df, open="open", high="high", low="low", close="close", volume="volume")
        
        df['ao'] = pandas_ta.ao(df['high'], df['low'], fast=5, slow=34)
        df['apo'] = pandas_ta.apo(df['close'], fast=12, slow=26)
        df['bop'] = pandas_ta.bop(df['open'], df['high'], df['low'], df['close'])
        df['cg'] = pandas_ta.cg(df['close'], length=10)
        df['fwma'] = pandas_ta.fwma(df['close'], length=10)
        df['kurtosis'] = pandas_ta.kurtosis(df['close'], length=30)
        
        return df
        
class Backtest:
    @staticmethod
    def trade_simulation(df,digit=1,pip_profit=1,commission=0):
    
        assert 'signal' in df.columns, 'Signal column is required.'

        df['value_grp'] = (df.signal != df.signal.shift(1)).astype('int').cumsum()
        df['open_time'] = df.time
        df['close_time'] =  df.time.shift(-1)
        df['open_price'] = df.close
        df['close_price'] = df.close.shift(-1)
        #Remove last signal.
        df = df[df['value_grp']!=df.iloc[-1].value_grp]
        
        #Create trading result
        df_trade = pd.DataFrame({
            'type' : df.groupby('value_grp').signal.first(),
            'open_time':df.groupby('value_grp').open_time.first(),
            'open_price' : df.groupby('value_grp').close.first(),
            'close_time' : df.groupby('value_grp').close_time.last(),
            'close_price' : df.groupby('value_grp').close_price.last(),
            'length' : df.groupby('value_grp').size(),
        })
        df_trade['pnl'] = (df_trade.close_price-df_trade.open_price)*df_trade.type*10**digit*pip_profit-commission
        df_trade = df_trade[df_trade.type!=0]
        df_trade['equity'] = df_trade.pnl.cumsum()
        
        df_trade.reset_index(drop=True, inplace=True)
        
        return df_trade
        