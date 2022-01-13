# Stock Trading Bot Advisor

# initialize lock file to prevent infinite amount of script instances
import os
import sys

lockfile = '/home/abc/scripts/script.lock'
if not os.path.exists(lockfile):
    with open(lockfile, 'w'): pass
else:
    print('lockfile has been created')
    sys.exit(1)

import pandas as pd
import pandas_datareader.data as web
import numpy as np
import matplotlib.pyplot as plt
import datetime
import time
import smtplib
from email.mime.text import MIMEText

#initialize Yahoo API
import yfinance as yahoo_finance


tickers = ['TSLA','AAPL', 'NIO', 'BABA', 'GOOG', 'NVDA', 'AMZN', 'FB', 'F', 'M']


start_time = datetime.datetime(2021, 2, 1)

#todays date
end_time = datetime.datetime.now().date().isoformat()    

username = 'abc@gmail.com'
password = ''


def get_data(ticker):
    attempts = 0
    connected = False
    while not connected:
        try:
            ticker_df = web.get_data_yahoo(ticker, start=start_time, end=end_time)
            connected = True
            print('Connection has been established')
        except Exception as e:
            print("type error: " + str(e))
            time.sleep(3)
            attempts += 1
            if attempts >= 10:
                connected = True
            pass

    # use numerical integer index will be initialized
    
    print(ticker_df.head(3))

    return ticker_df

# compute RSI values
def computeRSI (data, time_window):
    diff = data.diff(1).dropna()    

    #this preservers dimensions off diff values
    up_change = 0 * diff
    down_change = 0 * diff

    # up change is equal to the +ve difference while down change is equal to -ve difference, if not it is equal to zero
    up_chang[diff > 0] = diff[ diff>0 ]
    down_chg[diff < 0] = diff[ diff < 0 ]

    up_change_average   = up_change.ewm(com=time_window-1 , min_periods=time_window).mean()
    down_change_average = down_change.ewm(com=time_window-1 , min_periods=time_window).mean()

    rs = abs(up_change_average/down_change_average)
    rsi = (100 - 100)/(1+rs)
    return rsi

#moving average will be simplified

def computeSMA(data, window):
    sma = data.rolling(window=window).mean()
    return sma

def computeEMA(data, span):
    ema = data.ewm(span=span, adjust=False).mean()
    return ema


def construct_df(ticker):
    # collect data from Yahoo API
    df = get_data(ticker)
    # compute the moving averages 
    for i in range(50, 250, 50):
        #print(i)
        df['SMA_{}'.format(i)] = computeSMA(df['Adj Close'], i)
    for i in range(50, 250, 50):
        #print(i)
        df['EMA_{}'.format(i)] = computeEMA(df['Adj Close'], i)

    return df


def stochastic(data, k_window, d_window, window):
    # input to function is one column from df
    # containing closing price or whatever value we want to extract K and D from

    min_val  = data.rolling(window=window, center=False).min()
    max_val = data.rolling(window=window, center=False).max()

    stch = ((data-min_val)/(max_val-min_val)) * 100

    K = stch.rolling(window=k_window, center=False).mean()
    
    D = K.rolling(window=d_window, center=False).mean()

    return K, D

def resample(df):
    agg_dict = {'Open': 'first',
                'High': 'max',
                'Low': 'min',
                'Close': 'last',
                'Adj Close': 'last',
                'Volume': 'mean'}

    # 'WA' - weekly aggregation
    df_res = df.resample('WA').agg(agg_dict)

    return df_res




def send_email(data_rsi, data_200_ema, data_50_ema, data_200_ema_vicinity, data_weekly_stochRSI, username, password):

    smtp_ssl_host = 'smtp.gmail.com'
    smtp_ssl_port = 465
    sender = 'abc@gmail.com'
    receiver = 'def@yahoo.com'

    msg_body_rsi = ("RSI reading of 30 \n"
                "Good entry potential\n"
                "ticker/s: \n"
                 + data_rsi + "\n\n")

    msg_body_200_ema = ("It is above 200 EMA \n"
                "Good entry potential \n"
                "ticker/s: \n"
                 + data_200_ema + "\n\n")

    msg_body_50_ema = ("It is near 50 EMA \n"
                "Big movement potential \n"
                "ticker/s: \n"
                 + data_50_ema + "\n\n")

    msg_body_200_ema_vicinity = ("It is near 200 EMA \n"
                "Strong reversal potential) \n"
                "ticker/s: \n"
                 + data_200_ema_vicinity + "\n\n")

    msg__body_weekly_stochRSI = ("weekly_stchRSI entry \n"
                "alert \n"
                "ticker/s: \n"
                 + data_weekly_stochRSI + "\n\n")


    msg_body = msg_body_rsi + msg_body_200_ema + msg_body_50_ema    \
               + msg_body_200_ema_vicinity + msg__body_weekly_stochRSI


    message = MIMEText(msg_body, "bold")
    # treat message as dictionary
    message['subject'] = 'Stock Signal'
    message['from']    = sender
    message['to']      = receiver


    # dummy email will send the mail
    try:
        server = smtplib.SMTP_SSL(smtp_ssl_host, smtp_ssl_port)
        server.login(username, password)
        server.sendmail(sender, receiver, message.as_string())
        server.quit()
        print("Email has been sent")
    except:
        print("Error: unable to send email")

