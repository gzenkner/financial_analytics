import pandas as pd # 0.23.0
import requests     # 2.19.1
import io
import numpy as np
import plotly.express as px
from alpha_vantage.timeseries import TimeSeries
import json
import csv
from datetime import datetime, timedelta
import plotly.graph_objects as go
from bs4 import BeautifulSoup


def get_mortgage_rate(start_date='2000-01-01', end_date='2018-10-01'):
    payload = {
        'Datefrom'   : pd.to_datetime(start_date).strftime('%d/%b/%Y'),
        'Dateto'     : pd.to_datetime(end_date).strftime('%d/%b/%Y'),
        'SeriesCodes': 'IUMBV34,IUMBV37,IUMBV42,IUMBV45',
        'CSVF'       : 'TN',
        'UsingCodes' : 'Y',
        'VPD'        : 'Y',
        'VFD'        : 'N'
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) '
                    'AppleWebKit/537.36 (KHTML, like Gecko) '
                    'Chrome/54.0.2840.90 '
                    'Safari/537.36'
    }

    url_endpoint = 'http://www.bankofengland.co.uk/boeapps/iadb/fromshowcolumns.asp?csv.x=yes'

    response = requests.get(url_endpoint, params=payload, headers=headers)
    # Check if the response was successful, it should return '200'
    print(response.status_code)

    df = pd.read_csv(io.BytesIO(response.content))

    return df



def date_today():
    """
    Returns today's date in ISO-8601 "%Y-%m-%d"
    """
    today = datetime.today()
    return today.strftime("%Y-%m-%d")



def get_sp500_info():
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find the table containing the companies and sectors
    table = soup.find('table', {'class': 'wikitable sortable'})

    # Initialize empty dictionary for storing data
    data = {}

    # Extract data from the table rows
    headers = []
    for header in table.find_all('th'):
        headers.append(header.text.strip())
        
    for row in table.find_all('tr')[1:]:
        cols = row.find_all('td')
        if len(cols) >= len(headers):  # Ensure the row has enough columns
            for i, header in enumerate(headers):
                if header not in data:
                    data[header] = []
                data[header].append(cols[i].text.strip())
    
    df = pd.DataFrame(data)
    sector_counts = df['GICS Sector'].value_counts()
    data = go.Pie(labels=sector_counts.index, values=sector_counts.values)
    layout = go.Layout(title='Distribution of Sectors')
    fig = go.Figure(data=[data], layout=layout)
    return fig, df


def get_cpih_csv(ffill_period='default', start_date=None, end_date=None, dtype='pandas'):
    df = pd.read_csv('cpih.csv')
    df['date'] = pd.to_datetime(df['date'], format='%Y %b')  # Specify the date format explicitly
    df.set_index('date', inplace=True)

    if start_date is not None and end_date is not None:
        df = df.loc[start_date:end_date]

    if ffill_period == 'monthly':
        df = df.resample('M').ffill()
    elif ffill_period == 'quarterly':
        df = df.resample('Q').ffill()
    elif ffill_period == 'yearly':
        df = df.resample('Y').ffill()
    elif ffill_period != 'default':
        raise ValueError("Invalid ffill_period. Allowed values are 'monthly', 'quarterly', 'yearly', and 'default'.")

    df = df.reset_index()  # Reset the index to move the date to a separate column

    if dtype == 'numpy':
        return df.to_numpy()
    elif dtype == 'pandas':
        return df
    else:
        raise ValueError("Invalid dtype. Allowed values are 'pandas' and 'numpy'.")
    


def get_boe_interest_rate_csv(ffill_period='default', start_date=None, end_date=None, dtype='pandas'):
    df = pd.read_csv('BoE_interest_rates.csv')
    df['date'] = pd.to_datetime(df['Date Changed'], format='%d %b %y')  # Specify the date format explicitly
    df.set_index('date', inplace=True)
    df = df.drop('Date Changed', axis=1)

    df = df.sort_index()  # Sort the DataFrame by the date index

    if start_date is not None and end_date is not None:
        df = df.loc[start_date:end_date]

    if ffill_period == 'weekly':
        df = df.resample('W').ffill()
    elif ffill_period == 'monthly':
        df = df.resample('M').ffill()
    elif ffill_period == 'quarterly':
        df = df.resample('Q').ffill()
    elif ffill_period == 'yearly':
        df = df.resample('Y').ffill()
    elif ffill_period != 'default':
        raise ValueError("Invalid ffill_period. Allowed values are 'weekly', 'monthly', 'quarterly', 'yearly', and 'default'.")

    # Add missing yearly timestamps and rates
    idx = pd.date_range(start=start_date, end=end_date, freq='Y')
    existing_years = df.index.year
    missing_years = set(idx.year) - set(existing_years)
    missing_data = pd.DataFrame({'date': pd.to_datetime(list(missing_years), format='%Y'), 'Rate': 0.5})
    missing_data.set_index('date', inplace=True)
    df = pd.concat([df, missing_data])
    df = df.sort_index()

    df = df.reset_index()

    if dtype == 'numpy':
        return df.to_numpy()
    elif dtype == 'pandas':
        return df
    else:
        raise ValueError("Invalid dtype. Allowed values are 'pandas' and 'numpy'.")
    

def plot_investments(json_file, dir='data/'):
    json_file = f"{dir}{json_file}"

    with open(str(json_file)) as file:
        data = json.load(file)

    symbols = []
    dates = []
    amounts = []
    shares = []

    for symbol, investment in data.items():
        for date, data in investment['buy']['date'].items():
            symbols.append(symbol)
            dates.append(date)
            amounts.append(data['amount'])
            shares.append(data['shares'])

    # Creating the grouped bar chart traces
    data = []
    unique_symbols = set(symbols)

    for symbol in unique_symbols:
        symbol_dates = [date for symbol_, date in zip(symbols, dates) if symbol_ == symbol]
        symbol_amounts = [amount for symbol_, amount in zip(symbols, amounts) if symbol_ == symbol]
        trace = go.Bar(
            x=symbol_dates,
            y=symbol_amounts,
            name=symbol
        )
        data.append(trace)

    # Creating the grouped bar chart layout
    layout = go.Layout(
        barmode='group',
        title='Investment Amount by Symbol',
        xaxis=dict(title='Date'),
        yaxis=dict(title='Amount'),
        width=600, height=400
    )

    # Creating the figure
    fig = go.Figure(data=data, layout=layout)

    # Displaying the chart
    return fig.show()