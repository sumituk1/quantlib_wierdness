import pandas as pd
import datetime as dt
from copy import  copy
import logging
import pandas as pd

import datetime
from mosaicsmartdata.common.constants import *
from mosaicsmartdata.common.read_config import *
from mosaicsmartdata.core.markout_msg import *
from mosaicsmartdata.core.trade import Trade
from mosaicsmartdata.core.quote import Quote
import time

size_threshold = 100 * 1000  # 100 kb before re-indexing kicks in
class PriceBuffer:
    def __init__(self, buf_incr = 10000):
        self.buf_incr = buf_incr
        self.value = np.zeros(0)
        self.time = pd.Series(np.zeros(0))
        self.last = 0

    def add_point(self, timestamp, value):
        self.last +=1
        if self.last > len(self.value):
            extra_buffer = np.zeros(self.buf_incr)
            extra_buffer[:] = np.NaN
            self.value = np.concatenate([self.value, extra_buffer], axis = 0)
            extra_time = pd.Series(np.zeros(self.buf_incr))
            extra_time[:] = datetime.datetime(2100, 1, 1,1,1,1) # far in the future
            self.time = pd.concat([self.time, extra_time], axis = 0)
        self.time[self.last - 1] = timestamp
        self.value[self.last - 1] = value
        if timestamp == datetime.datetime(2017,1,16,13,50,0):
            print('aaaa') # to set breakpoint here ;)



    def get_last_price_before(self, timestamp):
        filter_ = self.time <= timestamp
        nicedata = self.value[filter_]
        if len(nicedata) > 0:
            return nicedata[-1]
        else:
            return np.NaN

    def throw_away_before(self, timestamp):
        filter_ = self.time < timestamp
        self.value = copy(self.value[filter_])
        self.time = copy(self.time[filter_])


