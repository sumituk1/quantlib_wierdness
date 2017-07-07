from mosaicsmartdata.core.date_calculator import DateCalculator
from mosaicsmartdata.core.instrument import FXForward, FXSwap

def split_ric(sym):
    ccy = str(sym[:3])
    tenor = str(sym[3:-1])
    return (ccy, tenor)


def ccy_to_major_pair(ccy):
    if ccy in ['EUR', 'GBP', 'AUD', 'NZD']:
        return (ccy, 'USD')
    else:
        return ('USD', ccy)

class sym_to_fx_instrument:
    def __init__(self):
        self.instr_cache = {}

    def __call__(self, sym, today):
        if (sym, today) not in self.instr_cache:
            date_calc = DateCalculator()
            ccy, tenor = split_ric(sym)
            pair = ccy_to_major_pair(ccy)
            spot_date = date_calc.spot_date(pair, today)
            spot_instr = FXForward(ccy = pair, settle_date = spot_date, sym = sym, tenor = 'SPOT')
            if not tenor:
                self.instr_cache[(sym, today)] = spot_instr
            else: # it must be an FX Swap, so get the other leg
                if tenor == 'ON':
                    other_date = date_calc.date_add(today,'0b') # next business day
                    outright_tenor = 'O'
                elif tenor == 'TN':
                    other_date = date_calc.date_add(today,'1b')
                    outright_tenor = 'T'
                else:
                    other_date = date_calc.date_add(spot_date, tenor)
                    outright_tenor = tenor

                other_instr = FXForward(ccy = pair, settle_date = other_date, sym = sym, tenor = outright_tenor)
                if tenor in ['ON','TN']:
                    legs = [other_instr, spot_instr]
                else:
                    legs = [spot_instr, other_instr]

                self.instr_cache[(sym, today)] = FXSwap(legs, tenor=tenor)

        return self.instr_cache[(sym, today)]


if __name__ == "__main__":
    from mosaicsmartdata.common import qc_csv_helper
    filename = '../../../resources/fx/EUR_JPY_GBP_till_SN.csv'
    quote_dict = qc_csv_helper.get_fx_quotes(filename)
