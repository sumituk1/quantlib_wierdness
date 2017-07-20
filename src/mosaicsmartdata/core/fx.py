from collections import namedtuple

from aiostreams import operators as op
from mosaicsmartdata.core.instrument import FXForward, FixedIncomeIRSwap, PricingContext
from mosaicsmartdata.core.quote import Quote
from mosaicsmartdata.core.date_calculator import DateCalculator

#TODO: curve calibration facade

#BasicQuote = namedtuple('BasicQuote', 'instr mid timestamp')

def construct_OIS_curve(usd_ois_quotes):
    '''

    :param usd_ois_quotes: a dict where the key is the tuple (start date, end date) and the value is the quote
    :return: a curve object
    '''
    # TODO: implement
    pass


def implied_discounting_curve(spot, fwpts, usd_curve, valuation_date):
    disc_factors = []
    for (spot_date, fwd_date), fpt in fwpts.items:
        ccy = fpt.ccy2
        usd_df = discounting_factor(usd_curve, spot_date, fwd_date)
        df_ratio = (spot.mid + fpt.mid) / spot.mid
        implied_df = df_ratio * usd_df  # TODO: or divide? write this out
        disc_factors.append((implied_df, spot_date, fwd_date))

    # TODO: where do we get daycount conventions etc?
    curve = curve_from_disc_factors(disc_factors, ccy=ccy)


def discounting_factor(curve, start_date, end_date):
    '''
    Returns the discounting factor from the second date onto the first
    :param curve:
    :param start_date:
    :param end_date:
    :return: discounting factor
    '''
    pass


def curve_from_disc_factors(disc_factors, **kwargs):
    '''
    Constructs a discounting curve from an array of factors and their
    respective start and end dates
    :param disc_factors:
    :param start_dates:
    :param end_dates:
    :param kwargs: Extra stuff like daycount conventions etc
    :return:
    '''
    pass


class FXPricingContextGenerator:
    def __init__(self):
        self.spot_rate = {}# dict of spot rates with ccy1=USD, key is ccy2
        self.spot_original_quote = {}
        self.fwpt = {} # dict of dicts of forward points, fist dict by ccy2 as with spot, containing a dict by tenor
        self.usd_ois = {} # dict of rates by tenor
        self.date_calculator = DateCalculator()

    def __call__(self, quote: Quote):
        # insert the latest quote into the correct storage
        if isinstance(quote.instrument, FixedIncomeIRSwap):
            self.usd_ois[(quote.instr.start_date, quote.instr.end_date)] = quote.mid

        elif isinstance(quote.instrument, FXForward):
            if quote.instrument.ccy[0] == 'USD':
                non_usd_ccy = quote.instrument.ccy[1]
                invert = False
            elif quote.instrument.ccy[1] == 'USD':
                non_usd_ccy = quote.instrument.ccy[0]
                invert = True
            else:
                # ignore crosses
                pass

            # calculate normalized mid
            if quote.units == 'outright':
                used_mid = quote.mid
            elif quote.units == 'pips':
                # TODO: handle forward quotes in pips relative to spot
                if non_usd_ccy not in self.spot_rate:
                    self.spot_rate[non_usd_ccy] = float('NaN')
                used_mid = float('NaN')
            else:
                raise ValueError('quote.units must be outright or pips!')

            if invert:
                used_mid = 1/used_mid

            today = quote.timestamp.date()
            if quote.instrument.is_spot(today):
                self.spot_rate[non_usd_ccy] = used_mid
            else:
                if non_usd_ccy not in self.fwpt:
                    self.fwpt[non_usd_ccy] = {}
                self.fwpt[non_usd_ccy][(quote.instr.spot_date(today), quote.instr.settle_date)] = used_mid
        else:
            raise ValueError(quote, ' has an instrument type I can''t handle:', quote.instrument)

        # re-generate the discounting curve bundle
        # TODO: only update disc curves when fwpt or OIS tick, NOT when spot ticks!
        curves={}
        curves['USD'] = construct_OIS_curve(self.usd_ois)
        for ccy in self.spot_rate:
            if ccy in self.fwpt:
                this_spot = self.spot_rate[ccy]
                this_fwpts = self.fwpt[ccy]
                curves[ccy] = implied_discounting_curve(this_spot, this_fwpts, curves['USD'],today)

        return PricingContext(curves, self.spot_rate, quote.timestamp)


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