class MarkoutCalculatorPre:
    '''
    A basic markout calculator to handle pre-trade markout
    After each price update, returns a list of the markouts completed so far,
    so should be followed by a flattener
    It assumes all messages arrrive in strict timestamp order
    '''

    def __init__(self, lags_list, max_lag, instr=None):
        self.pending = []
        self.lags_list = lags_list
        self.buffer = PriceBuffer()
        #self.last_price = pd.DataFrame(columns=['mid', 'timestamp']).reset_index()
        self.last_timestamp = None
        self.COB_time_utc = None
        self.max_lag = max_lag

    def __call__(self, msg, COB_time_utc=None):
        # t0 = time.time()
        self.last_timestamp = msg.timestamp
        completed = []
        # t_3 = time.time()
        # print(msg)
        if isinstance(msg, Trade):
            self.COB_time_utc = COB_time_utc
            # Egor - no need to generate markout_requests for pre as they already would have been
            # generated
            # self.generate_markout_requests(msg)
            for mk in self.lags_list:
                mkmsg = MarkoutMessage2(trade=msg,
                                        initial_price=msg.adj_traded_px,
                                        next_timestamp=msg.timestamp + dt.timedelta(0, float(mk)),
                                        timestamp=msg.timestamp,
                                        dt=mk)
                if mkmsg.trade_id == '222' and mk == '-900':
                    print('aaa') # to set breakpoint here
                # if len(self.last_price[self.last_price['timestamp'] <= mkmsg.next_timestamp]['mid'].values) == 0:
                #     # TODO: empty Quote mid for lagged time. Log this
                #     mkmsg.price_markout = None
                # else:
                #     mkmsg.final_price = self.last_price[self.last_price['timestamp'] <=
                #                                         mkmsg.next_timestamp]['mid'].values[-1]
                mkmsg.final_price = self.buffer.get_last_price_before(mkmsg.next_timestamp)
                if mkmsg.final_price is np.NaN:
                    logging.getLogger(__name__).warning('Saw a NaN final price in pre-markouts')
                mkmsg.price_markout = (mkmsg.final_price - mkmsg.initial_price)

                if (mkmsg.side == TradeSide.Ask) and (not mkmsg.price_markout is None):
                    mkmsg.price_markout *= -1

                completed.append(mkmsg)
        elif isinstance(msg, Quote):
            # update the pending markout_messages with the new timestamp
            for x in self.pending:
                x.timestamp = msg.timestamp
        else: # if not isinstance(msg, Quote):
            print(msg)

        # print("MarkoutCalculatorPre(): time spent before timestamp check =%s "%(time.time()-t_3))

        if isinstance(msg, Quote) or hasattr(msg, 'mid'):
            # throw out stale Quotes which have a timestamp > min(abs(lags_list) if lags_list < 0
            # intra-day markout lags given
            # t_3 = time.time()
            # ix = len(self.last_price) + 1
            self.buffer.add_point(msg.timestamp, msg.mid)
            if len(self.buffer.time) > size_threshold:
                stale_timestamp = self.buffer.time[self.buffer.last - 1] - dt.timedelta(0, self.max_lag)
                self.buffer.throw_away_before(stale_timestamp)
            # self.last_price.set_value(ix, 'mid', msg.mid)
            # self.last_price.set_value(ix, 'timestamp', msg.timestamp)
            # print("MarkoutCalculatorPre(): time spent appending Quote =%s " % (time.time() - t_3))
            # t_3 = time.time()
            #stale_timestamp = self.last_price['timestamp'].values[-1] - dt.timedelta(0, self.max_lag)
            # dt.timedelta(0, max([abs(float(x)) for x in self.lags_list]))
            # print("MarkoutCalculatorPre(): time spent calculating stale =%s " % (time.time() - t_3))
            # t_3 = time.time()
            # if len(self.last_price) > size_threshold:
            #     print("Re-indexing!!")
            #     if len(self.last_price[self.last_price['timestamp'] <= stale_timestamp]) > 0:
            #         # re-indexing is expensive!!
            #         self.last_price.drop(self.last_price[self.last_price['timestamp'] < stale_timestamp].index,
            #                              inplace=True)
            #         self.last_price.reset_index(drop=True, inplace=True)
                    # print("MarkoutCalculatorPre(): time spent dropping & re-indexing=%s " % (time.time() - t_3))
        # print("Total time spent in MarkoutCalculatorPre() = %s" % (time.time() - t0))
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
        self.last_timestamp = None
        self.COB_time_utc = None

    def generate_markout_requests(self, msg):
        if self.last_price is None:
            print(msg)
            raise ValueError('A trade arrived before any quote data!')
        else:
            # for each markout lag in lags_list, create a markout_msg for this trade
            for mk in self.lags_list:
                if "COB" not in mk:
                    mkmsg = MarkoutMessage2(trade=msg,
                                            # trade_id=msg.trade_id,
                                            # notional=msg.notional,
                                            # sym=msg.sym,
                                            # side=msg.side,
                                            initial_price=msg.adj_traded_px,
                                            next_timestamp=msg.timestamp + dt.timedelta(0, float(mk)),
                                            dt=mk)
                else:
                    # This is a COB lag. Extract the COB time in UTC
                    # COB_time_utc = None

                    # now get the COB lag i.e. COB_T0 or COB_T1, COB_T2
                    COB_lag = mk[-1]
                    COB_time_utc = dt.datetime.combine(msg.trade_date, self.COB_time_utc) + \
                                   dt.timedelta(days=float(COB_lag))

                    mkmsg = MarkoutMessage2(trade=msg,
                                            # trade_id=msg.trade_id,
                                            # notional=msg.notional,
                                            # sym=msg.sym,
                                            # side=msg.side,
                                            initial_price=msg.traded_px,
                                            next_timestamp=COB_time_utc,
                                            dt=mk)
                # print(mkmsg)
                self.pending.append(mkmsg)

    def __call__(self, msg, COB_time_utc=None):
        # t0 = time.time()
        self.last_timestamp = msg.timestamp

        if isinstance(msg, Trade):
            self.COB_time_utc = COB_time_utc
            self.generate_markout_requests(msg)
            # elif isinstance(msg, Quote) or hasattr(msg, 'mid'):
            # self.last_price = msg.mid
        elif isinstance(msg,Quote):
            # update the pending markout_messages with the new timestamp
            for x in self.pending:
                x.timestamp = msg.timestamp
            # [(lambda x: x.timestamp = msg.timestamp)(x) for x in self.pending]
        else: # if not isinstance(msg, Quote):
            print(msg)
        # determine which pending markout requests we can complete now

        completed = [x for x in self.pending if x.next_timestamp < self.last_timestamp]
        self.pending = [x for x in self.pending if x not in completed]

        for x in completed:
            x.final_price = self.last_price
            x.price_markout = (x.final_price - x.initial_price)
            # x.cents_markout = (x.final_price - x.initial_price)

            if x.side == TradeSide.Ask:
                x.price_markout *= -1

        if isinstance(msg, Quote) or hasattr(msg, 'mid'):
            self.last_price = msg.mid
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
        pre_lags = [x for x in lags_list if x[0] == '-']
        post_lags = [x for x in lags_list if not x[0] == '-']
        if len([x for x in lags_list if "COB" not in x]) > 0:
            self.max_lag = max([abs(float(x)) for x in lags_list if "COB" not in x])
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
        if isinstance(msg, Trade) and self.COB_time_utc is None:
            # set the utc cob time as per traded ccy
            # first get the UTC time for COB per ccy of risk (only possible at trade level)
            if msg.ccy == Currency.EUR:
                self.COB_time_utc = self.COB_time_utc_eur
            elif msg.ccy == Currency.USD:
                self.COB_time_utc = self.COB_time_utc_ust
            elif msg.ccy == Currency.GBP:
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
