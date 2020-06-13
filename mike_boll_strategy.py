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

from  vnpy.app.cta_strategy.new_strategy import NewBarGenerator
from vnpy.trader.constant import Direction ,Interval


class Mike_Boll_NewStrategy(CtaTemplate):
    """"""

    author = "云崖"

    open_window = 5
    xminute_window = 15
    mike_window = 1
    boll_length = 50
    boll_dev = 2.0

    mike_length = 80
    sl_multiplier = 9.3
    sl_trade = 2
    fixed_size = 1

    ask = 0
    bid = 0

    emamid = 0
    ema_mid = 0
    ema_hh = 0
    ema_ll = 0

    ema_wr = 0  #初级压力线
    ema_mr = 0  #中级压力线
    ema_sr = 0  #高级压力线

    ema_ws = 0  #初级支撑线
    ema_ms = 0  #中级支撑线
    ema_ss = 0  #高级支撑线

    long_stop = 0
    short_stop = 0
    long_stop_trade = 0
    short_stop_trade = 0
    ema_entry_crossover = 0
    boll_entry_crossover = 0
    last_close = 0
    currnet_boll_up = 0
    last_boll_up = 0
    current_boll_down = 0
    last_boll_down = 0
    boll_width = 0


    parameters = [
                    "open_window",
                    "xminute_window",
                    "mike_window",
                    "boll_length",
                    "boll_dev",

                    "mike_length",
                    "sl_multiplier",
                    "sl_trade",
                    "fixed_size"
                    ]

    variables = [
                    "ema_mid",
                    "ema_hh",
                    "ema_ll",
                    "ema_wr",
                    "ema_mr",
                    "ema_sr",
                    "ema_ws",
                    "ema_ms",
                    "ema_ss",
                    "long_stop",
                    "short_stop",
                    "long_stop_trade",
                    "short_stop_trade",
                    "ema_entry_crossover",
                    "boll_entry_crossover",
                    "last_close",
                    "currnet_boll_up",
                    "last_boll_up",
                    "current_boll_down",
                    "last_boll_down",
                    "boll_width",
                    ]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        self.bg_open = NewBarGenerator(self.on_bar, self.open_window, self.on_open_bar)
        self.am_open = ArrayManager()

        self.bg_xminute = NewBarGenerator(
                                        on_bar=self.on_bar,
                                        window=self.xminute_window,
                                        on_window_bar=self.on_xminute_bar,
                                        interval=Interval.MINUTE
                                        )
        self.am_xminute = ArrayManager()

        self.bg = NewBarGenerator(
                                on_bar=self.on_bar,
                                window=self.mike_window,
                                on_window_bar=self.on_hour_bar,
                                interval=Interval.HOUR
                            )
        self.am = ArrayManager(self.mike_length + 5)

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
        self.bg.update_bar(bar)
        self.bg_xminute.update_bar(bar)
        self.bg_open.update_bar(bar)

    def on_open_bar(self, bar: BarData):
        """"""
        self.cancel_all()

        self.am_open.update_bar(bar)
        if not self.am.inited or not self.am_open.inited or not self.am_xminute.inited:
            return

        if self.pos == 0:
            self.intra_trade_high = bar.high_price
            self.intra_trade_low = bar.low_price

            if self.ema_entry_crossover > 0 and self.boll_entry_crossover > 0:
                self.buy(self.currnet_boll_up, self.fixed_size,True)
                # self.write_log(f"on_15min_bar:buyprice:{bar.close_price},fixe_size:{self.fixed_size}")

            elif self.ema_entry_crossover < 0 and self.boll_entry_crossover < 0:
                self.short(self.current_boll_down, self.fixed_size,True)
                # self.write_log(f"on_15min_bar:shortprice:{bar.close_price},fixe_size:{self.fixed_size}")

        elif self.pos > 0:
            if self.ema_entry_crossover < 0:
                self.sell(bar.close_price - 5, abs(self.pos))
                # self.sell(self.ask,abs(self.pos))

                # self.write_log(f"on_15min_bar:sellprice:{bar.close_price},size:{abs(self.pos)}")
            else:
                self.intra_trade_high = max(self.intra_trade_high, bar.high_price)
                self.intra_trade_low = bar.low_price

                # 使用布林宽度止损
                long_stop_high = self.intra_trade_high - self.boll_width * self.sl_multiplier

                # 取布林宽度与成交价格回撤比例atrr的最大值
                self.long_stop = max(self.long_stop_trade,long_stop_high)
                self.sell(self.long_stop, abs(self.pos), True)
                # self.write_log(
                #     f"on_15min_bar:STOP:sellprice:{self.long_stop},close:{self.am.close[-1]},size:{abs(self.pos)}")

        elif self.pos < 0:
            if self.ema_entry_crossover > 0:
                self.cover(bar.close_price + 5, abs(self.pos))

                # self.write_log(f"on_15min_bar:coverprice:{bar.close_price},size:{abs(self.pos)}")
            else:
                self.intra_trade_high = bar.high_price
                self.intra_trade_low = min(self.intra_trade_low, bar.low_price)

                short_stop_low = self.intra_trade_low + self.boll_width * self.sl_multiplier
                self.short_stop = min(self.short_stop_trade,short_stop_low)

                self.cover(self.short_stop, abs(self.pos), True)
                # self.write_log(
                #     f"on_15min_bar:STOP:shortprice:{self.short_stop},close:{self.am.close[-1]},size:{abs(self.pos)}")

        self.sync_data()
        self.put_event()

    def on_xminute_bar(self,bar:BarData):
        """
        :param bar:
        :return:
        """
        # 计算布林线指标
        self.am_xminute.update_bar(bar)

        if not self.am_xminute.inited and not self.am.inited:
            return

        self.atr_value = self.am_open.atr(30)

        sma_array = self.am_xminute.sma(self.boll_length, True)
        std_array = self.am_xminute.sma(self.boll_length, True)
        dev = abs(self.am_xminute.close[:-1] - sma_array[:-1]) / std_array[:-1]
        dev_max = dev[-self.boll_length:].max()
        boll_up_array = sma_array + std_array * dev_max
        boll_down_array = sma_array - std_array * dev_max

        # Get current and last index
        self.last_close = self.am_xminute.close[-2]
        self.currnet_boll_up = boll_up_array[-1]
        self.last_boll_up = boll_up_array[-2]
        self.current_boll_down = boll_down_array[-1]
        self.last_boll_down = boll_down_array[-2]
        self.boll_width = abs(self.currnet_boll_up - self.current_boll_down)

        if (self.last_close <= self.last_boll_up and bar.close_price > self.currnet_boll_up):
            self.boll_entry_crossover = 1

        elif (self.last_close >= self.last_boll_down and bar.close_price < self.current_boll_down):
            self.boll_entry_crossover = -1
        self.put_event()
    def on_hour_bar(self, bar: BarData):
        """
        计算 mike 指标线
        :param bar:
        :return:
        """

        self.am.update_bar(bar)
        if not self.am.inited:
            return

        # 计算mike压力支撑线
        self.mike()

        if (self.am.close[-1] > self.ema_sr) or (self.ema_ms < self.am.close[-1] < self.ema_ws):
            self.ema_entry_crossover = 1

        elif (self.am.close[-1] < self.ema_ss) or (self.ema_mr > self.am.close[-1] > self.ema_wr):
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
        if trade.direction == Direction.LONG:
            self.long_entry = trade.price
            self.long_stop_trade = self.long_entry - self.sl_trade * self.atr_value
        else:
            self.short_entry = trade.price
            self.short_stop_trade = self.short_entry + self.sl_trade * self.atr_value

        self.put_event()

    def on_stop_order(self, stop_order: StopOrder):
        """
        Callback of stop order update.
        """
        pass

    def mike(self,):

        # 获取 : 前一个收盘价的ema_mid[-2] ，ema_hh  ema_ll
        self.emamid = (self.am.close + self.am.high + self.am.low) / 3
        self.ema_mid = self.emamid[-1]
        self.ema_hh = self.am.high[-self.mike_length:-1].max()
        self.ema_ll = self.am.low[-self.mike_length:-1].min()

        self.ema_wr = self.emamid[-2] + (self.emamid[-2] - self.ema_ll)
        self.ema_mr = self.emamid[-2] + (self.ema_hh - self.ema_ll)
        self.ema_sr = 2 * self.ema_hh - self.ema_ll

        self.ema_ws = self.emamid[-2] - (self.ema_hh - self.emamid[-2])
        self.ema_ms = self.emamid[-2] - (self.ema_hh - self.ema_ll)
        self.ema_ss = 2 * self.ema_ll - self.ema_hh


