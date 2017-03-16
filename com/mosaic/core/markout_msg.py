import numpy as np


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
        self.price_markout = np.nan
        self.yield_markout = np.nan

    @property
    def __str__(self):
        return 'trade:' + self.trade + \
               ' instr:' + str(self.sym) + \
               ' next_timestamp:' + str(self.next_timestamp) + \
               ' dt:' + str(self.dt) + \
               ' price_markout:' + str(self.price_markout) + \
               ' yield_markout:' + str(self.yield_markout)