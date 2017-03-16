from core.trade import Trade, Quote
from com.mosaic.common.constants import *
from common.read_config import *
import datetime as dt


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
        self.last_price = None
        self.last_timestamp = None

    def generate_markout_requests(self, msg):
        if self.last_price is None:
            print(msg)
            raise ValueError('A trade arrived before any quote data!')
        else:
            for mk in self.lags_list:
                mkmsg = {'trade': msg,
                         'trade_id': msg.trade_id,
                         'notional': msg.notional,
                         'side': msg.side,
                         'initial_price': msg.traded_px, # self.last_price,
                         'next_timestamp': msg.timestamp + dt.timedelta(0, mk),  # mk in secs.
                         'dt': mk  # mk in secs
                         }
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

        completed = [x for x in self.pending if x['next_timestamp'] <
                     self.last_timestamp]
        self.pending = [x for x in self.pending if x not in completed]

        for x in completed:
            x['final_price'] = self.last_price
            x['markout'] = x['final_price'] - x['initial_price']

        if isinstance(msg, Quote) or hasattr(msg, 'mid'):
            self.last_price = msg.mid()

        return completed


class GovtBondMarkoutCalculator(MarkoutCalculator):
    # Constructor
    def __init__(self, lags_list=None):
        if lags_list is None:
            # get the lags_list from config file
            lags_list_str = get_data_given_section_and_key("GovtBond_Markout", "lags_list")
            lags_list = [float(x) for x in lags_list_str.split(',')]
        else:
            lags_list = lags_list

        self.notional = 0
        # all properties that any trade can have belong in the superclass
        MarkoutCalculator.__init__(self, lags_list=lags_list)

    def __call__(self, msg):
        self.last_timestamp = msg.timestamp

        if isinstance(msg, Trade):
            self.generate_markout_requests(msg)
            # elif isinstance(msg, Quote) or hasattr(msg, 'mid'):
            # self.last_price = msg.mid()
        elif not isinstance(msg, Quote):
            print(msg)
        # determine which pending markout requests we can complete now

        completed = [x for x in self.pending if x['next_timestamp'] <
                     self.last_timestamp]
        self.pending = [x for x in self.pending if x not in completed]

        for x in completed:
            x['final_price'] = self.last_price
            if x['side'] == TradeSide.Bid:
                x['markout'] = (x['final_price'] - x['initial_price'])/100*x['notional']
            else:
                x['markout'] = -1*(x['final_price'] - x['initial_price']) / 100 * x['notional']

        if isinstance(msg, Quote) or hasattr(msg, 'mid'):
            self.last_price = msg.mid()

        return completed



