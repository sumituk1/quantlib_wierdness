import numpy as np


class PnLCalculator:
    def __init__(self):
        self.quantity = 0
        self.cost = 0.0
        self.market_value = 0.0
        self.r_pnl = 0.0
        self.average_price = 0.0

    def fill(self, n_pos, exec_price):
        pos_change = n_pos - self.quantity
        direction = np.sign(pos_change)
        prev_direction = np.sign(self.quantity)
        qty_closing = min(abs(self.quantity), abs(pos_change)) * direction if prev_direction != direction else 0
        qty_opening = pos_change if prev_direction == direction else pos_change - qty_closing

        new_cost = self.cost + qty_opening * exec_price
        if self.quantity != 0:
            new_cost += qty_closing * self.cost / self.quantity
            self.r_pnl += qty_closing * (self.cost / self.quantity - exec_price)

        self.quantity = n_pos
        self.cost = new_cost

    def update(self, price):
        if self.quantity != 0:
            self.average_price = self.cost / self.quantity
        else:
            self.average_price = 0
        self.market_value = self.quantity * price
        return self.market_value - self.cost
