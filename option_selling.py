import pandas as pd
import pandas_datareader as pdr
import matplotlib.pyplot as plt
import numpy as np

start_date = '2001-01-01'
end_date = '2020-07-01'

''' Not a single exception handler. Just send it'''

if False:
    tickers = open('./sp500_list').readlines()
    tickers = [each.strip().replace('.', '') for each in tickers]
    # tickers = ['BRK-B','BF-B']
    for each_ticker in tickers:
        try:
            pdr.get_data_yahoo(each_ticker, start=start_date, end=end_date).to_hdf('Sp500.h5', key=each_ticker, mode='a')
        except:
            print(each_ticker)
            pass

def generate_timeseries(ticker,localdata=True):

    if localdata:
        store = pd.HDFStore('Sp500.h5')
        res = store[ticker][['Adj Close']]
        store.close()
    else:
        print('Downloading data from yahoo')
        res = pdr.get_data_yahoo(ticker, start=start_date, end=end_date)[['Adj Close']]

    res['ret'] = res['Adj Close'].pct_change()
    res['day'] = res.index
    res['day'] = res['day'].apply(lambda x: x.strftime("%A"))
    res['weekly_ret'] = res['ret'].rolling(5).sum()
    res = res[res['day'] == 'Friday']
    res = res.dropna()
    # res['weekly_ret'].hist(bins=100)
    ts = res['weekly_ret'].sort_values(ascending=False)
    #     print('Return Profile of ',ticker)
    #     print(ts.describe())
    #     print('-=-=-=-=-=-=-=-=-')
    return ts


def get_er_and_es(threshold, ts):
    '''given a threshold, return probability below and above that threshold,
       calculate expected return if actual return is lower than the threshold,
       calculate expected return if actual return is higher than the threshold'''
    threshold_id = 0
    for each in range(len(ts)):
        if threshold < ts[each]:
            threshold_id = each
    '''threshold id is 1 behind the currrent index'''
    # return threshold_id
    aboves = ts[0:threshold_id + 1]
    belows = ts[threshold_id + 1:]
    ev_below = belows.sum() / len(belows)
    p_below = len(belows) / len(ts)
    ev_above = aboves.sum() / len(aboves)
    p_above = len(aboves) / len(ts)
    return ev_below, ev_above, p_below, p_above


# get_er_and_es(0.1,ts)

def option_selling_ev(premium, threshold, ticker,report=False):
    ''' The goal is to calculate returns of selling weekly options'''
    ts = generate_timeseries(ticker,localdata=False)
    # for max loss of option selling
    hero_move = max(ts)
    zero_move = min(ts)

    ''' Call Option Selling'''
    ev_below, ev_above, p_below, p_above = get_er_and_es(threshold, ts)
    sell_call_ev = premium - max(ev_above - threshold, 0) * p_above
    wtf_call_v = premium - max(hero_move - threshold, 0)
    if report:
        print("Call Option Selling EV is: ",round(sell_call_ev*52*100,2),'%')
        print("Net Option premium income per year is: ",round(premium*52*100,2),'%')
        print("There is ",round(p_above*100.0,0), "% probability that return will be higher than call threshold.")
        print("Be careful, worst case is ", round(wtf_call_v*100.0, 0), '%')
    ''' Put Option Selling'''
    ev_below, ev_above, p_below, p_above = get_er_and_es(-threshold, ts)
    sell_put_ev = premium - max(-ev_below - threshold, 0) * p_below
    wtf_put_v = premium - max(-zero_move - threshold, 0)
    if report:
        print("Put Option Selling EV is: ",round(sell_put_ev*52*100,2),'%')
        print("Net Option premium income per year is: ",round(premium*52*100,2),'%')
        print("There is ",round(p_below*100.0,0), "% probability that return will be lower than put threshold.")
        print("Be careful, worst case is ", round(wtf_put_v*100.0, 0), '%')


    return sell_call_ev, sell_put_ev

''' quick calc'''

price = 202.8
strike = 212.5
option_premium = 2.37
threshold = strike / price - 1
premium = option_premium / price

sell_call_ev, sell_put_ev = option_selling_ev(premium=premium, threshold=threshold, ticker='MSFT',report=True)

