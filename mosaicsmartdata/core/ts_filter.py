import pandas as pd
import numpy as np
#import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib import dates
# import logging


class OneSidedCusum:
    def __init__(self, cutoff, thresh = None):
        self.cutoff = cutoff
        self.thresh = thresh
        if self.thresh is None:
            self.thresh = 3 * self.cutoff
        self.S = 0

    def __call__(self, x):
        self.S = max(0, self.S + x - self.cutoff)
        if self.S > self.thresh:
            self.S = 0
            return True
        else:
            return False


class TwoSidedCusum:
    def __init__(self, cutoff, thresh):
        self.pos = OneSidedCusum(cutoff, thresh)
        self.neg = OneSidedCusum(cutoff, thresh)

    def __call__(self, x):
        pos = self.pos(x)
        neg = self.neg(-x)
        return pos or neg


class EMA:
    def __init__(self, alpha):
        self.alpha = alpha
        self.value = None

    def __call__(self, x):
        if self.value is None:
            self.value = x
        else:
            self.value = self.alpha * x + (1 - self.alpha) * self.value
        return self.value


class AdaptiveEMA:
    def __init__(self, slow_alpha, fast_alpha, cutoff, thresh):
        self.fast_ema = EMA(fast_alpha)
        self.slow_ema = EMA(slow_alpha)
        self.cusum = TwoSidedCusum(cutoff, thresh)

    def __call__(self, x):
        slow_sm = self.slow_ema(x)
        fast_sm = self.fast_ema(x)
        jump = self.cusum(x-slow_sm)
        if jump:
            self.slow_ema.value = self.fast_ema.value

def load_data():
    data = pd.read_excel("C:\\Sumit\\Mosaic\\Quant\\Quant Container\\Filter\\old_30yr_UST.xlsx",
                         sheetname="GovtBond",
                         header=0,
                         skiprows=1,
                         parse_cols="C:F").dropna(how='all').reset_index()
    data["Timestamp"] = pd.to_datetime(data["Timestamp"], format="%Y%m%d:%H:%M:%S")

    data.sort_values(by="Timestamp", inplace=True)
    return data


# mad = lambda x: np.fabs(x - x.mean()).mean()

def mean_abs_dev(price_series, ewm_series):
    if len(price_series) == 0 or len(ewm_series) == 0:
        return 0
    x = price_series - ewm_series
    return np.fabs(x - x.mean()).mean()


def sma(data, window):
    """
    Calculates Simple Moving Average
    http://fxtrade.oanda.com/learn/forex-indicators/simple-moving-average
    """
    if len(data) < window:
        return None
    return sum(data[-window:]) / float(window)


def detect_cumsum(slow_ema,
                  curr_value,
                  fast_ema,
                  i,
                  cut_off,
                  S_i=None,
                  amplitude_threshold=None):
    """
        runs a statistical quality control test by looking at the passed in slow_ewm and the cut-off
        (See: https://en.wikipedia.org/wiki/CUSUM)
        i is the index
        cut_off
        S_i is the CUSUM control structure.
        """
    if amplitude_threshold is None:
        amplitude_threshold = 2 * cut_off

    if i == 0:
        S_i = 0
    else:
        x_i = (curr_value - slow_ema)
        if x_i > 0:
            S_i = max(0, S_i + x_i - cut_off)
        else:
            S_i = max(0, S_i - x_i - cut_off)

    if S_i > amplitude_threshold:
        # The value of S is significant. Set the slow_ewm to fast_ewm
        slow_ema = fast_ema

    return slow_ema, S_i


def ema(data, alpha=0.03):
    """
        returns an n period exponential moving average for
        the time series data

        data is a list ordered from oldest (index 0) to most
        recent (index -1)

        alpha is the decay factor

        returns a numeric array of the exponential
        moving average
        """
    # c = 2.0 / (window + 1)
    slow_decay = alpha  # <-- user input
    # slow_span = 2 / slow_decay - 1
    # if len(data) < 2 * slow_span:
    #     raise ValueError("data is too short")
    fast_decay = 5 * slow_decay
    S_i_upper = None

    # initialise the moving average arrays
    slow_ema = []
    filtered_slow_ema = []
    fast_ema = []

    i = 0

    # going forward. Assumes dates are in ascending order
    for row in data:
        try:
            if i == 0:
                slow_ema.append(data[i])
                fast_ema.append(data[i])
            else:
                slow_ema.append(slow_decay * data[i] + (1 - slow_decay) * filtered_slow_ema[i - 1])
                fast_ema.append(fast_decay * data[i] + (1 - fast_decay) * fast_ema[i - 1])

            # run a cut-off Control structure check on the slow_ema just computed
            slow_ema_i, S_i_upper = \
                detect_cumsum(slow_ema[i],
                              data[i],
                              fast_ema[i],
                              i,
                              # 3 * np.std(slow_ema) if len(slow_ema) > 2 else 0,
                              1.5 * mean_abs_dev(price_series=data[:i + 1], ewm_series=slow_ema),
                              S_i_upper)
            filtered_slow_ema.append(slow_ema_i)
        except Exception as e:
            print("Exception index = %s Exception=%s" % (i, str(e)))
            pass
        i += 1
    # [filtered_slow_ema.append(x) for x in data[slow_span + i:]]
    return filtered_slow_ema, fast_ema


def plot_data(col, method="gaussian"):
    # plot the Mid
    ax = data.plot(x="Timestamp", y=col, c="Blue", label="original data")
    # data[col].resample('5min').rolling(win_type='gaussian').mean(std=0.1)
    if method == "gaussian:":
        md = data[col].rolling(window=200, win_type=method).mean(std=0.1)
        ax.plot(md.index, md, c="Red", label="filtered data")
    elif method == "mean":
        md = data[col].resample("5min").mean()
        ax.plot(md.index, md, c="Red", label="filtered data")
    elif method == "ewma":
        '''http://connor-johnson.com/2014/02/01/smoothing-with-exponentially-weighted-moving-averages/'''
        alpha = 0.03
        md = data[col].ewm(adjust=False, alpha=alpha).mean()
        md2, fast_ema = ema(data=data[col].values, alpha=alpha)
        ax.plot(data["Timestamp"], md, c="Red", label=r"filter with single-EWM , $alpha=%s$" % alpha)
        ax.plot(data["Timestamp"][:len(md2)], md2, c="Green",
                label=r"filter with Control structure(CUSUM),$\alpha=%s$" % alpha)
        # ax.plot(data["Timestamp"][:len(fast_ema)], fast_ema, c="Black",
        #         label=r"fast_ema ,$\alpha=%s$" % alpha)

    # ax.plot_date(data.index.to_pydatetime(), data.index)
    ax.set_xlabel("Timestamp")
    ax.set_ylabel(col)
    ax.legend(loc="upper right", shadow=True)
    # Create your formatter object and change the xaxis formatting.
    date_fmt = '%d/%m/%y %H:%M'

    formatter = dates.DateFormatter(date_fmt)
    ax.xaxis.set_major_formatter(formatter)

    plt.gcf().autofmt_xdate()


if __name__ == '__main__':
    data = load_data()
    # plot_data("Mid")
    # plot_data("Spread (cents)")
    meandev = 0.1 # substitute an estimate of stdev here
    my_smooth = AdaptiveEMA(0.03, 0.15, meandev, 3*meandev)
    result = []
    for x in data:
        result.append(my_smooth(x))

    plot_data("Spread(bps)", method="ewma")
    plt.show()
