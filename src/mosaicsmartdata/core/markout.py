import pandas as pd
import datetime as dt
from copy import  copy
import logging
import pandas as pd

import datetime
from mosaicsmartdata.common.constants import *
from mosaicsmartdata.common.read_config import *
from mosaicsmartdata.core.markout_msg import *
from mosaicsmartdata.core.trade import Trade, InterestRateSwapTrade,FixedIncomeTrade
from mosaicsmartdata.core.quote import Quote


size_threshold = 100 * 1000  # 100 kb before re-indexing kicks in
class PriceBuffer:
    def __init__(self, buf_incr = 10000, max_lag = None):
        self.buf_incr = buf_incr
        self.max_lag = max_lag
        self.value = []#np.zeros(0)
        self.time = []#pd.Series(np.zeros(0))
        self.last = 0

    def add_point(self, timestamp, value):
        self.last +=1
        if self.last > len(self.value):
            time_dummy = datetime.datetime(2100, 1, 1,1,1,1) # far in the future
            self.time += [time_dummy]*self.buf_incr
            self.value += [None]*self.buf_incr
        self.time[self.last - 1] = timestamp
        self.value[self.last - 1] = value

    def get_last_price_before(self, timestamp, cutoff_timestamp = None):
        def filter_fun(time):
            if cutoff_timestamp:
                return time <= timestamp and time > cutoff_timestamp
            else:
                return time <= timestamp

        last_price = float('NaN')
        for i, value in enumerate(self.value):
            if value is None: # we fill the tail of the pre-allocated array with None
                break
            if filter_fun(self.time[i]):
                last_price = value # values are ordered, so take the latest
        return last_price


    def throw_away_before(self, timestamp):
        oldlen = len(self.value)
        self.value = [value for i, value in enumerate(self.value) if self.time[i] >= timestamp]#copy(self.value[np.array(filter_)])
        if self.last == oldlen:
            self.last = len(self.value)# both arrays just full
        else:
            inds = list(range(oldlen))
            new_inds = [ind for i, ind in enumerate(inds) if self.time[i] >= timestamp]
            for i, ind in enumerate(new_inds):
                if ind ==self.last:
                    self.last = i
                    break
            if self.last > len(self.value):
                raise RuntimeError('Error in price buffer!')

        self.time = [time_ for time_ in self.time if time_ >= timestamp]

    def __getstate__(self):
        # trim all unneeded data before saving
        if self.last > 0: # if there's any data in the buffer
            max_lookback = self.time[self.last - 1] + dt.timedelta(seconds=self.max_lag)
            self.throw_away_before(max_lookback)
            self.value = list(self.value[:self.last])
            self.time = list(self.time[:self.last])
        state = self.__dict__.copy()
        return state

def is_quote(x):
    x_type = str(type(x))
    return 'Quote' in x_type or 'PricingContext' in x_type

