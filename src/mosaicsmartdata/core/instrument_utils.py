from mosaicsmartdata.core.date_calculator import DateCalculator
from mosaicsmartdata.core.instrument import FXForward, FXSwap, OIS

# TODO: have a nice currency list
ccys = {'EUR','USD','GBP','JPY', 'CAD'}

def ccy_to_major_pair(ccy):
    if ccy in ['EUR', 'GBP', 'AUD', 'NZD']:
        return (ccy, 'USD')
    else:
        return ('USD', ccy)

# only works for FX spot and forward symbols for now
def split_ric(sym):
    sym = sym.split('=')[0]
    ccy = str(sym[:3])
    if sym[-3:] == 'OIS': # OIS instrument
        instr_type = 'ois'
        pair = ccy
        tenor = str(sym[3:-3]) # tenor can have different length, '2M' or '11M'
    else: # assume it's an FX instrument
        instr_type ='fx'
        if len(sym) >= 6 and str(sym[3:6]) in ccys:
            pair = (ccy, str(sym[3:6]))
            tenor = str(sym[6:])
        else:
            pair = ccy_to_major_pair(ccy)
            tenor = str(sym[3:])

    return (instr_type, pair, tenor)


class sym_to_instrument:
    def __init__(self):
        self.instr_cache = {}

    def __call__(self, sym, today):
        if (sym, today) not in self.instr_cache:
            date_calc = DateCalculator()
            instr_type, pair, tenor = split_ric(sym)
            spot_date = date_calc.spot_date(instr_type, pair, today)
            if instr_type=='fx':
                spot_instr = FXForward(ccy = pair, settle_date = spot_date, sym = sym, tenor = 'SPOT')
                if not tenor:
                    self.instr_cache[(sym, today)] = spot_instr
                else: # it must be an FX Swap, so get the other leg
                    if tenor == 'ON':
                        o_date = date_calc.date_add(today,'0b') # next business day
                        o_instr = FXForward(ccy=pair,
                                            settle_date=o_date,
                                            sym=sym,
                                            tenor='O')
                        t_date = date_calc.date_add(today,'1b')
                        t_instr = FXForward(ccy=pair,
                                            settle_date=t_date,
                                            sym=sym,
                                            tenor='T')
                        legs = [o_instr, t_instr]
                    elif tenor == 'TN':
                        t_date = date_calc.date_add(today,'1b')
                        t_instr = FXForward(ccy=pair,
                                            settle_date=t_date,
                                            sym=sym,
                                            tenor='T')
                        legs = [t_instr, spot_instr]
                    else:
                        if tenor == 'SN':
                            tenor = '1b'
                        if tenor == 'SW':
                            tenor = '1w'
                        other_date = date_calc.date_add(spot_date, tenor)
                        outright_tenor = tenor

                        other_instr = FXForward(ccy = pair,
                                                settle_date = other_date,
                                                sym = sym,
                                                tenor = outright_tenor)
                        legs = [spot_instr, other_instr]

                    self.instr_cache[(sym, today)] = FXSwap(legs, tenor=tenor, sym=sym, ccy=pair)
            elif instr_type=='ois':
                # only get SW or later here
                if tenor == 'SW':
                    end_date = date_calc.date_add(spot_date, '1w')
                else:
                    end_date = date_calc.date_add(spot_date, tenor)

                my_instr = OIS(ccy=pair, spot_settle_date=spot_date, maturity_date=end_date, sym=sym)

                self.instr_cache[(sym, today)] = my_instr


        return self.instr_cache[(sym, today)]


if __name__ == "__main__":
    from mosaicsmartdata.common import qc_csv_helper
    filename = '../../../resources/fx/EUR_JPY_GBP_till_SN.csv'
    quote_dict = qc_csv_helper.get_fx_quotes(filename)
