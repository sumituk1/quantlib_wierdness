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

''' Create a candlestick chart'''
def pandas_candlestick_ohlc(dat, stick="day", otherseries=None):
    """
    :param dat: pandas DataFrame object with datetime64 index, and float columns "Open", "High", "Low", and "Close",
    likely created via DataReader from "yahoo"
    :param stick: A string or number indicating the period of time covered by a single candlestick.
    Valid string inputs include "day", "week", "month", and "year", ("day" default), and any numeric input indicates
    the number of trading days included in a period
    :param otherseries: An iterable that will be coerced into a list, containing the columns of dat that hold other
    series to be plotted as lines

    This will show a Japanese candlestick plot for stock data stored in dat, also plotting other series if passed.
    """
    mondays = WeekdayLocator(MONDAY)        # major ticks on the mondays
    alldays = DayLocator()              # minor ticks on the days
    dayFormatter = DateFormatter('%d')      # e.g., 12

    # Create a new DataFrame which includes OHLC data for each period specified by stick input
    transdat = dat.loc[:,["Open", "High", "Low", "Close"]]
    if (type(stick) == str):
        if stick == "day":
            plotdat = transdat
            stick = 1 # Used for plotting
        elif stick in ["week", "month", "year"]:
            if stick == "week":
                transdat["week"] = pd.to_datetime(transdat.index).map(lambda x: x.isocalendar()[1]) # Identify weeks
            elif stick == "month":
                transdat["month"] = pd.to_datetime(transdat.index).map(lambda x: x.month) # Identify months
            transdat["year"] = pd.to_datetime(transdat.index).map(lambda x: x.isocalendar()[0]) # Identify years
            grouped = transdat.groupby(list(set(["year",stick]))) # Group by year and other appropriate variable
            plotdat = pd.DataFrame({"Open": [], "High": [], "Low": [], "Close": []}) # Create empty data frame containing what will be plotted
            for name, group in grouped:
                plotdat = plotdat.append(pd.DataFrame({"Open": group.iloc[0,0],
                                            "High": max(group.High),
                                            "Low": min(group.Low),
                                            "Close": group.iloc[-1,3]},
                                           index = [group.index[0]]))
            if stick == "week": stick = 5
            elif stick == "month": stick = 30
            elif stick == "year": stick = 365

    elif type(stick) == int and stick >= 1:
        transdat["stick"] = [np.floor(i / stick) for i in range(len(transdat.index))]
        grouped = transdat.groupby("stick")
        plotdat = pd.DataFrame({"Open": [], "High": [], "Low": [], "Close": []}) # Create empty data frame containing what will be plotted
        for name, group in grouped:
            plotdat = plotdat.append(pd.DataFrame({"Open": group.iloc[0,0],
                                        "High": max(group.High),
                                        "Low": min(group.Low),
                                        "Close": group.iloc[-1,3]},
                                       index = [group.index[0]]))

    else:
        raise ValueError('Valid inputs to argument "stick" include the strings '
                         '"day", "week", "month", "year", or a positive integer')


    # Set plot parameters, including the axis object ax used for plotting
    fig, ax = plt.subplots()
    fig.subplots_adjust(bottom=0.2)
    if plotdat.index[-1] - plotdat.index[0] < pd.Timedelta('730 days'):
        weekFormatter = DateFormatter('%b %d')  # e.g., Jan 12
        ax.xaxis.set_major_locator(mondays)
        ax.xaxis.set_minor_locator(alldays)
    else:
        weekFormatter = DateFormatter('%b %d, %Y')
    ax.xaxis.set_major_formatter(weekFormatter)

    ax.grid(True)

    # Create the candelstick chart
    candlestick_ohlc(ax, list(zip(list(date2num(plotdat.index.tolist())), plotdat["Open"].tolist(), plotdat["High"].tolist(),
                      plotdat["Low"].tolist(), plotdat["Close"].tolist())),
                      colorup = "black", colordown = "red", width = stick * .4)

    # Plot other series (such as moving averages) as lines
    if otherseries != None:
        if type(otherseries) != list:
            otherseries = [otherseries]
        dat.loc[:,otherseries].plot(ax = ax, lw = 1.3, grid = True)

    ax.xaxis_date()
    ax.autoscale_view()
    plt.setp(plt.gca().get_xticklabels(), rotation=45, horizontalalignment='right')
    plt.show()

def get_swaps_marketdata(start,
                         end=datetime.date.today(),
                         source="fred"):

    # start = datetime.datetime(2015,10,1)
    # end = datetime.date.today()
    # fix the terms od swap data
    terms = [1, 2, 3, 5, 7, 10, 30]  # FRED hasn't got 20y swap rates
    df = pd.DataFrame()
    for idx in range(0, len(terms)):
        tenor = terms[idx]
        col = "DSWP" + str(tenor)
        xx = data.DataReader(col, source, start, end)
        df[tenor] = xx[col]

    # reverse the timeseries from latest day going back in time
    df_sorted_date_desc = df.iloc[::-1]

    # df_sorted_date_desc.to_csv("C:\\Sumit\\temp\\marketdata.csv")
    # pandas_candlestick_ohlc(swap_data[5])

    # return the data as a dataframe...
    return df_sorted_date_desc

''' Get the swaps marketdata. Default = FRED'''
def get_bonds_marketdata(start,
                         end=datetime.date.today(),
                         source="fred",
                         bPlot = False):
    # Get the US CMT rates
    terms = [1, 2, 3, 5, 7, 10, 20, 30]
    df = pd.DataFrame()
    for idx in range(0, len(terms)):
        tenor = terms[idx]
        col = "DGS" + str(tenor)
        xx = data.DataReader(col, source, start, end)
        df[tenor] = xx[col]

    df_sorted_date_desc = df.iloc[::-1]
    return df_sorted_date_desc


''' Get the swaps marketdata. Default = FRED'''
def get_marketdata(start,
                   end=datetime.date.today(),
                   productType=ProductType.SWAPS,
                   source="fred",
                   bPlot = False):

    # start = datetime.datetime(2015,10,1)
    # end = datetime.date.today()
    if productType == ProductType.SWAPS:
        df = get_swaps_marketdata(start,end,source)
    elif productType == ProductType.BOND:
        # Get the US CMT rates
        df = get_bonds_marketdata(start, end,source)
    elif productType == ProductType.SWAPSPREADS:
        df_swaps = get_swaps_marketdata(start,end,source)
        df_bonds = get_bonds_marketdata(start, end, source)
        df = df_swaps-df_bonds

    # df_sorted_date_desc.to_csv("C:\\Sumit\\temp\\marketdata.csv")
    # pandas_candlestick_ohlc(swap_data[5])
    if bPlot:
        # plt.figure()
        df.plot.line()
        # for key,value in swap_data.items():
        #     plt.plot(value,label=str(key)+"y")
        #     plt.grid(True)

        plt.legend()
        plt.grid(True)
        plt.show()

    # return the data as a dataframe...
    return df



'''------ Start of main test program  -----------'''
if __name__ == "__main__":
    start = datetime.datetime(2015, 8, 1)
    # get_marketdata(start,productType=ProductType.SWAPSPREADS,bPlot=True)
    data, date_unique, rics_unique = get_fx_reuters_data()

    # plot data
    for i in range(0,10):
        plt.plot(data[data.iloc[:, 0] == rics_unique[i]].values[:, 2],label=rics_unique[i])

    plt.legend()
    plt.show()