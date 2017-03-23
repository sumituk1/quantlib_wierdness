import copy
from mosaicsmartdata.core.trade import Quote,Trade
from mosaicsmartdata.common.constants import *


class Hedger:
    '''
    A basic hedge trade generator
    After each trade, returns a list containing the trade plus the hedge trades,
    if any; after each quote returns an empty list
    so should be followed by a flattener.
    The hedge trades returned should have hedge.parent_id = trade.trade_id
    and hedge.paper_trade = True.
    It assumes all messages arrrive in strict timestamp order
    '''

    def __init__(self, hedge_calculator):
        self.hedge_calculator = hedge_calculator
        self.last_quotes = {}

    def __call__(self, msg):
        if isinstance(msg, Quote):
            # store the latest quote for each instrument;
            # make a copy just in case the msg object gets modififed downstream
            self.last_quotes[msg.sym] = copy.deepcopy(msg)

            return []

        elif isinstance(msg, Trade):
            hedges = self.hedge_calculator(msg, self.last_quotes)

            return hedges + [msg]

        else:
            raise ValueError('Message must be a subclass of either Quote or Trade!')


def my_hedge_calculator(msg, lastquotes):
    # as a simple example, just do opposite trade as a hedge
    hedge_dict = msg.__dict__

    if msg.side == TradeSide.Bid:
        hedge_dict.side == TradeSide.Ask
    else:
        hedge_dict.side == TradeSide.Bid

    hedge_dict.trade_id = 'hedge_1_' + msg.trade_id
    hedge_dict.paper_trade = True

    return msg.__class__(**hedge_dict)