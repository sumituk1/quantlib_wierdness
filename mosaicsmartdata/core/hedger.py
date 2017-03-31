import copy
from mosaicsmartdata.common.constants import *
from mosaicsmartdata.common.read_config import *
from mosaicsmartdata.core.trade import Quote, Trade, FixedIncomeFuturesHedge, FixedIncomeOTCHedge
from mosaicsmartdata.common.constants import *


class HedgeClass:
    Listed = 0
    OTC = 1


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
            return [msg]

        elif isinstance(msg, Trade):
            hedges = self.hedge_calculator(msg, self.last_quotes)
            # want to send the original trade on as well
            return hedges + [msg]
        else:
            raise ValueError('Message must be a subclass of either Quote or Trade!')


'''Extracts a duration based beta'''
def extract_beta(i, trade_duration, hedge_sym_arr, lastquotes):
    other_hedge_sym = [x for x in hedge_sym_arr if not x == hedge_sym_arr[i]]
    if lastquotes[hedge_sym_arr[i]].duration > trade_duration:
        return (lastquotes[hedge_sym_arr[i]].duration - trade_duration) / \
               (lastquotes[hedge_sym_arr[i]].duration - lastquotes[other_hedge_sym].duration)
    else:
        return (trade_duration - lastquotes[hedge_sym_arr[i]].duration) / \
               (lastquotes[hedge_sym_arr[i]].duration - lastquotes[other_hedge_sym].duration)


def my_hedge_calculator(msg, lastquotes):
    # as a simple example, just do opposite trade as a hedge
    hedge_dict = msg.__dict__
    hedge_trades = []
    hedge_listed_trade = None
    hedge_otc_trade = None
    ''' ---Process for LISTED--- '''
    hedge_listed_mapper = load_config(msg.ccy, HedgeClass.Listed)
    if not hedge_listed_mapper == "":
        min_hedge_delta = float(hedge_listed_mapper['min_hedge_delta'])
        set_beta = False
        # extract the tenors - first 2 config are hedge specific different config
        tenors_list = sorted([float(x) for x in (sorted([x for x in list(hedge_listed_mapper.keys())])[:-2])])
        # get the hedge sym(s)
        hedge_sym_arr = hedge_listed_mapper[str([x for x in tenors_list if msg.tenor > x][-1]).rstrip('0').rstrip('.')]
        hedge_sym_arr = hedge_sym_arr.split(',')

        num_hedges = len([x for x in hedge_sym_arr if x in lastquotes])
        # set the duration of the hedge based on the Quote object
        # if hedge_sym_arr not in lastquotes:
        if num_hedges == 0:
            raise ValueError('No Hedge prices received before receiving a Trade object!')
        else:
            # hedge_listed_trade = [None] * num_hedges
            if not msg.beta:
                set_beta = True
            for i in range(0, num_hedges):
                hedge_quote = lastquotes[hedge_sym_arr[i]]
                if set_beta:
                    msg.beta[hedge_sym_arr[i]] = 1 / num_hedges
                hedge_listed_trade = \
                    FixedIncomeFuturesHedge(trade_id=msg.trade_id + "_LISTED_HEDGE_" + str(i),
                                            package_id=msg.package_id,
                                            sym=hedge_sym_arr[i],
                                            paper_trade=True,
                                            notional=100000,  # <- typically futures notional is 100000
                                            delta=None,  # <-- TODO:ALWAYS pass in Futures delta
                                            timestamp=msg.timestamp,
                                            side=TradeSide.Ask if msg.side == TradeSide.Bid else TradeSide.Bid,
                                            traded_px=hedge_quote.ask if msg.side == TradeSide.Ask else hedge_quote.bid,
                                            client_sys_key=msg.client_sys_key,
                                            trade_date=hedge_quote.timestamp.date(),
                                            ccy=msg.ccy,
                                            trade_settle_date=msg.trade_settle_date,
                                            min_hedge_delta=min_hedge_delta)
                # trade=msg)
                # duration=hedge_quote.duration)
                # # set the duration of the hedge based on the Quote object
                # if hedge_sym_arr not in lastquotes:
                #     raise ValueError('No Hedge [rices received before receiving a Trade object!')
                # else:
                #     hedge_quote = lastquotes[hedge_sym_arr]
            hedge_trades.append(hedge_listed_trade)

    ''' ---Now process for OTC--- '''
    hedge_otc_mapper = load_config(msg.ccy, HedgeClass.OTC)
    if not hedge_otc_mapper == "":
        min_hedge_delta = float(hedge_otc_mapper['min_hedge_delta'])
        set_beta = False
        # extract the tenors - first 2 config are hedge specific different config
        tenors_list = sorted([float(x) for x in (sorted([x for x in list(hedge_otc_mapper.keys())])[:-2])])
        # get the hedge sym(s)
        hedge_sym_arr = hedge_otc_mapper[str([x for x in tenors_list if msg.tenor > x][-1]).rstrip('0').rstrip('.')]
        hedge_sym_arr = hedge_sym_arr.split(',')
        num_hedges = len([x for x in hedge_sym_arr if x in lastquotes])
        # set the duration of the hedge based on the Quote object
        # if hedge_sym_arr not in lastquotes:
        if num_hedges == 0:
            hedge_otc_trade = []
            raise ValueError('No Hedge prices received before receiving a Trade object!')
        else:
            if not msg.beta:
                set_beta = True
            # hedge_otc_trade = [None] * num_hedges
            for i in range(0, num_hedges):
                hedge_quote = lastquotes[hedge_sym_arr[i]]
                if set_beta:
                    # TODO: distribute beta between left leg and right leg
                    # msg.beta[hedge_sym_arr[i]] = extract_beta(i, msg.duration, hedge_sym_arr, lastquotes)
                    msg.beta[hedge_sym_arr[i]] = 1 / num_hedges
                hedge_otc_trade = \
                    FixedIncomeOTCHedge(trade_id=msg.trade_id + "_OTC_HEDGE_" + str(i),
                                        package_id=msg.package_id,
                                        sym=hedge_sym_arr[i],
                                        paper_trade=True,
                                        notional=1,  # <- typically futures notional is 100000
                                        delta=None,  # <-- TODO:ALWAYS pass in Futures delta
                                        timestamp=msg.timestamp,
                                        side=TradeSide.Ask if msg.side == TradeSide.Bid else TradeSide.Bid,
                                        traded_px=hedge_quote.ask if msg.side == TradeSide.Ask else hedge_quote.bid,
                                        client_sys_key=msg.client_sys_key,
                                        trade_date=hedge_quote.timestamp.date(),
                                        ccy=msg.ccy,
                                        trade_delta=msg.delta,
                                        trade_settle_date=msg.trade_settle_date,
                                        min_hedge_delta=min_hedge_delta,
                                        trade_beta=msg.beta,
                                        duration=hedge_quote.duration)
                hedge_trades.append(hedge_otc_trade)
    return hedge_trades


def load_config(ccy, hedge_class):
    if ccy == Currency.USD:
        if hedge_class == HedgeClass.Listed:
            # load the USD relevant hedge config
            try:
                return get_data_given_section('USD_GovtBond_LISTED_Hedge_Mapper')
            except configparser.NoSectionError:
                # section not present
                return ""
        else:
            try:
                return get_data_given_section('USD_GovtBond_OTC_Hedge_Mapper')
            except configparser.NoSectionError:
                return ""
    else:
        ValueError('Not implemented')
