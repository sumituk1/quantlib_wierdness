from mosaicsmartdata.common.constants import *
from mosaicsmartdata.common.read_config import *
from mosaicsmartdata.core.instrument_singleton import InstumentSingleton
from mosaicsmartdata.core.trade import Quote, Trade, FixedIncomeFuturesHedge, FixedIncomeOTCHedge


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

    def __init__(self, hedge_calculator, product_class=None):
        self.hedge_calculator = hedge_calculator
        self.last_quotes = {}
        # Load instrument static
        # self.instrument_static = InstumentSingleton()
        self.product_class = product_class
        self.configurator = Configurator() # <- passed in configurator object

    def __call__(self, msg):
        if isinstance(msg, Quote):
            # store the latest quote for each instrument;
            # make a copy just in case the msg object gets modififed downstream
            self.last_quotes[msg.sym] = msg  # copy.deepcopy(msg)
            return [msg]

        elif isinstance(msg, Trade):
            hedges = self.hedge_calculator(msg,
                                           self.last_quotes,
                                           # self.instrument_static,
                                           # self.configurator,
                                           self.product_class)
            # want to send the original trade on as well
            package = hedges + [msg]
            for x in package:
                x.package_size = len(package)
            return package
        else:
            raise ValueError('Message must be a subclass of either Quote or Trade!')


'''Extracts a duration based beta'''


# def extract_beta_0(hedge_quote_sym,
#                    trade_duration,
#                    hedge_sym_arr,
#                    lastquotes,
#                    product_class=ProductClass.GovtBond,
#                    trade_delta=None,
#                    hedge_delta=None):
#     # get the other hedge instr
#     if len(hedge_sym_arr) == 1:
#         return 1
#     other_hedge_sym = [x for x in hedge_sym_arr if not x == hedge_quote_sym][0]
#
#     if product_class == ProductClass.BondFutures:
#         if lastquotes[hedge_quote_sym].duration > trade_duration:
#             return (trade_delta - hedge_delta[other_hedge_sym]) / \
#                    abs((hedge_delta[hedge_quote_sym] - hedge_delta[other_hedge_sym]))
#         else:
#             return (hedge_delta[other_hedge_sym] - trade_duration) / \
#                    abs((hedge_delta[hedge_quote_sym] - hedge_delta[other_hedge_sym]))
#     elif product_class == ProductClass.GovtBond:
#         if lastquotes[hedge_quote_sym].duration > trade_duration:
#             # ths passed in hedge_quote is the right_wing hedge instr
#             return (trade_duration - lastquotes[other_hedge_sym].duration) / \
#                    abs((lastquotes[hedge_quote_sym].duration - lastquotes[other_hedge_sym].duration))
#         else:
#             # ths passed in hedge_quote is the left_wing hedge instr
#             return (lastquotes[other_hedge_sym].duration - trade_duration) / \
#                    abs((lastquotes[hedge_quote_sym].duration - lastquotes[other_hedge_sym].duration))
#     else:
#         raise ValueError("Hedging logic not implemented!!")


# current used implementation

# Looks at the left and the right hedge.
# Can ONLY handle 2 hedges.
# NOTE: hedge weights are inversely proportional to the diff of duration
def extract_beta(hedge_quote_sym, trade_duration, hedge_sym_arr, lastquotes):
    if len(hedge_sym_arr) == 0:
        raise ValueError("extract_beta called with no hedge_sym passed in")
    if len(hedge_sym_arr) == 1:
        return 1
    other_hedge_sym = [x for x in hedge_sym_arr if not x == hedge_quote_sym][0]
    if lastquotes[hedge_quote_sym].duration > trade_duration:
        return (trade_duration - lastquotes[other_hedge_sym].duration) / \
               abs((lastquotes[hedge_quote_sym].duration - lastquotes[other_hedge_sym].duration))
    else:
        return (lastquotes[other_hedge_sym].duration - trade_duration) / \
               abs((lastquotes[hedge_quote_sym].duration - lastquotes[other_hedge_sym].duration))


'''Implementation of the Hedge calculation. This is triggered by the Hedger class'''


def my_hedge_calculator(msg,
                        lastquotes,
                        # instrument_static,
                        # configurator,
                        product_class=None):
    hedge_dict = msg.__dict__
    # hedge_trades = []
    instrument_static = InstumentSingleton()
    configurator = Configurator()
    msg_processed = False

    if product_class is not None:
        # caller passed in specific hedge class to hedge the underlying
        if product_class == ProductClass.BondFutures:
            hedge_trades, msg_processed = perform_futures_hedge(msg, lastquotes)
        elif product_class == ProductClass.GovtBond:
            hedge_trades, msg_processed = perform_cash_hedge(msg, lastquotes)
        # msg_processed = True  # TODO: currently we support ONLY Futures OR Cash hedging

    # No specific hedge class passed in. So walk the config and try and do the hedging, starting with Futures
    if not msg_processed:
        hedge_trades, msg_processed = perform_futures_hedge(msg, lastquotes)
        # hedge_trades.append(hedge_trades_futures)
    if not msg_processed:
        # No futures hedging performed.
        hedge_trades, _ = perform_cash_hedge(msg, lastquotes)
        # hedge_trades.append(hedge_trades_cash)
    return hedge_trades


