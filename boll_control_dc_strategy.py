# _*_coding : UTF-8 _*_
#开发团队 ：yunya
#开发人员 ：Administrator
#开发时间 : 2020/6/17 21:49
#文件名称 ：boll_control_dc_strategy.py
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
from vnpy.trader.object import Direction
from  vnpy.app.cta_strategy.new_strategy import NewBarGenerator

class Boll_Control_Dcs_trategy(CtaTemplate):
    """"""
    author = "yunya"

    open_window = 36
    boll_length = 24
    prop = 1.8
    atr_window = 30
    sl_multiplier = 0.2
    dc_length = 20
    fixed_size = 1

    entry_crossover = 0
    atr_value = 0
    intra_trade_high = 0
    intra_trade_low = 0
    long_stop_trade = 0
    short_stop_trade = 0
    long_stop = 0
    short_stop = 0
    exit_short = 0
    exit_long = 0
    entry_ema = 0


    parameters = [
                "open_window",
                "boll_length",
                "dc_length",
                "sl_multiplier",
                "prop",
                "fixed_size",
                ]

    variables = [
                "entry_crossover",
                "long_stop",
                "short_stop"
                ]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        self.bg = NewBarGenerator(self.on_bar, self.open_window, self.on_xmin_bar)
        self.am = ArrayManager(int(self.boll_length) + 100)

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
        self.sma_array = am.sma(self.boll_length, True)
        std_array = am.sma(self.boll_length, True)
        dev = abs(self.am.close[:-1] - self.sma_array[:-1]) / std_array[:-1]
        dev_max = dev[-self.boll_length:].max()
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
        up_limit = current_sma * (1 + self.prop / 100)
        down_limit = current_sma * (1 - self.prop / 100)

        boll_width = currnet_boll_up - current_boll_down

        # Get crossover
        if (
            last_close <= last_boll_up
            and bar.close_price > currnet_boll_up
            and bar.close_price < up_limit
        ):
            self.entry_crossover = 1
        elif (
            last_close >= last_boll_down
            and bar.close_price < current_boll_down
            and bar.close_price > down_limit
        ):
            self.entry_crossover = -1

        if(last_close <=last_sma
            and bar.close_price > current_sma):
            self.entry_ema = -1
        elif (last_close >= last_sma
            and bar.close_price < current_sma):
            self.entry_ema = 1
        else:
            self.entry_ema = 0

        self.atr_value = am.atr(self.atr_window)
        self.exit_short, self.exit_long = self.am.donchian(self.dc_length)

        if not self.pos:
            self.intra_trade_high = bar.high_price
            self.intra_trade_low = bar.low_price

            if self.entry_crossover > 0:
                self.buy(up_limit, self.fixed_size, True)

            elif self.entry_crossover < 0:
                self.short(down_limit, self.fixed_size, True)

        elif self.pos > 0:
            if self.entry_ema > 0:
                self.sell((bar.close_price - 5), abs(self.pos))

            # 最高价回撤比例、固定止损、唐安奇下轨中的最大值为止损位
            self.intra_trade_high = max(self.intra_trade_high, bar.high_price)
            self.intra_trade_low = bar.low_price

            long_stop_high = self.intra_trade_high - boll_width * self.sl_multiplier
            long_high_trade = max(long_stop_high,self.long_stop_trade)
            self.long_stop = max(self.exit_long,long_high_trade)

            self.sell(self.long_stop, abs(self.pos), True)

        elif self.pos < 0:
            if self.entry_ema < 0:
                self.cover((bar.close_price + 5), abs(self.pos))
            else:
                # 最低价回撤比例、固定止损、唐安奇上轨中的最小值为止损位
                self.intra_trade_high = bar.high_price
                self.intra_trade_low = min(self.intra_trade_low, bar.low_price)

                short_stop_low = self.intra_trade_low + boll_width * self.sl_multiplier
                short_low_trade = min(short_stop_low,self.short_stop_trade)
                self.short_stop = min(short_low_trade,self.exit_short)

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
        if trade.direction == Direction.LONG:
            self.long_entry = trade.price  # 成交最高价
            self.long_stop_trade = self.long_entry - 2 * self.atr_value
        else:
            self.short_entry = trade.price
            self.short_stop_trade = self.short_entry + 2 * self.atr_value

        self.sync_data()
        self.put_event()

    def on_stop_order(self, stop_order: StopOrder):
        """
        Callback of stop order update.
        """
        self.put_event()
        pass


