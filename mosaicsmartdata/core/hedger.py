import copy
from mosaicsmartdata.common.constants import *
from mosaicsmartdata.common.read_config import *
from mosaicsmartdata.core.trade import Quote, Trade, FixedIncomeHedge
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
            self.last_quotes[msg.sym] = msg  # copy.deepcopy(msg)
            return []

        elif isinstance(msg, Trade):
            hedges = self.hedge_calculator(msg, self.last_quotes)
            return hedges

        else:
            raise ValueError('Message must be a subclass of either Quote or Trade!')


def my_hedge_calculator(msg, lastquotes):
    # as a simple example, just do opposite trade as a hedge
    hedge_dict = msg.__dict__
    hedge_mapper = load_config(msg.ccy)

    min_hedge_delta = float(hedge_mapper['min_hedge_delta'])

    # extract the tenors - first 2 config are hedge specific different config
    tenors_list = sorted([float(x) for x in (sorted([x for x in list(hedge_mapper.keys())])[:-2])])
    # get the hedge(s)
    hedge_arr = hedge_mapper[str([x for x in tenors_list if msg.tenor > x][-1]).rstrip('0').rstrip('.')]
    # set the duration of the hedge based on the Quote object
    if hedge_arr not in lastquotes:
        raise ValueError('No Hedge [rices received before receiving a Trade object!')
    else:
        hedge_quote = lastquotes[hedge_arr]

    hedge_trade = FixedIncomeHedge(trade_id=msg.trade_id + "_HEDGE",
                                   sym=hedge_arr,
                                   paper_trade=True,
                                   notional=1,
                                   delta=None,
                                   timestamp=msg.timestamp,
                                   side=TradeSide.Ask if msg.side == TradeSide.Bid else TradeSide.Bid,
                                   traded_px=hedge_quote.ask if msg.side == TradeSide.Ask else TradeSide.Bid,
                                   client_sys_key=msg.client_sys_key,
                                   trade_date=hedge_quote.timestamp.date(),
                                   ccy=msg.ccy,
                                   is_cash = True,
                                   is_futures=False,
                                   trade_settle_date=None,
                                   min_hedge_delta=min_hedge_delta,
                                   trade = msg,
                                   duration=hedge_quote.duration)

    return hedge_trade


def load_config(ccy):
    if ccy == Currency.USD:
        # load the USD relevant hedge config
        return get_data_given_section('USD_GovtBond_Hedge_Mapper')
    else:
        ValueError('Not implemented')
