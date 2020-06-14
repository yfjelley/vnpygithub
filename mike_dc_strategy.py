# _*_coding : UTF-8 _*_
#开发团队 ：yunya
#开发人员 ：Administrator
#开发时间 : 2020/6/14 8:34
#文件名称 ：mike_dc_strategy.py
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

from vnpy.trader.constant import Direction ,Interval,Exchange


class Mike_Dc_Strategy(CtaTemplate):
    """"""

    author = "yunya"

    exchange : Exchange = ""
    mike_window = 1
    mike_length = 30
    dc_length = 10
    kk_length = 20
    kk_dev = 2.0
    sl_trade = 2
    fixed_size = 1

    ask = 0
    bid = 0

    ema_mid = 0
    ema_hh = 0
    ema_ll = 0

    ema_wr = 0  #初级压力线
    ema_mr = 0  #中级压力线
    ema_sr = 0  #高级压力线

    ema_ws = 0  #初级支撑线
    ema_ms = 0  #中级支撑线
    ema_ss = 0  #高级支撑线

    dc_up = 0
    dc_down = 0
    kk_up = 0
    kk_down = 0

    atr_value = 0
    long_stop = 0
    short_stop = 0
    long_stop_trade = 0
    short_stop_trade = 0
    long_enrty = 0
    short_enrty = 0
    ema_entry_crossover = 0
    boll_entry_crossover = 0
    boll_width = 0


    parameters = [
                    "exchange",
                    "open_window",
                    "xminute_window",
                    "mike_window",
                    "mike_length",
                    "dc_length",
                    "kk_length",
                    "kk_dev",
                    "sl_trade",
                    "fixed_size",
                    ]

    variables = [
                    "long_stop",
                    "short_stop",
                    "ema_entry_crossover",
                    "boll_entry_crossover",
                    "boll_width",
                    "ema_mid",
                    "ema_hh",
                    "ema_ll",
                    "ema_wr",
                    "ema_mr",
                    "ema_sr",
                    "ema_ws",
                    "ema_ms",
                    "ema_ss",
                    ]

    def __init__(self, cta_engine, strategy_nam_xhoure, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_nam_xhoure, vt_symbol, setting)

        self.bg_xhour = BarGenerator(
                                on_bar=self.on_bar,
                                window=self.mike_window,
                                on_window_bar=self.on_hour_bar,
                                interval=Interval.HOUR
                            )
        self.am_xhour = ArrayManager(max(self.dc_length ,self.kk_length) + 10)

    def on_init(self):
        """
        Callback when strategy is inited.
        """
        self.write_log("策略初始化")
        self.exchange_load_bar(self.exchange)

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
        self.bg_xhour.update_tick(tick)
        self.ask = tick.ask_price_1  # 卖一价
        self.bid = tick.bid_price_1  # 买一价

    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        self.bg_xhour.update_bar(bar)

    def on_hour_bar(self, bar: BarData):
        """
        计算 mike 指标线
        :param_xhour bar:
        :return:
        """

        self.am_xhour.update_bar(bar)
        if not self.am_xhour.inited:
            return

        # 计算mike压力支撑线
        ema_array = (self.am_xhour.close[:-1] + self.am_xhour.high[:-1] + self.am_xhour.low[:-1]) / 3
        self.ema_mid = ema_array[-1]
        self.ema_hh = self.am_xhour.high[-self.mike_length:-1].max()
        self.ema_ll = self.am_xhour.low[-self.mike_length:-1].min()

        self.ema_wr = self.ema_mid + (self.ema_mid - self.ema_ll)
        self.ema_mr = self.ema_mid + (self.ema_hh - self.ema_ll)
        self.ema_sr = 2 * self.ema_hh - self.ema_ll

        self.ema_ws = self.ema_mid - (self.ema_hh - self.ema_mid)
        self.ema_ms = self.ema_mid - (self.ema_hh - self.ema_ll)
        self.ema_ss = 2 * self.ema_ll - self.ema_hh

        if (self.am_xhour.close[-1] > self.ema_sr) or (self.ema_ms < self.am_xhour.close[-1] < self.ema_ws):
            self.ema_entry_crossover = 1

        elif (self.am_xhour.close[-1] < self.ema_ss) or (self.ema_mr > self.am_xhour.close[-1] > self.ema_wr):
            self.ema_entry_crossover = -1

        self.kk_up,self.kk_down = self.am_xhour.keltner(self.kk_length,self.kk_dev)

        self.dc_up,self.dc_down = self.am_xhour.donchian(self.dc_length)

        if self.pos == 0:
            self.atr_value = self.am_xhour.atr(30)

            if self.ema_entry_crossover > 0 :
                self.buy(self.kk_up, self.fixed_size,True)
                print(self.kk_up)

            elif self.ema_entry_crossover < 0 :
                self.short(self.kk_down, self.fixed_size,True)

        elif self.pos > 0:

            self.long_stop = max(self.dc_down,self.long_stop_trade)
            self.sell(self.long_stop, abs(self.pos), True)

        elif self.pos < 0:

            self.short_stop = min(self.dc_up,self.short_stop_trade)
            self.cover(self.short_stop, abs(self.pos), True)

        self.sync_data()
        self.put_event()

    def on_order(self, order: OrderData):
        """
        Callback of new order data update.
        """
        pass

        # self.write_log(f"on_order: status:{order.status}, orderid: {order.vt_orderid}, offset:{order.offset}, price:{order.price}, volume:{order.volume}, traded: {order.traded}")
        # self.put_event()

    def on_trade(self, trade: TradeData):
        """
        Callback of new trade data update.
        """
        # if trade.direction == Direction.LONG:
        #     self.long_enrty = trade.price
        #     self.long_stop_trade = self.long_enrty - 2 * self.atr_value
        #
        # else:
        #     self.short_enrty = trade.price
        #     self.short_stop_trade = self.short_enrty + 2 * self.atr_value

        self.put_event()

    def on_stop_order(self, stop_order: StopOrder):
        """
        Callback of stop order update.
        """
        pass

    def exchange_load_bar(self,exchange:Exchange):
        """
        如果是火币，ok 交易所，就从数据库获取初始化数据
        """
        if exchange == Exchange.OKEX or exchange == Exchange.HUOBI:
            self.load_bar(days=10,use_database=True)
        else:
            self.load_bar(10)

