import pandas as pd
import datetime as dt
from calendar import monthrange

def exclude_month_ends(data_df,date_rng):
    month_end = return_month_ends(date_rng=date_rng)
    return data_df[~data_df["TradeDate"].isin(month_end)]

def return_month_ends(date_rng):
    end_of_month_day = [x[1] for x in
                        [monthrange(yr, month) for month, yr in zip(list(date_rng.month), list(date_rng.year))]]

    month_end = set([dt.datetime(year, month, day) for day, month, year in
                     zip(end_of_month_day, date_rng.month, date_rng.year)])
    return month_end

def return_lastday_of_prev_month(dt):
    return monthrange(dt.year, dt.month - 1)
