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