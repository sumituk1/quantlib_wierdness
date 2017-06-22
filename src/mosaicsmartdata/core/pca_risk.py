#from sklearn.decomposition import PCA
import numpy as np
from mosaicsmartdata.common.constants import *
from mosaicsmartdata.common.read_config import *
from mosaicsmartdata.core.trade import Trade
from mosaicsmartdata.core.quote import Quote


class SwapsFactorRisk:
    def __init__(self, *args):
        self.f1_risk = args[0]
        self.f2_risk = args[1]
        self.f3_risk = args[2]
        self.total_factor_risk = args[3]

    # def get_f1_risk(self, attr):
    #     return self.f1_risk


class PCARisk:
    def __init__(self):
        configurator = Configurator()
        # thisfiledir = os.path.dirname(os.path.abspath(inspect.stack()[0][1]))
        # get the factor loadings, tenor_list and annualisation factor
        self.eig_vec = np.genfromtxt('../resources/' +
                                      configurator.get_data_given_section_and_key("Factor_loadings", "eig_vector"))
        self.eig_val = np.genfromtxt('../resources/' +
                                     configurator.get_data_given_section_and_key("Factor_loadings", "eig_value"))

        self.tenor_list = [int(x) for x in configurator.get_data_given_section_and_key("Factor_loadings", "tenor_list").split(',')]
        self.mult = float(configurator.get_data_given_section_and_key("Factor_loadings", "annual_mult"))

        # self.eig_vec = np.array([[0.0638554, 0.21389878, -0.38284765],
        #                          [0.13077123, 0.33385239, -0.44283622],
        #                          [0.18226383, 0.38486285, -0.28635806],
        #                          [0.21228725, 0.33841131, -0.10379211],
        #                          [0.2297719, 0.30690827, 0.04482106],
        #                          [0.23835453, 0.21965848, 0.16979336],
        #                          [0.24508527, 0.14256822, 0.16518113],
        #                          [0.24608177, 0.09897627, 0.19715396],
        #                          [0.24585935, 0.05433519, 0.24679926],
        #                          [0.24718362, 0.0029286, 0.17964089],
        #                          [0.24100974, -0.02196934, 0.27817342],
        #                          [0.2430982, -0.0547422, 0.11142535],
        #                          [0.23703055, -0.07507827, 0.1086539],
        #                          [0.2347622, -0.07919441, 0.1471804],
        #                          [0.23785058, -0.12666093, -0.01512619],
        #                          [0.23450143, -0.20464126, -0.07548291],
        #                          [0.23014111, -0.26985136, -0.22450526],
        #                          [0.22879609, -0.27189335, -0.16918891],
        #                          [0.22771846, -0.30159046, -0.28069669],
        #                          [0.22703854, -0.30595978, -0.29558024]])

        # self.eig_val = np.array([7.00E-03, 3.09E-04, 2.81E-05])
        self.basket = dict()
        self.trade_id = None

    def __call__(self, msg):
        if isinstance(msg, Trade):
            self.trade_id = msg.trade_id # store the trade_id
            if msg.trade_id in self.basket.keys():
                self.basket[msg.trade_id].append(msg)
            else:
                self.basket[msg.trade_id] = [msg]

            if len(self.basket[msg.trade_id]) >= msg.package_size:
                # received all the legs of the package.
                # calculate the package level risk and stamp to the trade
                factor_risk = self.calc_risk()
                # update the factor_risk attribute for each of the trades in the package
                for val in self.basket[msg.trade_id]:
                    val.factor_risk = factor_risk
                return self.basket[msg.trade_id]
            else:
                return []
        elif isinstance(msg, Quote):
            return [msg]
        else:
            raise ValueError("Unknown message type passed into Risk calculator")

    def calc_risk(self):
        dv01_arr = np.zeros(len(self.tenor_list))
        i = 0
        # build the DV01 matrix
        for x in self.basket[self.trade_id]:
            # first fill the tenor. find the closest tenor in the swap curve used to extract factor loadings
            tenor = min(self.tenor_list, key=lambda y: abs(y - x.tenor))

            # now fill the dv01
            if x.side == TradeSide.Bid:
                # buying the fix leg. Set the DV01 as -ve
                dv01_arr[self.tenor_list.index(tenor)] += -1 * x.delta
            else:
                dv01_arr[self.tenor_list.index(tenor)] += abs(x.delta)

        f1_risk = np.sqrt(self.mult * np.square(np.dot(self.eig_vec[:,0], dv01_arr)) * self.eig_val[0])
        f2_risk = np.sqrt(self.mult * np.square(np.dot(self.eig_vec[:,1], dv01_arr)) * self.eig_val[1])
        f3_risk = np.sqrt(self.mult * np.square(np.dot(self.eig_vec[:,2], dv01_arr)) * self.eig_val[2])
        total_factor_risk = np.sqrt(self.mult * (np.square(np.dot(self.eig_vec[:,0], dv01_arr)) * self.eig_val[0] +
                                                 np.square(np.dot(self.eig_vec[:,1], dv01_arr)) * self.eig_val[1] +
                                                 np.square(np.dot(self.eig_vec[:,2], dv01_arr)) * self.eig_val[2]))
        swaps_factor_risk = SwapsFactorRisk(f1_risk, f2_risk, f3_risk, total_factor_risk)
        return swaps_factor_risk
