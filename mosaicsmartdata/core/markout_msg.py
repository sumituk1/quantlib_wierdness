import numpy as np
from mosaicsmartdata.core.trade import GenericParent


class MarkoutMessage2(GenericParent):
    '''
    A basic markout calculator
    After each price update, returns a list of the markouts completed so far,
    so should be followed by a flattener
    It assumes all messages arrrive in strict timestamp order
    '''

    def __init__(self, *args, **kwargs):
        # properties of trade itself
        self.trade = None
        self.next_timestamp = None
        self.initial_price = None
        self.final_price = None
        self.dt = None
        # self.bps_markout = None
        # $self.cents_markout = None
        self.price_markout = None

        super().__init__(**(self.apply_kwargs(self.__dict__, kwargs)))

    def __getattr__(self, item):
        if item in self.__dict__:
            return self.__dict__[item]
        # calculate different markout types on the fly by applying the correct multiplier
        elif item in self.trade.__dict__:
            return self.trade.__dict__[item]
        elif str(item)[-8:] == '_markout':
            mk_type = str(item)[:-8]
            mults = self.trade.markout_mults()
            if mk_type in mults:
                return self.price_markout * mults[mk_type] if not self.price_markout is None else "NaN"
        else:
            raise ValueError('This object doesn\'t understand ' + item)

    def __str__(self):
        out = ""
        attribs = [a for a in dir(self) if not a.startswith('__') and not callable(getattr(self, a))]

        for item in attribs:
            if item == 'trade':
                out += ' package_id:' + self.trade.package_id
                out += ' trade_id:' + self.trade.trade_id
                out += ' sym:' + self.trade.sym
                out += ' timestamp:' + self.trade.timestamp.strftime("%d/%m/%Y %H:%M:%S")
                out += ' delta:' + str(self.trade.delta)
                out += ' paper_trade:' + str(self.trade.paper_trade)
                out += ' client_sys_key:' + self.trade.client_sys_key
                out += ' notional:' + str(self.trade.notional)
                if self.trade.trade_settle_date is not None:
                    out += ' trade_settle_date:' + self.trade.trade_settle_date.strftime("%d/%m/%Y")
                if self.trade.maturity_date is not None:
                    out += ' trade_maturity_date:' + self.trade.maturity_date.strftime("%d/%m/%Y")
                # if self.trade.maturity_date is not None:
                #     out += ' trade_settle_date:' + self.trade.trade_settle_date.strftime("%d/%m/%Y %H:%M")
                # else:
                #     out += ' trade_settle_date:'
                # if self.trade.maturity_date is not None:
                #     out += ' trade_settle_date:' + self.trade.maturity_date.strftime("%d/%m/%Y %H:%M")
                # else:
                #     out += ' trade_settle_date:'
                out += ' side:' + self.trade.side
                out += ' traded_px:' + str(self.trade.traded_px)
                out += ' ccy:' + self.trade.ccy
            elif 'markout' not in item:
                out += " " + item + ":" + str(self.__dict__[item])
            else:
                mk_type = str(item)[:-8]
                mults = self.trade.markout_mults()
                if mk_type in mults:
                    for key, value in mults.items():
                        out += " " + key + ":" + str(self.price_markout * value
                                                     if not self.price_markout is None else "NaN")

        return out
        # return self.price_markout * mults[mk_type]

        # return 'trade_id:' + self.trade_id + \
        #        ' instr:' + self.sym + \
        #        ' next_timestamp:' + self.next_timestamp.strftime("%d/%m/%Y %H:%M") + \
        #        ' dt:' + str(self.dt) + \
        #        ' cents_markout:' + str(self.cents_markout) + \
        #        ' bps_markout:' + str(self.bps_markout)


if False:
    class MarkoutMessage:
        '''
        A basic markout calculator
        After each price update, returns a list of the markouts completed so far,
        so should be followed by a flattener
        It assumes all messages arrrive in strict timestamp order
        '''

        def __init__(self, trade,
                     trade_id,
                     notional,
                     sym,
                     side,
                     initial_price,
                     next_timestamp,
                     dt):
            # properties of trade itself
            self.trade = trade
            self.trade_id = trade_id
            self.side = side
            self.notional = notional
            self.sym = sym
            self.next_timestamp = next_timestamp
            self.initial_price = initial_price
            self.final_price = np.nan
            self.dt = dt
            self.bps_markout = np.nan
            self.cents_markout = np.nan

        #    @property
        def __str__(self):
            return 'trade_id:' + self.trade_id + \
                   ' instr:' + self.sym + \
                   ' next_timestamp:' + self.next_timestamp.strftime("%d/%m/%Y %H:%M") + \
                   ' dt:' + str(self.dt) + \
                   ' cents_markout:' + str(self.cents_markout) + \
                   ' bps_markout:' + str(self.bps_markout)
