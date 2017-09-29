from aiostreams import operators as op
from mosaicsmartdata.core.curve_utils import construct_OIS_curve, discounting_factor, curve_from_disc_factors
from mosaicsmartdata.core.date_calculator import DateCalculator
from mosaicsmartdata.core.instrument import FXSwap, FXForward, OIS, PricingContext
from mosaicsmartdata.core.instrument_static_singleton import InstrumentStaticSingleton
from mosaicsmartdata.core.quote import Quote


def implied_discounting_curve(spot_mid, outrights, usd_curve, spot_date, ccy):#, valuation_date = None):
    disc_factors = []
    for fwd_date, tmp in outrights.items():
        fwd_mid, tenor = tmp
        if fwd_date is None or spot_date is None:
            raise ValueError('fwd date and spot date must be valid!')
        # get the USD discounting factors;
        # as we only care about yield differential for pricing,
        # the one_pre_spot flag makes sure we return 1.0 as pre-spot USD disc factor
        usd_df = discounting_factor(usd_curve, spot_date, fwd_date, one_pre_spot= True)
        implied_df = usd_df * spot_mid/ fwd_mid# d2 = d1*S/F
        disc_factors.append((spot_date, fwd_date, implied_df, tenor))

    disc_factors.sort(key=lambda x: x[1])
    # TODO: where do we get daycount conventions etc?
    curve = curve_from_disc_factors(disc_factors, ccy=ccy)
    return curve


