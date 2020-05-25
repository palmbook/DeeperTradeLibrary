name = 'DeeperTradeLibrary'

import numpy as np
import pandas as pd

import ta
import pandas_ta
import requests

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

class API:
    @staticmethod
    def get_instrument_data(token, country, instrument, timeframe='D1', length=100, From=None, To=None, IncludeFirst=True):
        url = 'https://api.deepertrade.co/instruments/%s/%s/data' % (country, instrument)
        header = { 'Authorization':'Bearer ' + token }
        payload = {
            "Timeframe": timeframe,
            "Length" : length,
            "IncludeFirst": IncludeFirst
        }
        if From is not None: payload['From'] = From
        if To is not None: payload['To'] = To
        r = requests.get(url, headers=header, params=payload)
        if r.status_code == 200:
            df = pd.DataFrame(r.json()['Data'])
            df.columns = map(str.lower, df.columns)
            return df
        else :
            print(r.json())
            return None
class Tools:

    @staticmethod
    def line_notify(token, message=''):
        url = 'https://notify-api.line.me/api/notify'
        headers = {'content-type':'application/x-www-form-urlencoded','Authorization':'Bearer ' + token}
        requests.post(url, headers = headers, data = {'message': message})
    
    @staticmethod
    def timeframe_resampler_candle(self, dt):
        if len(dt)!=0:
            if dt.name=='open': return dt.values[0]
            elif dt.name=='high': return dt.max()
            elif dt.name=='low': return dt.min()
            elif dt.name=='close': return dt.values[-1]
            elif dt.name=='volume': return dt.sum()
        else:
            return np.nan

    @staticmethod
    def timeframe_resampler(df, timeframe='1D'):
        #Columns Check
        assert 'time' in df.columns, '\'time\' column is required.'
        assert 'open' in df.columns, '\'open\' column is required.'
        assert 'high' in df.columns, '\'high\' column is required.'
        assert 'low' in df.columns, '\'low\' column is required.'
        assert 'close' in df.columns, '\'close\' column is required.'
        #Processing
        dfp = df.copy()
        dfp['time'] = pd.to_datetime(dfp.time)
        dfp.set_index('time', inplace=True)
        dfr = dfp.resample(timeframe).apply(self.timeframe_resampler_candle).dropna()
        dfr['time'] = dfr.index
        dfr = dfr[df.columns]
        dfr.reset_index(drop=True, inplace=True)

        return dfr
        
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
    
    @staticmethod
    def stock_trade_simulation(df, shares=1, commission=0.5, vat=7.0):

        assert 'time' in df.columns, '\'time\' column is required.'
        assert 'open' in df.columns, '\'open\' column is required.'
        assert 'high' in df.columns, '\'high\' column is required.'
        assert 'low' in df.columns, '\'low\' column is required.'
        assert 'close' in df.columns, '\'close\' column is required.'
        assert 'signal' in df.columns, '\'signal\' column is required.'

        df = df.copy()
        
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
        df_trade['shares'] = shares
        df_trade['profit'] = (df_trade.close_price - df_trade.open_price) * shares
        df_trade['commission'] = round((df_trade.open_price * shares * (commission / 100)) * (vat / 100), 2)
        df_trade['pnl'] = df_trade.profit - df_trade.commission
        df_trade = df_trade[df_trade.type==1]
        df_trade['equity'] = df_trade.pnl.cumsum()

        df_trade.reset_index(drop=True, inplace=True)

        return df_trade
        