# _*_coding : UTF-8 _*_
#开发团队 ：yunya
#开发人员 ：Administrator
#开发时间 : 2020/6/12 14:34
#文件名称 ：mike_boll_strategy.py
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

from vnpy.trader.constant import Direction ,Interval


class Mike_Boll_Strategy(CtaTemplate):
    """"""

    author = "云崖"

    open_window = 5
    xminute_window = 15
    mike_window = 2
    boll_length = 80
    boll_dev = 2.0
    mike_length = 20
    sl_multiplier = 0.81
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

    boll_up = 0
    boll_down = 0
    long_stop = 0
    short_stop = 0
    ema_entry_crossover = 0
    boll_entry_crossover = 0
    boll_width = 0

    param_xhoureters = [
                    "open_window",
                    "xminute_window",
                    "mike_window",
                    "boll_length",
                    "mike_length",
                    "sl_multiplier",
                    "sl_trade",
                    "fixed_size"
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

        self.bg_open = BarGenerator(self.on_bar, self.open_window, self.on_open_bar)
        self.am_open = ArrayManager()

        self.bg_xminute = BarGenerator(
                                        on_bar=self.on_bar,
                                        window=self.xminute_window,
                                        on_window_bar=self.on_xminute_bar,
                                        interval=Interval.MINUTE
                                        )
        self.am_xminute = ArrayManager()

        self.bg_xhour = BarGenerator(
                                on_bar=self.on_bar,
                                window=self.mike_window,
                                on_window_bar=self.on_hour_bar,
                                interval=Interval.HOUR
                            )
        self.am_xhour = ArrayManager(self.mike_length + 5)

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
        self.bg_xhour.update_tick(tick)
        self.ask = tick.ask_price_1  # 卖一价
        self.bid = tick.bid_price_1  # 买一价

    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        self.bg_xhour.update_bar(bar)
        self.bg_xminute.update_bar(bar)
        self.bg_open.update_bar(bar)

    def on_open_bar(self, bar: BarData):
        """
         开单窗口
        """
        self.cancel_all()

        self.am_open.update_bar(bar)
        if not self.am_xhour.inited or not self.am_xminute.inited or not self.am_open.inited :
            return

        if self.pos == 0:
            self.intra_trade_high = bar.high_price
            self.intra_trade_low = bar.low_price

            if self.ema_entry_crossover > 0 :
                self.buy(self.boll_up, self.fixed_size,True)

            elif self.ema_entry_crossover < 0 :
                self.short(self.boll_down, self.fixed_size,True)

        elif self.pos > 0:
            if self.ema_entry_crossover < 0:
                self.sell(bar.close_price - 5, abs(self.pos))

            else:
                self.intra_trade_high = max(self.intra_trade_high, bar.high_price)
                self.intra_trade_low = bar.low_price

                # 使用布林宽度止损
                self.long_stop = self.intra_trade_high - self.boll_width * self.sl_multiplier
                self.sell(self.long_stop, abs(self.pos), True)

        elif self.pos < 0:
            if self.ema_entry_crossover > 0:
                self.cover(bar.close_price + 5, abs(self.pos))

            else:
                self.intra_trade_high = bar.high_price
                self.intra_trade_low = min(self.intra_trade_low, bar.low_price)

                self.short_stop = self.intra_trade_low + self.boll_width * self.sl_multiplier
                self.cover(self.short_stop, abs(self.pos), True)

        self.sync_data()
        self.put_event()

    def on_xminute_bar(self,bar:BarData):
        """
        :param_xhour bar:
        :return:
        """
        # 计算布林线指标
        self.am_xminute.update_bar(bar)

        if not self.am_xminute.inited and not self.am_xhour.inited:
            return

        boll_up_array,boll_down_array = self.am_xminute.boll(self.boll_length,self.boll_dev,True)

        self.boll_up = boll_up_array[-1]
        self.boll_down = boll_down_array[-1]
        self.boll_width = self.boll_up - self.boll_down

        self.put_event()
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
        self.put_event()

    def on_stop_order(self, stop_order: StopOrder):
        """
        Callback of stop order update.
        """
        pass


