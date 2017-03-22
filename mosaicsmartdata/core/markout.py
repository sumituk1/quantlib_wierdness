import datetime as dt
import operator
import pandas as pd
from mosaicsmartdata.common.constants import *
from mosaicsmartdata.common.read_config import *
from mosaicsmartdata.core.markout_msg import *
from mosaicsmartdata.core.trade import Trade, Quote


class MarkoutCalculator:
    '''
    A basic markout calculator
    After each price update, returns a list of the markouts completed so far,
    so should be followed by a flattener
    It assumes all messages arrrive in strict timestamp order
    '''

    def __init__(self, lags_list, instr=None):
        self.pending = []
        self.lags_list = lags_list
        self.last_price = pd.DataFrame (columns = ['mid','timestamp']).reset_index()#dict.fromkeys(["mid","timestamp"])
        self.last_timestamp = None

    def generate_markout_requests(self, msg):
        if self.last_price is None:
            print(msg)
            raise ValueError('A trade arrived before any quote data!')
        else:
            # for each markout lag in lags_list, create a markout_msg for this trade
            for mk in self.lags_list:
                if "COB" not in mk:
                    mkmsg = MarkoutMessage(trade=msg,
                                           trade_id=msg.trade_id,
                                           notional=msg.notional,
                                           sym=msg.sym,
                                           side=msg.side,
                                           initial_price=msg.traded_px,
                                           next_timestamp=msg.timestamp + dt.timedelta(0, float(mk)),
                                           dt=mk)
                else:
                    # This is a COB lag. Extract the COB time in UTC
                    COB_time_utc = None

                    # first get the UTC time for COB per ccy of risk
                    if msg.ccy == Currency.EUR:
                        COB_time_utc = get_data_given_section_and_key("GovtBond_Markout", "EGB_COB")
                    elif msg.ccy == Currency.USD:
                        COB_time_utc = get_data_given_section_and_key("GovtBond_Markout", "UST_COB")
                    elif msg.ccy == Currency.GBP:
                        COB_time_utc = get_data_given_section_and_key("GovtBond_Markout", "GBP_COB")

                    # now convert the str_time to time object
                    COB_time_utc = dt.datetime.strptime(COB_time_utc,"%H:%M:%S").time()

                    # now get the COB lag i.e. COB_T0 or COB_T1, COB_T2
                    COB_lag = mk[-1]
                    COB_time_utc = dt.datetime.combine(msg.trade_date, COB_time_utc) + \
                                                       dt.timedelta(days=float(COB_lag))

                    mkmsg = MarkoutMessage(trade=msg,
                                           trade_id=msg.trade_id,
                                           notional=msg.notional,
                                           sym=msg.sym,
                                           side=msg.side,
                                           initial_price=msg.traded_px,
                                           next_timestamp=COB_time_utc,
                                           dt=mk)
                # print(mkmsg)
                self.pending.append(mkmsg)

    def __call__(self, msg):
        self.last_timestamp = msg.timestamp

        if isinstance(msg, Trade):
            self.generate_markout_requests(msg)
            # elif isinstance(msg, Quote) or hasattr(msg, 'mid'):
            # self.last_price = msg.mid()
        elif not isinstance(msg, Quote):
            print(msg)
        # determine which pending markout requests we can complete now

        completed = [x for x in self.pending if x.next_timestamp < self.last_price['timestamp'].values[-1]]
        self.pending = [x for x in self.pending if x not in completed]

        for x in completed:
            x.final_price = self.last_price[self.last_price['timestamp'] <= x.next_timestamp]['mid'].values[-1]
            x.cents_markout = (x.final_price - x.initial_price) * 100 # <-- assumes par_value is 100 for quote and trade
            x.bps_markout = ((x.final_price - x.initial_price) / x.trade.duration / x.trade.par_value) * 10000

            if x.side == TradeSide.Ask:
                x.cents_markout *= -1
                x.bps_markout *= -1

        if isinstance(msg, Quote) or hasattr(msg, 'mid'):
            ix = len(self.last_price)+1
            self.last_price.set_value(ix, 'mid', msg.mid())
            self.last_price.set_value(ix, 'timestamp', msg.timestamp)
            # # self.last_price.loc['mid'] = msg.mid()
            # self.last_price.loc['timestamp'] = msg.timestamp

        return completed


# price markout and value m/o = Price*delta - mktmsg
# trade delta - change in price "Delta" - override
# COB
#

class GovtBondMarkoutCalculator(MarkoutCalculator):
    # Constructor
    boo_contains_COB = False

    def __init__(self, lags_list=None):
        if lags_list is None:
            # get the lags_list from config file
            lags_list_str = get_data_given_section_and_key("GovtBond_Markout", "lags_list")
            # check if there's any "COB"
            # boo_contains_COB = [x for x in lags_list_str.split(',') if "COB" in x]
            # if boo_contains_COB:
            #     lags_list = extract_COB_markout_lags(lags_list_str)
            # else:
            #     lags_list = [float(x) for x in lags_list_str.split(',')]
            lags_list = [x for x in lags_list_str.split(',')]
        else:
            lags_list = lags_list

        self.notional = 0
        # all properties that any trade can have belong in the superclass
        MarkoutCalculator.__init__(self, lags_list=lags_list)

# don't need this code, the function is inherited anyway
#    def __call__(self, msg):
#        return MarkoutCalculator.__call__(self, msg)

        # def __call__(self, msg):
        #     self.last_timestamp = msg.timestamp
        #
        #     if isinstance(msg, Trade):
        #         self.generate_markout_requests(msg)
        #     elif isinstance(msg, Quote):
        #         self.sym = msg.sym
        #     elif not isinstance(msg, Quote):
        #         print(msg)
        #     # determine which pending markout requests we can complete now
        #
        #     completed = [x for x in self.pending if x['next_timestamp'] <
        #                  self.last_timestamp]
        #     self.pending = [x for x in self.pending if x not in completed]
        #
        #     for x in completed:
        #         x['final_price'] = self.last_price
        #         if x['side'] == TradeSide.Bid:
        #             x['markout'] = (x['final_price'] - x['initial_price'])/100*x['notional']
        #         else:
        #             x['markout'] = -1*(x['final_price'] - x['initial_price']) / 100 * x['notional']

        # if isinstance(msg, Quote) or hasattr(msg, 'mid'):
        #     self.last_price = msg.mid()
        #
        # return completed

