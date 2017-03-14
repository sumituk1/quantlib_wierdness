''' Pandas remote data access : http://pandas.pydata.org/pandas-docs/stable/remote_data.html
    - Yahoo! Finance
    - Google Finance
    - St.Louis FED (FRED)
    - Kenneth French’s data library
    - World Bank
    - Google Analytics
'''

# import sys
# import os
# sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/' + '..' + '/'))

# Import matplotlib
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.dates import date2num
import pylab
import pandas as pd
from pandas_datareader import data
import datetime
from matplotlib.dates import DateFormatter, WeekdayLocator, DayLocator, MONDAY
from matplotlib.finance import candlestick_ohlc
from common.constants import *

''' calculates a interpolated swaprate dataframe for missing tenors. Uses linear interop'''
def calc_interpolated_marketdata(tenor,swaprate_md):
    # first find the tenors closest to the input tenor
    swaprate_md_local = swaprate_md.copy()

    if tenor < swaprate_md_local.columns[0]:
        # set the first swaprate as the passed in tenor
        x = swaprate_md_local[swaprate_md_local.columns[0]].values
        swaprate_md_local.insert(0,tenor,x)
    elif tenor > swaprate_md_local.columns[-1]:
        # set the last swaprate as the passed in tenor
        x = swaprate_md_local[swaprate_md_local.columns[-1]].values
        index = swaprate_md_local.columns.get_loc(swaprate_md_local.columns[-1])
        swaprate_md_local.insert(index+1, tenor,x) # insert the new tenor at the end...
    else:
        # do a linear interpolation
        for lower, upper in zip(swaprate_md_local.columns[:-1], swaprate_md_local.columns[1:]):
            if lower <= tenor <= upper:
                break

        swaprate_md_local.insert(swaprate_md_local.columns.get_loc(upper),tenor,np.nan)
        swaprate_md_local = swaprate_md_local.interpolate(axis=1)

    return swaprate_md_local

''' Make sure all tenors in the passed in portfolio have got the corresponding swap marketdata
Interpolate/extrapolate wherever necessary...'''
def prepare_marketdata(md, port_df,__PORTFOLIO_TENOR_COLUMN_NUMBER):
    for index in port_df.index:
        # check if this is a multi-leg per package_id
        if type(port_df.loc[index]) == pd.Series:
            # Just one single leg
            count_legs = 1
        else:
            count_legs = len(port_df.loc[index].values)

        if count_legs == 1:
            leg_df = port_df.loc[index].values
            tenor = leg_df[__PORTFOLIO_TENOR_COLUMN_NUMBER]

            # get the market_data returns timeseries
            if tenor not in md.columns:
                md = calc_interpolated_marketdata(tenor, md)
        else:
            # for each individual leg, make sure the
            # marketdata containes all the swaprates
            for count in range(0, count_legs):
                leg_df = port_df.loc[index].values[count]
                tenor = leg_df[__PORTFOLIO_TENOR_COLUMN_NUMBER]
                # get the market_data returns timeseries
                if tenor not in md.columns:
                    md = calc_interpolated_marketdata(tenor, md)
    return md

''' Generates the time-series difference'''
# noinspection PyShadowingNames
def calc_ts_diff(md, __IS_MARKETDATA_PERCENT= False):
    md_diff_loc = pd.DataFrame(index=md.index, columns=md.columns)

    if __IS_MARKETDATA_PERCENT:
        for cols in md.columns:
            if "Spot" in cols:
                md_diff_loc[cols] = np.log(md[cols]) - np.log(md[cols].shift(-1))
            else:
                md_diff_loc[cols] = md[cols].diff(-1)
    else:
        # marketdata given in % so divide by 100
        for cols in md.columns:
            if "Spot" in cols:
                md_diff_loc[cols] = np.log(md[cols] / 100) - np.log(md[cols].shift(-1) / 100)
            else:
                md_diff_loc[cols] = md[cols].diff(-1) / 100
                # md_diff_loc = md.diff(-1) / 100

    train_cols = md_diff_loc.columns[0:]
    md_diff_loc = md_diff_loc.dropna(subset=train_cols)  # remove any NaN rows
    # md_diff_loc_2 = md_diff_loc[:-1] # remove the final row after differencing
    return md_diff_loc

''' Generates the time-series difference'''
# noinspection PyShadowingNames
def calc_ts_diff_pct(md, unique_dates, unique_rics):
    md_diff_out = pd.DataFrame(columns = unique_rics)

    for i in range(0,len(unique_rics)):
        train_cols = md[md.iloc[:, 0] == unique_rics[i]]
        md_diff_temp = train_cols.iloc[:, -1].pct_change()* 10000 # convert to pips
        md_diff_out[unique_rics[i]] = md_diff_temp.values

    # now convert the dataframe to dates on first column and factors on 1st row
    print("Test")
    return md_diff_out.dropna()

""" Loads TR FX data into a pandas dataframe
Returns :
    1) fx_data - containes dataes/rics and average bid/ask
    2) uniques_dates - gives all the uniques dates
    3) uniques rics - gives a list of unique rics
"""
def prepare_fx_marketdata(marketdata_df,
                          col_sym,
                          col_date,
                          col_price):
    # 1. drop any nans from avg bid/ask
    marketdata_df = (marketdata_df[~np.isnan(marketdata_df.iloc[:, col_price])]
                     .iloc[:, [col_sym, col_date, col_price]])
    # set the index as sym + date
    marketdata_df = (marketdata_df.set_index([marketdata_df.iloc[:, 0],
                                              marketdata_df.iloc[:, 1]]))
    # return a ist of unique dates
    unique_dates = marketdata_df.iloc[:, 1].unique()
    # return a ist of unique syms
    unique_rics = marketdata_df.iloc[:, 0].unique()
    return marketdata_df, unique_dates, unique_rics

'''------ Start of main test program  -----------'''
if __name__ == "__main__":
    tenor = 15
    _marketdataFileName = "PCA_test_interpolation.xlsx"
    _marketdataSheetName = "marketdata"
    pre = os.path.abspath(os.path.dirname(__file__) + '/' + '../..' + '/resources')
    md = pd.read_excel(os.path.join(pre, _marketdataFileName), header=0, sheetname=_marketdataSheetName,
                                  index_col=0, na_values=['NA'])
    if tenor not in md.columns:
        md = calc_interpolated_marketdata(tenor, md)

    md.plot()
    plt.show()