class MarkoutCalculatorPre:
    '''
    A basic markout calculator to handle pre-trade markout
    After each price update, returns a list of the markouts completed so far,
    so should be followed by a flattener
    It assumes all messages arrrive in strict timestamp order
    '''

    def __init__(self, lags_list, max_lag, instr=None):
        self.lags_list = lags_list
        self.buffer = PriceBuffer(max_lag=max_lag)
        self.last_timestamp = None
        self.COB_time_utc = None
        self.max_lag = max_lag

    def __call__(self, msg, COB_time_utc=None):
        # t0 = time.time()
        self.last_timestamp = msg.timestamp
        completed = []
        # t_3 = time.time()
        # print(msg)
        if isinstance(msg, Trade) or 'trade_id' in msg.__dict__: # workaround for a Python class resolution issue
            self.COB_time_utc = COB_time_utc
            for mk in self.lags_list:
                mkmsg = MarkoutMessage2(trade=msg,
                                        initial_price=msg.traded_price(),
                                        next_timestamp=msg.timestamp + dt.timedelta(0, float(mk)),
                                        timestamp=msg.timestamp,
                                        dt=mk)
                # if price more than 24 hours before desired, treat it as stale
                cutoff_timestamp = mkmsg.next_timestamp + dt.timedelta(0,-24*60*60)
                final_price_context = self.buffer.get_last_price_before(mkmsg.next_timestamp,cutoff_timestamp)
                mkmsg.final_price = mkmsg.trade.valuation_price(final_price_context)
                mkmsg.price_markout = mkmsg.trade.price_diff(mkmsg)

                # TODO: rewrite this!!!
                # if 'price_type' in mkmsg.trade.__dict__ and mkmsg.trade.price_type == PriceType.Upfront and mkmsg.dt == "0":
                #     # Handle upfront_fee at point of trade
                #     mkmsg.price_markout = (mkmsg.final_price + mkmsg.initial_price)
                #
                #     # Reset the traded_px to be the current NPV of the swap for later markouts
                #     for y in self.pending:
                #         if y not in completed:
                #             y.initial_price = mkmsg.final_price
                # else:
                #     mkmsg.price_markout = (mkmsg.final_price - mkmsg.initial_price)
                #
                # mkmsg.price_markout*= mkmsg.trade.side_mult()
                if mkmsg.final_price is np.NaN:
                    logging.getLogger(__name__).warning('Saw a NaN final price in pre-markouts')

                completed.append(mkmsg)
        elif is_quote(msg):
            pass
        else: # if not isinstance(msg, Quote):
            error_string = 'Markout calculator only wants trades or price data, instead it got ' + str(msg)
            logging.getLogger(__name__).error(error_string)
            raise ValueError(error_string)

        if is_quote(msg):
            try: # if it's a vanilla quote
                last_price = msg.mid
            except: # if it's a PricingContext
                last_price = msg
            # TODO adjust so works with PriceContexts
            self.buffer.add_point(msg.timestamp, last_price)
            if len(self.buffer.time) > size_threshold:
                stale_timestamp = self.buffer.time[self.buffer.last - 1] - dt.timedelta(0, self.max_lag)
                self.buffer.throw_away_before(stale_timestamp)
        return completed


class MarkoutCalculatorPost:
    '''
    A basic markout calculator to handle post trade markouts
    After each price update, returns a list of the markouts completed so far,
    so should be followed by a flattener
    It assumes all messages arrrive in strict timestamp order
    '''

    def __init__(self, lags_list, instr=None):
        self.pending = []
        self.lags_list = lags_list
        self.last_price = None
        self.nonpaper_legs_count = None
        self.display_DV01 = None
        self.last_timestamp = None
        self.COB_time_utc = None

    def only_cob_markouts(self):
        out = [True if "COB" in x else False for x in self.lags_list]
        return out

    def generate_markout_requests(self, msg):
        if self.last_price is None and not self.only_cob_markouts():
            print(msg)
            raise ValueError('A trade arrived before any quote data!')
        else:
            # for each markout lag in lags_list, create a markout_msg for this trade
            for mk in self.lags_list:
                if "COB" not in mk:
                    next_timestamp = msg.timestamp + dt.timedelta(0, float(mk))
                else:
                    # This is a COB lag. Extract the COB time in UTC
                    # COB_time_utc = None
                    # now get the COB lag i.e. COB_T0 or COB_T1, COB_T2
                    COB_lag = mk[-1]
                    next_timestamp = dt.datetime.combine(msg.trade_date, self.COB_time_utc) + \
                                   dt.timedelta(days=float(COB_lag))

                mkmsg = MarkoutMessage2(trade=msg,
                                        initial_price=msg.traded_price(),
                                        next_timestamp = next_timestamp,
                                        dt=mk)

                self.pending.append(mkmsg)

    def __call__(self, msg, COB_time_utc=None):
        # t0 = time.time()
        self.last_timestamp = msg.timestamp

        if isinstance(msg, Trade) or 'trade_id' in msg.__dict__: # a workaround for Python class resolution issue
            self.COB_time_utc = COB_time_utc
            self.generate_markout_requests(msg)
        elif is_quote(msg):
            for x in self.pending: # update the pending markout_messages with the new timestamp
                x.timestamp = msg.timestamp
        else: # if not isinstance(msg, Quote):
            error_string = 'Markout calculator only wants trades or price data, instead it got ' + str(msg)
            logging.getLogger(__name__).error(error_string)
            raise ValueError(error_string)

        # determine which pending markout requests we can complete now

        completed = [x for x in self.pending if x.next_timestamp < self.last_timestamp]
        self.pending = [x for x in self.pending if x not in completed]

        for x in completed:
            x.final_price = x.trade.valuation_price(self.last_price)
            x.price_markout = x.trade.price_diff(x)
            # TODO: rewrite this!!!. Refactored to price_diff()

            # if 'price_type' in x.trade.__dict__ and x.trade.price_type == PriceType.Upfront and x.dt == "0":
            #     # Handle upfront_fee at point of trade
            #     x.price_markout = (x.final_price + x.initial_price)
            #
            #     # Reset the traded_px to be the current NPV of the swap for later markouts
            #     for y in self.pending:
            #         if y not in completed:
            #             y.initial_price = x.final_price
            # else:
            #     x.price_markout = (x.final_price - x.initial_price)
            #
            # x.price_markout *= x.trade.side_mult()

        if is_quote(msg):
            try: # if it's a vanilla quote
                self.last_price = msg.mid
            except: # if it's a PricingContext
                self.last_price = msg
        # print("Time spent in MarkoutCalculatorPost() = %s"%(time.time()-t0))
        return completed


