import requests
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


class Choppiness_Indicator():

    def __init__(self, market, start, end, tick_interval, lookback):
        self.market = market
        self.start = start
        self.end = end
        self.tick_interval = tick_interval
        self.lookback = lookback
        self.url = 'https://api.binance.com/api/v3/klines?symbol='+ market + '&interval='+ self.tick_interval
        #self.data = requests.get(self.url).json()
        self.trend = self.instantiate_trend()

    def get_data(self):
        try:
            data = requests.get(self.url).json()
        except:
            print(" <<<<<<<<<<<<<<<   ERROR READING THE DATA  >>>>>>>>>>>>>>>>")
        df = pd.DataFrame(data=data, columns=['Open Time', 'Open', 'High', 'Low', 'Close', 'Volume', 'datetime', 'Quote Asset Time', 'Number of Trades', 'Taker buy base asset volume', 'Taker buy quote asset volume', 'Ignore'])
        df['datetime'] = pd.to_datetime(df['datetime'], unit='ms')
        df = df.set_index('datetime').astype(float)
        data_df = df[['High', 'Low', 'Close']]
        data_df = data_df[(data_df.index > self.start) & (data_df.index < self.end)]
        #print(data_df)
        return data_df

    def get_ci(self, high, low, close, lookback):
        tr1 = pd.DataFrame(high - low).rename(columns = {0:'tr1'})
        tr2 = pd.DataFrame(abs(high - close.shift(1))).rename(columns = {0:'tr2'})
        tr3 = pd.DataFrame(abs(low - close.shift(1))).rename(columns = {0:'tr3'})
        frames = [tr1, tr2, tr3]
        tr = pd.concat(frames, axis = 1, join = 'inner').dropna().max(axis = 1)
        atr = tr.rolling(1).mean()
        highh = high.rolling(lookback).max()
        lowl = low.rolling(lookback).min()
        ci = 100 * np.log10((atr.rolling(lookback).sum()) / (highh - lowl)) / np.log10(lookback)
        return ci

    def instantiate_trend(self):
        
        print(f" \n<<<<<<<<<< Getting Data for: {self.market} >>>>>>>>>>>")
        market_data = self.get_data()
        print(f" <<<<<<<<<< Calculating the Chop Index for {self.market} between {self.start} --- {self.end} >>>>>>>>>>>")
        ci_data = self.get_ci(market_data['High'], market_data['Low'], market_data['Close'], self.lookback)
        ci_data = ci_data.dropna()
        #print(ci_data)
        print(f" <<<<<<<<<< Computing The Average Chop Index Values... >>>>>>>>>>>")
        ci_data = np.array(ci_data)
        ci_data_avg = ci_data.mean()
        print(f" <<<<<<<<<< The Average Chop Index Value is {ci_data_avg}. >>>>>>>>>>>")
        if ci_data_avg > 55:
            self.trend = "RANGING"
        elif ci_data_avg < 45:
            self.trend = "TRENDING"
        elif (ci_data_avg >= 45 and ci_data_avg <= 55):
            if abs(ci_data_avg - 55) <= abs(ci_data_avg):
                self.trend = "RANGING"
            else:
                self.trend = "TRENDING"
        else:
            print(f" <<<<<<<<<< Error Computing Trend for {self.market} >>>>>>>>>>>")
        
        return self.trend
    
    def compute_trend(self):
        
        print(f" \n<<<<<<<<<< Getting Data for: {self.market} >>>>>>>>>>>")
        market_data = self.get_data()
        print(f" <<<<<<<<<< Calculating the Chop Index for {self.market} between {self.start} --- {self.end} >>>>>>>>>>>")
        ci_data = self.get_ci(market_data['High'], market_data['Low'], market_data['Close'], self.lookback)
        ci_data = ci_data.dropna()
        #print(ci_data)
        print(f" <<<<<<<<<< Computing The Average Chop Index Values... >>>>>>>>>>>")
        ci_data = np.array(ci_data)
        ci_data_avg = ci_data.mean()
        print(f" <<<<<<<<<< The Average Chop Index Value is {ci_data_avg}. >>>>>>>>>>>")
        if self.trend == "RANGING" and ci_data_avg > 45:
            self.trend = "RANGING"
        elif self.trend == "RANGING" and ci_data_avg <= 45:
            self.trend = "TRENDING"
        elif self.trend == "TRENDING" and ci_data_avg < 55:
            self.trend = "TRENDING"
        elif self.trend == "TRENDING" and ci_data_avg >= 55:
            self.trend = "RANGING"
        else:
            print(f" <<<<<<<<<< Error Computing Trend for {self.market} >>>>>>>>>>>")
        
        return self.trend

    def visualize(self):
        
        ax1 = plt.subplot2grid((11,1,), (0,0), rowspan = 5, colspan = 1)
        ax2 = plt.subplot2grid((11,1,), (6,0), rowspan = 4, colspan = 1)
        data = self.get_data()
        data['ci'] = self.get_ci(data['High'], data['Low'], data['Close'], self.lookback)
        ax1.plot(data['Close'], linewidth = 2.5, color = '#2196f3')
        ax1.set_title('BTC CLOSING PRICES')  
        ax2.plot(data['ci'], linewidth = 2.5, color = '#fb8c00')
        ax2.axhline(38.2, linestyle = '--', linewidth = 1.5, color = 'grey')
        ax2.axhline(61.8, linestyle = '--', linewidth = 1.5, color = 'grey')
        ax2.set_title('BTC CHOPPINESS INDEX 14')
        plt.show()


