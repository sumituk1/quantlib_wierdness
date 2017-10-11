# from sklearn.decomposition import PCA
from mosaicsmartdata.common.read_config import *
from mosaicsmartdata.common.constants import HolidayCities
from mosaicsmartdata.core.trade import Trade
from mosaicsmartdata.core.curve_utils import *
from mosaicsmartdata.core.quote import Quote as my_Quote
from pathlib import Path as pth
from mosaicsmartdata.common.quantlib.bond.fixed_bond import *


class FactorRisk:
    def __init__(self, *args):
        self.f1_risk = args[0]
        self.f2_risk = args[1]
        self.f3_risk = args[2]
        self.total_factor_risk = args[3]

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

        # def get_f1_risk(self, attr):
        #     return self.f1_risk


class PCARisk:
    def __init__(self):
        configurator = Configurator()
        # thisfiledir = os.path.dirname(os.path.abspath(inspect.stack()[0][1]))
        # get the factor loadings, tenor_list and annualisation factor
        self.percentileRank = 0.05  # percentile VaR
        self.root_location = mosaicsmartdata.__path__
        if len(self.root_location) > 1:
            self.root_location = [x for x in self.root_location if 'msq-domain' in x]
        # config_location = self.root_location[0] + '/configuration/'
        # self.eig_vec = np.genfromtxt(config_location +
        #                               configurator.get_data_given_section_and_key("Factor_loadings", "eig_vector"))
        # self.eig_val = np.genfromtxt(config_location +
        #                              configurator.get_data_given_section_and_key("Factor_loadings", "eig_value"))

        self.tenor_list = [int(x) for x in
                           configurator.get_data_given_section_and_key("Factor_loadings", "tenor_list").split(',')]
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
            self.trade_id = msg.trade_id  # store the trade_id
            self.eig_vec = np.genfromtxt(str(pth(self.root_location[0]).parents[1])
                                         + "\\resources\\PCA\\" + msg.instrument.ccy + "_eig_vec__" +
                                         (msg.trade_date - dt.timedelta(days=30)).strftime("%Y.%m") + ".csv")
            self.eig_val = np.genfromtxt(str(pth(self.root_location[0]).parents[1]) + "\\resources\\PCA\\" +
                                         msg.instrument.ccy + "_eig_value__" +
                                         (msg.trade_date - dt.timedelta(days=30)).strftime("%Y.%m") + ".csv")
            if msg.trade_id in self.basket.keys():
                self.basket[msg.trade_id].append(msg)
            else:
                self.basket[msg.trade_id] = [msg]

            if len(self.basket[msg.trade_id]) >= msg.package_size:
                # received all the legs of the package.

                # first sort the trades in the basket by maturity_date
                self.basket[self.trade_id] = sorted(self.basket[self.trade_id],
                                                    key=lambda x: x.instrument.maturity_date)

                # calculate the package level risk and stamp to the trade
                factor_risk = self.calc_risk()

                # update the factor_risk attribute for each of the trades in the package
                for val in self.basket[msg.trade_id]:
                    val.factor_risk = factor_risk
                return self.basket[msg.trade_id]
            else:
                return []
        elif isinstance(msg, my_Quote):
            return [msg]
        else:
            raise ValueError("Unknown message type passed into Risk calculator")

    '''Calculates either a PCA based risk based on Swap rates with duration gap > 1yr or calls rollover_risk
    where gap risk < 1yr. The rollover_risk calc uses a simple var model based on the fixing'''
    def calc_risk(self):
        i = 0
        ## Sumit: 9th Oct, 2017 - Check if this is a roll-over. PCA Risk only works for > 1y
        if len(self.basket[self.trade_id]) == 2 and \
                (np.abs(self.basket[self.trade_id][1].instrument.maturity_date -
                            self.basket[self.trade_id][0].instrument.maturity_date).days / 360 < 1):

            tenor_gap = np.abs(self.basket[self.trade_id][1].instrument.maturity_date -
                            self.basket[self.trade_id][0].instrument.maturity_date).days / 360
            swaps_factor_risk = self.calculate_roll_risk(tenor_gap=tenor_gap)
        else:
            swaps_factor_risk = self.calculate_factor_risk_usingPCA()
            # # build the DV01 matrix
            # for x in self.basket[self.trade_id]:
            #     # first fill the tenor. find the closest tenor in the swap curve used to extract factor loadings
            #     tenor = min(self.tenor_list, key=lambda y: abs(y - x.tenor))
            #
            #     # now fill the dv01
            #     if x.side == TradeSide.Bid:
            #         # buying the fix leg. Set the DV01 as -ve
            #         dv01_arr[self.tenor_list.index(tenor)] += -1 * x.delta
            #     else:
            #         dv01_arr[self.tenor_list.index(tenor)] += abs(x.delta)
            #
            # f1_risk = np.sqrt(self.mult * np.square(np.dot(self.eig_vec[:,0], dv01_arr)) * self.eig_val[0])
            # f2_risk = np.sqrt(self.mult * np.square(np.dot(self.eig_vec[:,1], dv01_arr)) * self.eig_val[1])
            # f3_risk = np.sqrt(self.mult * np.square(np.dot(self.eig_vec[:,2], dv01_arr)) * self.eig_val[2])
            # total_factor_risk = np.sqrt(self.mult * (np.square(np.dot(self.eig_vec[:,0], dv01_arr)) * self.eig_val[0] +
            #                                          np.square(np.dot(self.eig_vec[:,1], dv01_arr)) * self.eig_val[1] +
            #                                          np.square(np.dot(self.eig_vec[:,2], dv01_arr)) * self.eig_val[2]))
            # swaps_factor_risk = FactorRisk(f1_risk, f2_risk, f3_risk, total_factor_risk)
        return swaps_factor_risk

    ''' Calculates the Risk for Switches/Rolls where the duration gap < 1yr'''

    def calculate_roll_risk(self, tenor_gap):
        lst_fwd = []
        logging.info("Going to calculate rollover risk")
        swaps_factor_risk = None
        ccy = self.basket[self.trade_id][0].ccy
        libor_rates_df, ois_rates_df = \
            read_usd_libor_data(str(pth(self.root_location[0]).parents[1]) + "\\resources\\Data extractor.xlsx",
                                sheet=ccy + " Swaps")
        libor_column = libor_rates_df.columns.values
        ois_column = ois_rates_df.columns.values
        k = 0
        # convert dataframe to a list that QL can understand
        for libor_rate, ois_rate \
                in zip(libor_rates_df.values[:100],
                       ois_rates_df.values[:100]):
            logging.warning(
                "Bootsrapping " + ccy + " curve for date:" + dt.datetime.strftime(libor_rates_df.index[k], "%Y.%m.%d"))
            libor_rate_ql = convert_df_to_ql_list(libor_rates_df.index[k], libor_column, libor_rate)
            ois_rate_ql = convert_df_to_ql_list(libor_rates_df.index[k], ois_column, ois_rate)

            usd_ois = USDOIS(pydate_to_qldate(libor_rates_df.index[k]),
                             UnitedStates() if ccy == Currency.USD else TARGET(),
                             ccy)  # Pass in the Trade date- not the settle_date
            # create the OIS curve
            usd_ois.create_ois_swaps(ois_rate_ql)

            # bootstrap the curve
            usd_ois.bootstrap_usd_ois_3M_curve(usd_3M_swap_rates=libor_rate_ql,
                                               discountCurve=usd_ois.ois_curve_c,
                                               bootStrapMethod=BootStrapMethod.PiecewiseFlatForward)

            # todo: Now get the forward_rate on the IMM roll-over GAP in duration
            lst_fwd.append(get_rate(usd_ois, self.basket[self.trade_id][0].instrument.maturity_date,
                                    self.basket[self.trade_id][1].instrument.maturity_date))

            k += 1

        # Now we have all the forwards. Calculate the return and a 95% vanumber
        swaps_factor_risk = self.calc_swap_var(lst_fwd, tenor_gap)

        swaps_factor_risk = FactorRisk(0.0, swaps_factor_risk, 0.0, swaps_factor_risk)
        return swaps_factor_risk

    ''' Calculates a simple VaR of a basket of trades by taking the worst 1% daily movement
        and multiplying with the DV01 of the long leg'''

    def calc_swap_var(self, rates_list, tenor_gap):
        sign = 1 if self.basket[self.trade_id][1].side == TradeSide.Ask else -1
        df = pd.DataFrame(data=None, columns=["Rate", "Diff_bps"])
        df["Rate"] = rates_list
        if sign == 1:
            # long the libor leg
            df["Diff_bps"] = sorted(df["Rate"].diff(-1) * 100)
        else:
            # short the libor leg
            df["Diff_bps"] = sorted(df["Rate"].diff(-1) * 100, reverse=True)

        var = df["Diff_bps"][self.percentileRank * len(df)] * \
              self.basket[self.trade_id][-1].notional * 0.0001 * tenor_gap

        return np.abs(var)

    '''Calculate the PCA risk of a basket based on eigen_vec & eig_values
    NOTE: This works for swaps duration mismatch  > 1yr '''

    def calculate_factor_risk_usingPCA(self):
        dv01_arr = np.zeros(len(self.tenor_list))
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

        f1_risk = np.sqrt(self.mult * np.square(np.dot(self.eig_vec[:, 0], dv01_arr)) * self.eig_val[0])
        f2_risk = np.sqrt(self.mult * np.square(np.dot(self.eig_vec[:, 1], dv01_arr)) * self.eig_val[1])
        f3_risk = np.sqrt(self.mult * np.square(np.dot(self.eig_vec[:, 2], dv01_arr)) * self.eig_val[2])
        total_factor_risk = np.sqrt(self.mult * (np.square(np.dot(self.eig_vec[:, 0], dv01_arr)) * self.eig_val[0] +
                                                 np.square(np.dot(self.eig_vec[:, 1], dv01_arr)) * self.eig_val[1] +
                                                 np.square(np.dot(self.eig_vec[:, 2], dv01_arr)) * self.eig_val[2]))
        swaps_factor_risk = FactorRisk(f1_risk, f2_risk, f3_risk, total_factor_risk)
        return swaps_factor_risk