class MarkoutCalculator:
    '''
    A basic markout calculator to handle both pre and post trade markouts
    After each price update, returns a list of the markouts completed so far,
    so should be followed by a flattener
    It assumes all messages arrrive in strict timestamp order
    '''

    def __init__(self, lags_list, instr=None):
        self.COB_time_utc = None
        self.timestamp = None
        # self.configurator = configurator
        lags_list = [str(lag) for lag in lags_list] # to allow to enter the lags as numbers

        if any([ 'COB' in lag for lag in lags_list]):
            self.cob = True
        else:
            self.cob = False
        pre_lags = [x for x in lags_list if x[0] == '-']
        post_lags = [x for x in lags_list if not x[0] == '-']
        if len([x for x in lags_list if "COB" not in x]) > 0:
            # this is the biggest backward-looking lag
            self.max_lag = min([float(x) for x in lags_list if "COB" not in x])
        else:
            self.max_lag = None
        # always do a post trade
        self.markout_calculator_post = MarkoutCalculatorPost(lags_list=post_lags)
        self.markout_calculator_pre = None
        if len(pre_lags) > 0:
            self.markout_calculator_pre = MarkoutCalculatorPre(max_lag=self.max_lag, lags_list=pre_lags)

    def generate_markout_requests(self, msg):
        self.markout_calculator_post.generate_markout_requests(msg)
        if self.markout_calculator_pre is not None:
            self.markout_calculator_pre.generate_markout_requests(msg)

    def __call__(self, msg):
        if isinstance(msg, Trade) and self.cob and self.COB_time_utc is None:
            # set the utc cob time as per traded ccy
            # first get the UTC time for COB per ccy of risk (only possible at trade level)
            if msg.ccy == Currency.EUR.value:
                self.COB_time_utc = self.COB_time_utc_eur
            elif msg.ccy == Currency.USD.value:
                self.COB_time_utc = self.COB_time_utc_ust
            elif msg.ccy == Currency.GBP.value:
                self.COB_time_utc = self.COB_time_utc_gbp
            # now convert the str_time to time object
            self.COB_time_utc = dt.datetime.strptime(self.COB_time_utc, "%H:%M:%S").time()

        completed = []
        if self.markout_calculator_pre is not None:
            [completed.append(x) for x in self.markout_calculator_pre(msg, self.COB_time_utc)]
        [completed.append(x) for x in self.markout_calculator_post(msg, self.COB_time_utc)]
        return completed


# price markout and value m/o = Price*delta - mktmsg
# trade delta - change in price "Delta" - override
# COB
#

class GovtBondMarkoutCalculator(MarkoutCalculator):
    # Constructor
    boo_contains_COB = False

    def __init__(self, lags_list=None):
        configurator = Configurator()
        # get the COB time per ccy
        self.COB_time_utc_eur = configurator.get_data_given_section_and_key("GovtBond_Markout", "EGB_COB")
        self.COB_time_utc_ust = configurator.get_data_given_section_and_key("GovtBond_Markout", "UST_COB")
        self.COB_time_utc_gbp = configurator.get_data_given_section_and_key("GovtBond_Markout", "GBP_COB")
        # set the lags_list
        if lags_list is None:
            # get the lags_list from config file
            lags_list_str = configurator.get_data_given_section_and_key("GovtBond_Markout", "lags_list")
            lags_list = [x for x in lags_list_str.split(',')]
        else:
            lags_list = lags_list

        # self.cob_mode = not [x for x in lags_list if "COB" not in x]
        # all properties that any trade can have belong in the superclass
        MarkoutCalculator.__init__(self, lags_list=lags_list)
