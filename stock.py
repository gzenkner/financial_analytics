import requests
import pandas as pd
import io
import numpy as np
import plotly.express as px
from alpha_vantage.timeseries import TimeSeries
import json
import csv
from datetime import datetime, timedelta, date
from sklearn.preprocessing import StandardScaler
import pandas as pd
import requests
from bs4 import BeautifulSoup
import seaborn as sns
import matplotlib.pyplot as plt


class Stocks:
    """Class for fetching stock data from Alpha Vantage API.

    Parameters:
        symbols (str or list): A single stock symbol or a list of stock symbols.
        function (str): The function type. It can be either 'TIME_SERIES_DAILY' or 'TIME_SERIES_INTRADAY'.
        api_key (str): Your Alpha Vantage API key
        (optional) start_date (str): The start date for the data query. Defaults to start of data.
        (optional) end_date (str): The end date for the data query. Defaults to last day stock market data was available.
        (optional) outputsize: The size of the time series to retrieve. Defaults to compact, which returns the last 100 data points. full returns the full history.

        TIME_SERIES_INTRADAY ONLY
        (optional) interval: The time-series data point interval. Defaults to 1 minute.
        (optional) Adjusted?: Whether the intraday endpoint should return adjusted data. Defaults to false.
        (optional) extended_hours: A string specifying the output size (optional).
        (optional) month: A string specifying the output size (optional).
        (optional) datatype: A string specifying the output size (optional).
    """
    def __init__(self, symbols, function='TIME_SERIES_DAILY', output_size='full', start_date=None, end_date=None, interval=None, api_key='yourkey'):
        """Initialize the Stocks class with the specified parameters."""
        self.symbols = symbols
        self.output_size = output_size
        self.start_date = start_date
        self.end_date = end_date
        self.api_key = api_key
        self.json_urls = []
        # TIME_SERIES_INTRADAY - required=[function, symbol, interval, apikey], optional=[adjusted, extended_hours, month, outputsize, datatype]
        # TIME_SERIES_DAILY - required=[function, symbol, apikey], optional=[outputsize, datatype]
      
        
        if function == 'TIME_SERIES_DAILY':
            self.time_series_daily(function)
        elif function == 'TIME_SERIES_INTRADAY':
            if interval is None:
                raise ValueError("Interval parameter is required for TIME_SERIES_INTRADAY.")
            self.time_series_intraday(function)

    def time_series_daily(self, function):
        self.function = function
        pass

    def time_series_intraday(self, function):
        self.function = function    
        pass


    def alpha_vantage_fetch_dataframe(self):
        if isinstance(self.symbols, str):
            self.symbols = [self.symbols]  # Convert single symbol to a list

        stock_dfs = []  # Collect stock dataframes for each symbol
        meta_dfs = []  # Collect meta dataframes for each symbol

        for symbol in self.symbols:
            json_url = f'https://www.alphavantage.co/query?function={self.function}&symbol={symbol}&outputsize={self.output_size}&apikey={self.api_key}&datatype=json'
            self.json_urls.append(json_url)
            response = requests.get(json_url)
            data = response.json()

            if 'Meta Data' not in data:
                print(f"No data available for symbol: {symbol}")
                continue

            metadata = data['Meta Data']
            stock_info = data['Time Series (Daily)']
            stock_df = pd.DataFrame.from_dict(stock_info, orient='index')
            stock_df.index = pd.to_datetime(stock_df.index)
            stock_df = stock_df.apply(pd.to_numeric)
            stock_df.sort_index(inplace=True)

            if self.start_date is not None:
                stock_df = stock_df.loc[self.start_date:]
            if self.end_date is not None:
                stock_df = stock_df.loc[:self.end_date]

            meta_df = pd.DataFrame(metadata, index=[0])

            stock_df['symbol'] = symbol  # Add symbol column to stock dataframe
            meta_df['symbol'] = symbol  # Add symbol column to meta dataframe

            stock_dfs.append(stock_df)
            meta_dfs.append(meta_df)

        stock_data = pd.concat(stock_dfs)
        meta_data = pd.concat(meta_dfs)

        return stock_data, meta_data

    def calculate_correlation(self, method='pearson'):
        df, _ = self.alpha_vantage_fetch_dataframe()
        selected_columns = df[['5. adjusted close', 'symbol']]

        pivot_df = pd.pivot_table(selected_columns, index=selected_columns.index, columns='symbol', values='5. adjusted close')
        correlation_matrix = pivot_df.corr()

        # Generate color-coded plot
        sns.set(style='white')
        cmap = sns.diverging_palette(220, 10, as_cmap=True)
        plt.figure(figsize=(10, 8))
        sns.heatmap(correlation_matrix, annot=True, cmap=cmap, center=0, linewidths=0.5)
        plt.title('Correlation Matrix')
        plt.show()

        return 



