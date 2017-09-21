from aiostreams import operators as op
from mosaicsmartdata.core.curve_utils import construct_OIS_curve, discounting_factor, curve_from_disc_factors
from mosaicsmartdata.core.date_calculator import DateCalculator
from mosaicsmartdata.core.instrument import FXSwap, FXForward, OIS, PricingContext
from mosaicsmartdata.core.instrument_static_singleton import InstrumentStaticSingleton
from mosaicsmartdata.core.quote import Quote


def implied_discounting_curve(spot_mid, outrights, usd_curve, spot_date, ccy):#, valuation_date = None):
    disc_factors = []
    for fwd_date, fwd_mid in outrights.items():
        if fwd_date is None or spot_date is None:
            pass
        # get the USD discounting factors;
        # as we only care about yield differential for pricing,
        # the one_pre_spot flag makes sure we return 1.0 as pre-spot USD disc factor
        usd_df = discounting_factor(usd_curve, spot_date, fwd_date, one_pre_spot= True)
        df_ratio = fwd_mid / spot_mid
        implied_df = df_ratio * usd_df  # TODO: or divide? write this out
        disc_factors.append((implied_df, spot_date, fwd_date))

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
        self.usd_ois = {} # dict of rates by tenor
        self.curves = {}
        self.date_calculator = DateCalculator()
        self.static = InstrumentStaticSingleton()
        self.today = None

    def __call__(self, quote: Quote):
        today = quote.timestamp.date()
        if today != self.today: # purge all caches
            self.spot_rate = {}
            self.spot_date = {}
            self.outright_rate = {}
            self.usd_ois = {}
            self.curves = {}
            self.today = today


        # insert the latest quote into the correct storage
        if isinstance(quote.instrument, OIS):
            self.usd_ois[(quote.instrument.spot_settle_date, quote.instrument.maturity_date)] = quote.mid

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
                self.spot_rate[non_usd_ccy] = float('NaN')
                self.spot_date[non_usd_ccy] = self.date_calculator.spot_date('fx', ('USD',non_usd_ccy), today)
            if non_usd_ccy not in self.outright_rate:
                self.outright_rate[non_usd_ccy] = {}

            # calculate normalized mid
            if isinstance(quote.instrument, FXForward): # forwards or spot
                used_mid = quote.mid
                if invert:
                    used_mid = 1 / used_mid

                if quote.instrument.is_spot(today):
                    self.spot_rate[non_usd_ccy] = used_mid
                else: # an outright
                    self.outright_rate[non_usd_ccy][quote.instrument.settle_date] = used_mid
            elif isinstance(quote.instrument, FXSwap): # FXSwap
                # convert from fx swap quote in pips to implied outright for USDXXX
                # determine whether the quote is post- or pre-spot
                if quote.instrument.legs[0].is_spot(today):
                    direction = 1
                    outright_date = quote.instrument.maturity_date
                elif quote.instrument.legs[1].is_spot(today): # pre-spot
                    direction = -1
                    outright_date = quote.instrument.settle_date
                elif quote.instrument.tenor == 'ON':
                    # TODO: calculate fair rates to today from ON, TN and spot
                    return []
                else:
                    raise ValueError('One of the FXSwap legs must be spot!')

                my_spot = self.spot_rate[non_usd_ccy]
                pip_size = self.static.pip_size(quote.instrument.ccy)
                if invert:
                    used_mid = 1/(1/my_spot + direction*quote.mid*pip_size)
                else:
                    used_mid = my_spot + direction*quote.mid*pip_size

                if outright_date is None:
                    pass
                self.outright_rate[non_usd_ccy][outright_date] = used_mid
        else:
            raise ValueError(quote, ' has an instrument type I can''t handle:', quote.instrument)

        # re-generate the discounting curve bundle
        # TODO: only update disc curves when fwpt or OIS tick, NOT when spot ticks!
        curves={}
        #print(self.spot_rate, self.outright_rate, self.usd_ois)
        if len(self.usd_ois)>=2: # want at least 2 points for OIS curve
            self.curves['USD'] = construct_OIS_curve(self.usd_ois)
            for ccy in self.spot_rate:
                if ccy in self.outright_rate and len(self.outright_rate[ccy])>=2:
                    tmp = implied_discounting_curve(self.spot_rate[ccy],
                                                            self.outright_rate[ccy],
                                                            self.curves['USD'],
                                                            self.spot_date[ccy],
                                                            ccy = ccy)#,
                                                            #valuation_date=today)
                    self.curves[ccy] = tmp

            context = PricingContext(self.curves, self.spot_rate, quote.timestamp)
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


