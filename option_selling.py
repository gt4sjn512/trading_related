import pandas as pd
import pandas_datareader as pdr
import matplotlib.pyplot as plt
import numpy as np

tickers = open('./sp500_list').readlines()
tickers = [each.strip().replace('.', '') for each in tickers]
# tickers = ['BRK-B','BF-B']

start = '2001-01-01'
end = '2020-07-01'
if False:
    for each_ticker in tickers:
        try:
            pdr.get_data_yahoo(each_ticker, start=start, end=end).to_hdf('Sp500.h5', key=each_ticker, mode='a')
        except:
            print(each_ticker)
            pass

store = pd.HDFStore('Sp500.h5')


def generate_timeseries(ticker):
    res = store[ticker][['Adj Close']]
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

def option_selling_ev(premium, threshold, ticker):
    ''' The goal is to calculate returns of selling weekly options'''
    ts = generate_timeseries(ticker)
    ev_below, ev_above, p_below, p_above = get_er_and_es(threshold, ts)
    sell_call_ev = premium - max(ev_above - threshold, 0) * p_above

    ev_below, ev_above, p_below, p_above = get_er_and_es(-threshold, ts)
    sell_put_ev = premium - max(-ev_below - threshold, 0) * p_below

    '''  
    print("Option Selling EV: Annualized return is: ",round(ev*52*100,2),'%')
    print("Net Option premium income per year is: ",round(premium*52*100,2),'%')
    print("There is ",round(pr,2), " probability that return will be lower than threshold.")
    print("Expected shortfall is ",round(es*52*100,2),'%')
    '''
    return sell_call_ev, sell_put_ev


price = 202.8
strike = 212.5
option_premium = 2.37
threshold = strike / price - 1
premium = option_premium / price

sell_call_ev, sell_put_ev = option_selling_ev(premium=premium, threshold=threshold, ticker='MSFT')

print(sell_call_ev)
print(sell_put_ev)