class FXPricingContextGenerator:
    def __init__(self):
        self.spot_rate = {}# dict of spot rates with ccy1=USD, key is ccy2
        self.spot_date = {}
        self.spot_original_quote = {}
        self.outright_rate= {} # dict of dicts of forward points, fist dict by ccy2 as with spot,
        # containing a dict of outright mids by settle_date
        self.usd_ois = []#  list of tuples (start date, end date, rate, tenor string)
        self.curves = {}
        self.date_calculator = DateCalculator()
        self.static = InstrumentStaticSingleton()
        self.today = None
        self.quotes_pending_spot = {}
        self.quotes_on_pending_tn = {}
        self.quotes_tn_latest = {}

    def __call__(self, quote: Quote):
        today = quote.timestamp.date()
        if today != self.today: # purge all caches
            # TODO: factor out this init
            self.spot_rate = {}
            self.spot_date = {}
            self.outright_rate = {}
            self.usd_ois = []
            self.curves = {}
            self.today = today
            self.quotes_pending_spot = {}

        # insert the latest quote into the correct storage
        quote_is_fx_spot = False
        if isinstance(quote.instrument, OIS):
            self.usd_ois.append((quote.instrument.spot_settle_date, quote.instrument.maturity_date, quote.mid, quote.instrument.tenor))

        elif isinstance(quote.instrument, FXForward) or isinstance(quote.instrument, FXSwap):
            if quote.instrument.ccy[0] == 'USD':
                non_usd_ccy = quote.instrument.ccy[1]
                invert = False
            elif quote.instrument.ccy[1] == 'USD':
                non_usd_ccy = quote.instrument.ccy[0]
                invert = True
            else:
                # ignore crosses
                pass

            if non_usd_ccy not in self.spot_rate:
                self.spot_rate[non_usd_ccy] = None
                self.quotes_pending_spot[non_usd_ccy] = [] # can be multiple tenors
                self.quotes_on_pending_tn[non_usd_ccy]=None # at most one per currency
                self.quotes_tn_latest[non_usd_ccy]= None
                self.spot_date[non_usd_ccy] = self.date_calculator.spot_date('fx', ('USD',non_usd_ccy), today)
            if non_usd_ccy not in self.outright_rate:
                self.outright_rate[non_usd_ccy] = {}

            # calculate normalized mid
            if isinstance(quote.instrument, FXForward): # forward or spot
                used_mid = quote.mid
                if invert:
                    used_mid = 1 / used_mid

                if quote.instrument.is_spot(today):
                    quote_is_fx_spot = True
                    self.spot_rate[non_usd_ccy] = used_mid
                    for q in self.quotes_pending_spot[non_usd_ccy]:
                        self.__call__(q)
                    self.quotes_pending_spot[non_usd_ccy] = []
                else: # an outright
                    self.outright_rate[non_usd_ccy][quote.instrument.settle_date] = used_mid
            elif isinstance(quote.instrument, FXSwap): # FXSwap
                if self.spot_rate[non_usd_ccy] is None: # need spot rates to convert!
                    self.quotes_pending_spot[non_usd_ccy].append(quote)
                    return []
                # convert from fx swap quote in pips to implied outright for USDXXX
                # determine whether the quote is post- or pre-spot
                if quote.instrument.legs[0].is_spot(today):
                    direction = 1
                    outright_date = quote.instrument.maturity_date
                    quote_mid = quote.mid
                    tenor = quote.instrument.tenor
                elif quote.instrument.legs[1].is_spot(today): #TN
                    #return []
                    direction = -1
                    outright_date = quote.instrument.settle_date
                    self.quotes_tn_latest[non_usd_ccy] = quote
                    quote_mid = quote.mid
                    tenor = quote.instrument.tenor
                    if self.quotes_on_pending_tn[non_usd_ccy] is not None:
                        self.__call__(self.quotes_on_pending_tn[non_usd_ccy])
                        self.quotes_on_pending_tn[non_usd_ccy] = None

                elif quote.instrument.tenor == 'ON':
                    tn_quote = self.quotes_tn_latest[non_usd_ccy]
                    if tn_quote is None:
                        self.quotes_on_pending_tn[non_usd_ccy] = quote
                        return []
                    else:
                        # construct a synthetic price from O to spot
                        quote_mid = quote.mid + tn_quote.mid
                        outright_date = quote.instrument.settle_date
                        direction = -1
                        tenor = 'ONTN'
                else:
                    raise ValueError('Can only handle ON, TN and post-spot tenors!')


                my_spot = self.spot_rate[non_usd_ccy]
                pip_size = self.static.pip_size(quote.instrument.ccy)
                if invert:
                    used_mid = 1/(1/my_spot + direction*quote_mid*pip_size)
                else:
                    used_mid = my_spot + direction*quote_mid*pip_size

                if outright_date is None:
                    raise ValueError("Outright date is None!")
                if used_mid is None or used_mid==float('nan'):
                    raise ValueError("Invalid used_mid!")

                self.outright_rate[non_usd_ccy][outright_date] = (used_mid, tenor)
        else:
            raise ValueError(quote, ' has an instrument type I can''t handle:', quote.instrument)

        # re-generate the discounting curve bundle
        # only update disc curves when fwpt or OIS tick, NOT when spot ticks!
        #print(self.spot_rate, self.outright_rate, self.usd_ois)
        curves_updated = False
        if True:
        # if not quote_is_fx_spot \
        #         or 'USD' not in self.curves \
        #         or not self.curves['USD'] \
        #         or not self.curves[non_usd_ccy]:
            if len(self.usd_ois)>=2: # want at least 2 points for OIS curve
                self.usd_ois.sort(key = lambda x: x[1]) # only get post-spot quotes here, so can sort by end date
                self.curves['USD'] = construct_OIS_curve(self.usd_ois, ccy = 'USD')
                curves_updated = True # at least one curve was re-generated
                for ccy in self.spot_rate:
                    if ccy in self.outright_rate and len(self.outright_rate[ccy])>=2:
                        tmp = implied_discounting_curve(self.spot_rate[ccy],
                                                                self.outright_rate[ccy],
                                                                self.curves['USD'],
                                                                self.spot_date[ccy],
                                                                ccy = ccy)#,
                                                                #valuation_date=today)
                        self.curves[ccy] = tmp



        if curves_updated or (quote_is_fx_spot and 'USD' in self.curves):
            context = PricingContext(self.curves, self.spot_rate, quote.timestamp, extra = self.outright_rate)
            return [context]
        else:
            return []



if __name__ == '__main__':
    # placeholders to make sure the code compiles
    spot_quotes = []
    fpt_quotes = []
    usd_ois_quotes = []
    trades = []

    # build the graph
    # Assume quotes already contain explicit dates, not just tenors
    # (enforced at quote object creation time?)
    quotes = op.merge_sorted([spot_quotes, fpt_quotes, usd_ois_quotes]) | \
                 op.map(FXPricingContextGenerator())
    full_stream = op.merge_sorted(quotes, trades)