def support_forming(df, n=14):
    # conclude that EMA might be forming support soon
    cnt = 0
    for i in range(0, n):
        if df['Adj Close'].iloc[-i] >= df['EMA_200'].iloc[-i]:
            cnt += 1

    # skip if falls below support
    if cnt/n >= 0.7 and (df['Adj Close'].iloc[-1] >= df['EMA_200'].iloc[-1]):
        return True
    else:
        return False


def conditions(df, df_res):
    ## long signal displayed as RSI the day before is below the threshold while today RSI is above - long signal

    if (df['RSI'].iloc[-1] <= 30):
        signal['RSI'].append(ticker)

    # long signal displayed as falling below 200 EMA yesterday while above 200 EMA today
    if (
        (df['EMA_200'].iloc[-5] > df['Adj Close'].iloc[-5]) and
        (df['EMA_200'].iloc[-1] < df['Adj Close'].iloc[-1])
       ):
        signal['EMA_200'].append(ticker)

    # potential long signal displayed as near 50 EMA
    
    if (
        ((df['EMA_50'].iloc[-1] / df['Adj Close'].iloc[-1]) >= 0.98) and
        ((df['EMA_50'].iloc[-1] / df['Adj Close'].iloc[-1]) <= 1.02)
       ):
        signal['EMA_50'].append(ticker)

    # potential long signal as near 200 EMA
    if (
        ((df['EMA_200'].iloc[-1] / df['Adj Close'].iloc[-1]) >= 0.98) and
        ((df['EMA_200'].iloc[-1] / df['Adj Close'].iloc[-1]) <= 1.02) and
        support_forming(df, 14)
       ):
        signal['EMA_200_vicinity'].append(ticker)

    # weekly stochastic RSI oversold signal
    thresh = 20
    
    if (
        df_res['K'].iloc[-1] <= thresh and
        df_res['D'].iloc[-1] <= thresh and
        ((df_res['K'].iloc[-1] / df_res['D'].iloc[-1]) >= 0.80) and
        ((df_res['K'].iloc[-1] / df_res['D'].iloc[-1]) <= 1.20)
       ):
        signal['weekly_stochRSI'].append(ticker)
    elif ( (df_res['K'].iloc[-1] == 0 ) or ( df_res['D'].iloc[-1] == 0 ) ):
        signal['weekly_stochRSI'].append(ticker)

    return None


signal = {}
signal['RSI'] = []
signal['EMA_200'] = []
signal['EMA_50'] = []
signal['EMA_200_vicinity'] = []
signal['weekly_stchRSI'] = []

for ticker in tickers:
    try:
        # df = get_data(ticker)       #just gets data
        df = construct_df(ticker)     #gets data and adds MAs to the df (implement RSI later)
        #adds RSI column to dataframe
        df['RSI'] = computeRSI(df['Adj Close'], 14)
        # RSI <= 30 is long signal
        # if last day RSI data (today) is oversold, send mail
        print('ticker:', ticker)
        print('rsi today', df['RSI'].iloc[-1])

        df_res = resample(df)
        df_res['RSI'] = computeRSI(df_res['Adj Close'], 14)
        df_res['K'], df_res['D'] = stochastic(df_res['RSI'], 3, 3, 14)

        conditions(df, df_res)


    except Exception as e:
        print("type error: " + str(e))



# if one of the value of the list is non empty list
if sum( 1 for i in signal.values() if len(i) > 0 ) > 0:
    rsi_str     = ' '.join(map(str, signal['RSI']))
    ema_200_str = ' '.join(map(str, signal['EMA_200']))
    ema_50_str  = ' '.join(map(str, signal['EMA_50']))
    ema_200_vicinity_str = ' '.join(map(str, signal['EMA_200_vicinity']))
    weekly_stchRSI_str = ' '.join(map(str, signal['weekly_stchRSI']))

    send_email(rsi_str, ema_200_str, ema_50_str, ema_200_vicinity_str, weekly_stchRSI_str, username, password)


# it will clean the lockfile
os.remove(lockfile)
