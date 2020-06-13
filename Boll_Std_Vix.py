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

class Boll_Std_vix(CtaTemplate):
    """"""
    author = "yunya"

    win_open = 15
    boll_window = 80
    atr_window = 30
    sl_multiplier = 10.0
    fixed_size = 1

    entry_crossover = 0
    atr_value = 0
    intra_trade_high = 0
    intra_trade_low = 0
    long_stop = 0
    short_stop = 0

    parameters = [
                "win_open",
                "boll_window",
                "sl_multiplier",
                "fixed_size",
                ]

    variables = [
                "entry_crossover",
                "atr_value",
                "intra_trade_high",
                "intra_trade_low",
                "long_stop",
                "short_stop"
                ]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        self.bg = NewBarGenerator(self.on_bar, self.win_open, self.on_xmin_bar)
        self.am = ArrayManager(self.boll_window + 100)

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
        self.put_event()

    def on_stop(self):
        """
        Callback when strategy is stopped.
        """
        self.write_log("策略停止")
        self.put_event()

    def on_tick(self, tick: TickData):
        """
        Callback of new tick data update.
        """
        self.bg.update_tick(tick)

    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        self.bg.update_bar(bar)

    def on_xmin_bar(self, bar: BarData):
        """"""
        self.cancel_all()

        am = self.am
        am.update_bar(bar)
        if not am.inited:
            return

        # Calculate array  计算数组
        self.sma_array = am.sma(self.boll_window, True)
        std_array = am.std(self.boll_window, True)
        dev = abs(self.am.close[:-1] - self.sma_array[:-1]) / std_array[:-1]
        dev_max = dev[-self.boll_window:].max()
        self.boll_up_array = self.sma_array + std_array * dev_max
        self.boll_down_array = self.sma_array - std_array * dev_max

        # Get current and last index
        current_sma = self.sma_array[-1]
        last_sma = self.sma_array[-2]
        last_close = self.am.close[-2]
        currnet_boll_up = self.boll_up_array[-1]
        last_boll_up = self.boll_up_array[-2]
        current_boll_down = self.boll_down_array[-1]
        last_boll_down = self.boll_down_array[-2]


        # Get crossover
        if (bar.close_price > currnet_boll_up and last_close <= last_boll_up):
            self.entry_crossover = 1

        elif(bar.close_price < current_boll_down and last_close >=last_boll_down):
            self.entry_crossover = -1

        self.atr_value = am.atr(self.atr_window)

        if not self.pos:
            self.intra_trade_high = bar.high_price
            self.intra_trade_low = bar.low_price

            if self.entry_crossover > 0:
                self.buy(bar.close_price, self.fixed_size, True)

            elif self.entry_crossover < 0:
                self.short(bar.close_price, self.fixed_size, True)

        elif self.pos > 0:

            self.intra_trade_high = max(self.intra_trade_high, bar.high_price)
            self.intra_trade_low = bar.low_price

            self.long_stop = self.intra_trade_high - self.atr_value * self.sl_multiplier
            self.sell(self.long_stop, abs(self.pos), True)

        elif self.pos < 0:

            self.intra_trade_high = bar.high_price
            self.intra_trade_low = min(self.intra_trade_low, bar.low_price)

            self.short_stop = self.intra_trade_low + self.atr_value * self.sl_multiplier
            self.cover(self.short_stop, abs(self.pos), True)

        self.put_event()

    def on_order(self, order: OrderData):
        """
        Callback of new order data update.
        """
        self.put_event()
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
        self.put_event()
        pass


