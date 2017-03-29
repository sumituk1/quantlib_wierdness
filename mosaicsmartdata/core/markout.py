import pandas as pd
import datetime as dt
from mosaicsmartdata.common.constants import *
from mosaicsmartdata.common.read_config import *
from mosaicsmartdata.core.markout_msg import *
from mosaicsmartdata.core.trade import Trade, Quote


class MarkoutCalculatorPre:
    '''
    A basic markout calculator to handle pre-trade markout
    After each price update, returns a list of the markouts completed so far,
    so should be followed by a flattener
    It assumes all messages arrrive in strict timestamp order
    '''

    def __init__(self, lags_list, instr=None):
        self.pending = []
        self.lags_list = lags_list
        self.last_price = pd.DataFrame(columns=['mid', 'timestamp']).reset_index()
        self.last_timestamp = None
        self.COB_time_utc = None

    def generate_markout_requests(self, msg):
        if len(self.last_price) == 0:
            # FOR COB mode, we will do a markout in the future once the COB is triggered
            print(msg)
            raise ValueError('A trade arrived before any quote data!')
        else:
            # for each markout lag in lags_list, create a markout_msg for this trade
            for mk in self.lags_list:
                mkmsg = MarkoutMessage2(trade=msg,
                                        # trade_id=msg.trade_id,
                                        # notional=msg.notional,
                                        # sym=msg.sym,
                                        # side=msg.side,
                                        initial_price=msg.traded_px,
                                        next_timestamp=msg.timestamp + dt.timedelta(0, float(mk)),
                                        dt=mk)
                # print(mkmsg)
                self.pending.append(mkmsg)

    def __call__(self, msg, COB_time_utc=None):
        self.last_timestamp = msg.timestamp
        completed = []
        # print(msg)
        if isinstance(msg, Trade):

            self.COB_time_utc = COB_time_utc
            # Egor - no need to generate markout_requests for pre as they already would have been
            # generated
            # self.generate_markout_requests(msg)
            for mk in self.lags_list:
                mkmsg = MarkoutMessage2(trade=msg,
                                        initial_price=msg.traded_px,
                                        next_timestamp=msg.timestamp + dt.timedelta(0, float(mk)),
                                        dt=mk)
                if len(self.last_price[self.last_price['timestamp'] <= mkmsg.next_timestamp]['mid'].values) == 0:
                    # TODO: empty Quote mid for lagged time. Log this
                    mkmsg.price_markout = None
                else:
                    mkmsg.final_price = self.last_price[self.last_price['timestamp'] <=
                                                        mkmsg.next_timestamp]['mid'].values[-1]
                    mkmsg.price_markout = (mkmsg.final_price - mkmsg.initial_price)

                if (mkmsg.side == TradeSide.Ask) and (not mkmsg.price_markout is None):
                    mkmsg.price_markout *= -1

                completed.append(mkmsg)

        elif not isinstance(msg, Quote):
            print(msg)

        # COMMENTED AS PER EGOR'S SUGGESTION.
        # ==================================
        # completed = []
        #
        # if len(self.last_price) > 0:
        #     completed = [x for x in self.pending if
        #                  x.next_timestamp < self.last_price['timestamp'].values[-1]]  # cut_off]
        #     self.pending = [x for x in self.pending if x not in completed]
        #
        # for x in completed:
        #     x.final_price = self.last_price[self.last_price['timestamp'] <= x.next_timestamp]['mid'].values[-1]
        #     x.price_markout = (x.final_price - x.initial_price)
        #
        #     if x.side == TradeSide.Ask:
        #         x.price_markout *= -1

        if isinstance(msg, Quote) or hasattr(msg, 'mid'):
            # throw out stale Quotes which have a timestamp > min(abs(lags_list) if lags_list < 0
            # intra-day markout lags given
            ix = len(self.last_price) + 1
            self.last_price.set_value(ix, 'mid', msg.mid)
            self.last_price.set_value(ix, 'timestamp', msg.timestamp)

            stale_timestamp = self.last_price['timestamp'].values[-1] - \
                              dt.timedelta(0, max([abs(float(x)) for x in self.lags_list]))

            if len(self.last_price[self.last_price['timestamp'] <= stale_timestamp]) > 0:
                # re-indexing is expensive!!
                self.last_price.drop(self.last_price[self.last_price['timestamp'] < stale_timestamp].index,
                                     inplace=True)
                self.last_price.reset_index(drop=True, inplace=True)

                # if not self.cob_mode:
                #
                # else:
                #     # Only COB markouts
                #     # no need to store intra-day Quotes. Only store COB markouts
                #
                #     if self.COB_time_utc is not None and msg.timestamp.time() <= self.COB_time_utc:
                #         ix = len(self.last_price)
                #         self.last_price.set_value(ix, 'mid', msg.mid)
                #         self.last_price.set_value(ix, 'timestamp', msg.timestamp)
                #         # self.last_price = pd.DataFrame({'mid': [msg.mid], 'timestamp': [msg.timestamp]})
                #
                #         # # self.last_price.loc['mid'] = msg.mid
                #         # self.last_price.loc['timestamp'] = msg.timestamp

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
                                            initial_price=msg.traded_px,
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
        self.last_timestamp = msg.timestamp

        if isinstance(msg, Trade):
            self.COB_time_utc = COB_time_utc
            self.generate_markout_requests(msg)
            # elif isinstance(msg, Quote) or hasattr(msg, 'mid'):
            # self.last_price = msg.mid
        elif not isinstance(msg, Quote):
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

        pre_lags = [x for x in lags_list if x[0] == '-']
        post_lags = [x for x in lags_list if not x[0] == '-']
        # always do a post trade
        self.markout_calculator_post = MarkoutCalculatorPost(lags_list=post_lags)
        self.markout_calculator_pre = None
        if len(pre_lags) > 0:
            self.markout_calculator_pre = MarkoutCalculatorPre(lags_list=pre_lags)

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
        # get the COB time per ccy
        self.COB_time_utc_eur = get_data_given_section_and_key("GovtBond_Markout", "EGB_COB")
        self.COB_time_utc_ust = get_data_given_section_and_key("GovtBond_Markout", "UST_COB")
        self.COB_time_utc_gbp = get_data_given_section_and_key("GovtBond_Markout", "GBP_COB")
        # set the lags_list
        if lags_list is None:
            # get the lags_list from config file
            lags_list_str = get_data_given_section_and_key("GovtBond_Markout", "lags_list")
            lags_list = [x for x in lags_list_str.split(',')]
        else:
            lags_list = lags_list

        # self.cob_mode = not [x for x in lags_list if "COB" not in x]
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
        #     self.last_price = msg.mid
        #
        # return completed
