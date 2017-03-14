# import sys
# import os
# sys.path.append(os.path.join(os.path.dirname(__file__) , '..'))
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),"../../common")))
import pandas as pd
import numpy as np
from common.constants import *
import collections

''' Given a portfolio, this function groups the DV01 risk by Tenor.
It then aggregates the Risk across each tenor bucket and returns a sorted list'''
def aggregate_port_risk(portfolio_df):
    grouped_tenor_data = portfolio_df.groupby("Tenor")
    tenor_DV01 = dict()
    for name,group in grouped_tenor_data:
        tenor_DV01[name] = calc_tenor_dv01(group)
        # if name not in tenor_DV01.keys():
        #     tenor_DV01[name] = calc_tenor_DV01(group)

    return collections.OrderedDict(sorted(tenor_DV01.items()))

'''Given a list of standard tenors, this function fills up gaps in the portfolio
risk bucket by putting in 0 to missing buckets'''
def fill_zero_dv01(standard_tenors, portfolio):
    for i in range(0,len(standard_tenors)):
        if standard_tenors[i] not in portfolio.keys():
            portfolio[standard_tenors[i]] = 0.0

''' Sums up the DV01 across a passed in tenor bucket.
NOTE: only 0ne tenor bucket should be passed in like the 5yr'''
def calc_tenor_dv01(df):
    sum_DV01 = 0
    for i in range(0, len(df)):
        sum_DV01 += get_dv01_adj_sign(df["DV01"].values[i], df["Side"].values[i])
        # refactored code.....
        # if df["Side"].values[i] == "Ask":
        #     sum_DV01 += +1 * df["DV01"].values[i]
        # else:
        #     sum_DV01 += -1 * df["DV01"].values[i]

    return sum_DV01

def get_dv01_adj_sign(DV01,Side):
    if Side == TradeSide.Ask:
        return +1 * DV01
    else:
        return -1 * DV01