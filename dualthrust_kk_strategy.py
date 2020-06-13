# _*_coding : UTF-8 _*_
#开发团队 ：yunya
#开发人员 ：Administrator
#开发时间 : 2020/6/13 15:44
#文件名称 ：dualthrust_dc_strategy.py
#开发工具 ： PyCharm


from vnpy.app.cta_strategy import (
    CtaTemplate,
    StopOrder,
    TickData,
    BarData,
    TradeData,
    OrderData,
    BarGenerator,
    ArrayManager,
)
import talib
from vnpy.trader.constant import Interval, Direction
from  vnpy.app.cta_strategy.new_strategy import NewBarGenerator
class DudlThrust_NewStrategy(CtaTemplate):
    """"""
    author = "yunyu"

    open_window = 5
    xminute_window = 15
    rolling_period = 70
    upper_open = 0.5
    lower_open = 0.6
    cci_window = 30
    keltner_window = 24
    keltner_dev = 1
    fixed_size = 1

    cci_value = 0
    exit_kk_up = 0
    exit_kk_down = 0
    dualthrust_up = 0
    dualthrust_down = 0

    ask = 0
    bid = 0

    parameters = [
                "open_window",
                "xminute_window",
                "rolling_period",
                "upper_open",
                "lower_open",
                "cci_window",
                "keltner_window",
                "keltner_dev",
                "fixed_size",
                ]

    variables = [
                "dualthrust_up",
                "dualthrust_down",
                "cci_value",
                "exit_kk_up",
                "exit_kk_down",
                ]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        self.bg = NewBarGenerator(on_bar=self.on_bar,window=self.xminute_window,on_window_bar=self.on_min_bar)
        self.am = ArrayManager()
        
        self.bg_open = BarGenerator(on_bar=self.on_bar,window=self.open_window,on_window_bar=self.on_open_bar,interval=Interval.MINUTE)
        self.am_open = ArrayManager()

    def on_init(self):
        """
        Callback when strategy is inited.
        """
        self.write_log("策略初始化")
        self.load_bar(10)

    def on_start(self):
        """
        Callback when strategy is started.
        """
        self.write_log("策略启动")

    def on_stop(self):
        """
        Callback when strategy is stopped.
        """
        self.write_log("策略停止")

    def on_tick(self, tick: TickData):
        """
        Callback of new tick data update.
        """
        self.bg.update_tick(tick)
        self.ask = tick.ask_price_1  # 卖一价
        self.bid = tick.bid_price_1  # 买一价



    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        self.bg_open.update_bar(bar)
        self.bg.update_bar(bar)

    def on_open_bar(self,bar:BarData):
        """
        开仓
        """
        self.am.update_bar(bar)

        self.cancel_all()

        if not self.am_open.inited and not self.am.inited:
            return

        if self.pos == 0:
            if self.cci_value > 0:
                self.buy(self.dualthrust_up,self.fixed_size,True)

            elif self.cci_value < 0:
                self.short(self.dualthrust_down,self.fixed_size,True)

        elif self.pos > 0:
            self.sell(self.exit_kk_down,self.fixed_size,True)

        elif self.pos < 0:
            self.cover(self.exit_kk_up,self.fixed_size,True)

        self.put_event()

    def on_min_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        self.am.update_bar(bar)

        if not self.am.inited:
            return

        self.dualthrust_up, self.dualthrust_down = self.dualthrust(
                                            self.am.high,
                                            self.am.low,
                                            self.am.close,
                                            self.am.open,
                                            self.rolling_period,
                                            self.upper_open,
                                            self.lower_open
                                            )
        self.cci_value = self.am.cci(self.cci_window)
        self.keltner_up, self.keltner_down = self.am.keltner(
            self.keltner_window, self.keltner_dev)

        self.sync_data()
        self.put_event()
    def on_order(self, order: OrderData):
        """
        Callback of new order data update.
        """
        pass

    def on_trade(self, trade: TradeData):
        """
        Callback of new trade data update.
        """
        self.put_event()

    def on_stop_order(self, stop_order: StopOrder):
        """
        Callback of stop order update.
        """
        pass
        # self.put_event()

    def market_order(self):
        """"""
        pass
        # self.buy(self.last_tick.limit_up, 1)
        # self.write_log("执行市价单测试")

    def limit_order(self):
        """"""
        pass
        # self.buy(self.last_tick.limit_down, 1)
        # self.write_log("执行限价单测试")

    def stop_order(self):
        """"""
        pass
        # self.buy(self.last_tick.ask_price_1, 1, True)
        # self.write_log("执行停止单测试")

    def dualthrust(self,high,low,close,open,n,k1,k2):
        """
        :param high:
        :param low:
        :param close:
        :return:
        """
        #计算N日最高价的最高价，收盘价的最高价、最低价，最低价的最低价
        hh = high[-n:-1].max()
        lc = close[-n:-1].min()
        hc = close[-n:-1].max()
        ll = low[-n:-1].min()

        #计算range,上下轨的距离前一根K线开盘价的距离
        range = max(hh - lc,hc - ll)

        up = open[-2] + k1 * range
        down = open[-2] - k2 * range

        return up,down










