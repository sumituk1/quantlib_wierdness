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