def load_config(ccy, hedge_class):
    configurator = Configurator()
    if ccy == Currency.USD:
        if hedge_class == HedgeClass.Listed:
            # load the USD relevant hedge config
            try:
                return configurator.get_data_given_section('USD_GovtBond_Listed_Hedge_Mapper')
            except configparser.NoSectionError:
                # section not present
                return ""
        else:
            try:
                return configurator.get_data_given_section('USD_GovtBond_OTC_Hedge_Mapper')
            except configparser.NoSectionError:
                return ""
    else:
        ValueError('Not implemented')


# Cash hedging
def perform_cash_hedge(msg, lastquotes):
    ''' Perform OTC hedge'''
    instrument_static = InstumentSingleton()
    configurator = Configurator()
    hedge_otc_mapper = load_config(msg.ccy, HedgeClass.OTC)
    msg_processed = False
    hedge_trades = []
    if not hedge_otc_mapper == "":
        msg_processed = True
        min_hedge_delta = float(hedge_otc_mapper['min_hedge_delta'])
        set_beta = False
        # extract the tenors - first 2 config are hedge specific different config
        tenors_list = sorted([float(x) for x in (sorted([x for x in list(hedge_otc_mapper.keys())])[:-2])])
        # get the hedge sym(s)
        hedge_sym_arr = hedge_otc_mapper[str([x for x in tenors_list if msg.tenor >= x][-1]).rstrip('0').rstrip('.')]
        hedge_sym_arr = hedge_sym_arr.split(',')

        # handle more than one right-wing
        if sum([(lambda x: lastquotes[x].duration > msg.duration)(x) for x in hedge_sym_arr]) > 1:
            del hedge_sym_arr[-1]

        # handle more than one left-wing
        if sum([(lambda x: lastquotes[x].duration < msg.duration)(x) for x in hedge_sym_arr]) > 1:
            del hedge_sym_arr[0]

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
                    msg.beta[hedge_sym_arr[i]] = extract_beta(hedge_quote.sym,
                                                              trade_duration=msg.duration,
                                                              hedge_sym_arr=hedge_sym_arr,
                                                              lastquotes=lastquotes)
                    # msg.beta[hedge_sym_arr[i]] = 1 / num_hedges
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

    return hedge_trades, msg_processed


''' ---Process for LISTED--- '''


def perform_futures_hedge(msg, lastquotes):
    ''' ---Process for LISTED--- '''
    instrument_static = InstumentSingleton()
    configurator = Configurator()
    hedge_trades = []
    msg_processed = False
    hedge_listed_mapper = load_config(msg.ccy, HedgeClass.Listed,configurator)
    if not hedge_listed_mapper == "":
        msg_processed = True
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
                contract_size = instrument_static(sym=hedge_quote.sym)['contract_size']
                # contract_delta = FixedIncomeFuturesHedge.calculate_futures_delta(contract_size=contract_size,
                #                                                                  futures_duration=hedge_quote.duration)
                if set_beta:
                    # get the trade_beta to this hedge
                    msg.beta[hedge_sym_arr[i]] = extract_beta(hedge_quote.sym,
                                                              trade_duration=msg.duration,
                                                              hedge_sym_arr=hedge_sym_arr,
                                                              lastquotes=lastquotes)
                # now construct the hedge
                hedge_listed_trade = \
                    FixedIncomeFuturesHedge(trade_id=msg.trade_id + "_LISTED_HEDGE_" + str(i),
                                            package_id=msg.package_id,
                                            sym=hedge_sym_arr[i],
                                            duration=hedge_quote.duration,
                                            paper_trade=True,
                                            notional=contract_size,
                                            trade_delta=msg.delta,  # <-- underlying trade_delta to be hedged
                                            timestamp=msg.timestamp,
                                            side=TradeSide.Ask if msg.side == TradeSide.Bid else TradeSide.Bid,
                                            traded_px=hedge_quote.ask if msg.side == TradeSide.Ask else hedge_quote.bid,
                                            client_sys_key=msg.client_sys_key,
                                            trade_date=hedge_quote.timestamp.date(),
                                            ccy=msg.ccy,
                                            trade_beta=msg.beta,
                                            trade_settle_date=msg.trade_settle_date,
                                            min_hedge_delta=min_hedge_delta)

                hedge_trades.append(hedge_listed_trade)
    return hedge_trades, msg_processed
