from typing import Any
import numpy as np
import talib

from vnpy.app.cta_strategy import (
    CtaTemplate,
    BarGenerator,
    ArrayManager,
    TickData,
    OrderData,
    BarData,
    TradeData,
    StopOrder
)
from  vnpy.app.cta_strategy.new_strategy import NewBarGenerator
from vnpy.trader.constant import Interval


class AtrStopRsiDcStrategy(CtaTemplate):
    """"""
    author = "yunya"

    hour_window = 1
    minute_window = 50
    open_window = 5
    rsi_length = 15
    distance_line = 2.0
    nloss_singnal = 3.1
    exit_dc_length = 30
    sl_multiplier = 8.0

    fixd_size = 1
    atr_window = 30

    exit_dowm = 0
    exit_up = 0
    atr_entry = 0
    rsi_entry = 0
    current_atr_stop = 0.0
    last_atr_stop = 0.0
    intra_trade_high = 0
    intra_trade_low = 0
    nloss_array = 0.0
    long_stop = 0
    short_stop = 0
    ask = 0
    bid = 0
    atr_value = 0

    parameters = [
            "hour_window",
            "minute_window",
            "open_window",
            "nloss_singnal",
            "rsi_length",
            "exit_dc_length",
            "sl_multiplier",
            "distance_line",
            "fixd_size",
            "atr_window"
    ]

    variables = [
        "current_atr_stop",
        "last_atr_stop",
        "long_stop",
        "short_stop",
        "atr_entry",
        "atr_value",
        "ask",
        "bid"
    ]

    def __init__(
            self,
            cta_engine: Any,
            strategy_name: str,
            vt_symbol: str,
            setting: dict,
    ):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)
        self.atr_stop_array = np.zeros(10)

        self.bg_xhour= NewBarGenerator(
                                            on_bar= self.on_bar,
                                            window=self.hour_window,
                                            on_window_bar=self.on_xhour_bar,
                                            interval=Interval.HOUR
                                            )
        self.am_hour = ArrayManager()
        
        self.bg_xminute = NewBarGenerator(
                                            on_bar=self.on_bar,
                                            window=self.minute_window,
                                            on_window_bar=self.on_xminute_bar
                                            )
        self.am_xminute = ArrayManager()


        self.bg_open = NewBarGenerator(
                                    on_bar=self.on_bar,
                                    window=self.open_window,
                                    on_window_bar=self.on_5min_bar
                                    )
        self.am_open = ArrayManager()

    def on_init(self):
        """
        Callback when strategy is inited.
        """
        self.write_log("策略初始化。。")
        self.load_bar(10)

        self.put_event()

    def on_start(self):
        """
        Callback when strategy is started.
        """
        self.write_log("策略启动。。")
        self.put_event()

    def on_stop(self):
        """
        Callback when strategy is stopped.
        """
        self.write_log("策略停止。。")
        self.put_event()

    def on_tick(self, tick: TickData):
        """
        Callback of new tick data update.
        """
        self.bg_open.update_tick(tick)
        self.ask = tick.ask_price_1  # 卖一价
        self.bid = tick.bid_price_1  # 买一价

        self.put_event()

    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        self.bg_xhour.update_bar(bar)
        self.bg_xminute.update_bar(bar)
        self.bg_open.update_bar(bar)

    def on_5min_bar(self, bar: BarData):

        self.cancel_all()
        self.am_open.update_bar(bar)

        if not self.am_open.inited or not self.am_xminute.inited or not self.am_hour.inited:
            return

        self.atr_value = self.am_open.atr(self.atr_window)

        if not self.pos:
            self.intra_trade_high = bar.high_price
            self.intra_trade_low = bar.low_price

            up_limit = self.current_atr_stop * (1 + self.distance_line / 100)
            down_limit = self.current_atr_stop * (1 - self.distance_line / 100)

            if self.atr_entry > 0 and self.rsi_entry > 0 and bar.close_price < up_limit:

                self.buy(up_limit, self.fixd_size, True)

            elif self.atr_entry < 0 and self.rsi_entry < 0 and bar.close_price > down_limit:
                self.short(down_limit, self.fixd_size, True)

        elif self.pos > 0:
            self.intra_trade_high = max(self.intra_trade_high, bar.high_price)
            self.intra_trade_low = bar.low_price
            long_stop_high = self.intra_trade_high - self.atr_value * self.sl_multiplier

            self.long_stop = max(self.exit_up,long_stop_high)
            self.sell(self.long_stop, abs(self.pos), True)

        elif self.pos < 0:
            self.intra_trade_high = bar.high_price
            self.intra_trade_low = min(self.intra_trade_low, bar.low_price)
            short_stop_low = self.intra_trade_low + self.atr_value * self.sl_multiplier

            self.short_stop = min(self.exit_dowm,short_stop_low)
            self.cover(self.short_stop, abs(self.pos), True)

        self.put_event()

    def on_xminute_bar(self, bar: BarData):
        """
        :param bar: 
        :return: 
        """
        self.am_xminute.update_bar(bar)

        if not self.am_xminute.inited:
            return

        rsi_array = talib.RSI(self.am_xminute.close[:-1], self.rsi_length )
        ema_array = talib.EMA(self.am_xminute.close,self.rsi_length)

        dev_array = abs(self.am_xminute.close[:-1] - ema_array[:-1]) / rsi_array

        rsi_up_array = rsi_array + rsi_array * dev_array
        rsi_dow_array = rsi_array - rsi_array * dev_array

        self.rsi_value = self.am_xminute.rsi(self.rsi_length,True)
        self.rsi_up = rsi_up_array[-1]
        self.rsi_dow = rsi_dow_array[-1]

        current_rsi_up = rsi_up_array[-1]
        last_rsi_up = rsi_up_array[-2]
        current_rsi_down = rsi_dow_array[-1]
        last_rsi_down = rsi_dow_array[-2]
        current_rsi_value = self.rsi_value[-1]
        last_rsi_value = self.rsi_value[-2]

        if (current_rsi_value > current_rsi_up) and (last_rsi_value <=last_rsi_up):
            self.rsi_entry = 1
        elif (current_rsi_value < current_rsi_down) and (last_rsi_value >= last_rsi_down):
            self.rsi_entry = -1
        else:
            self.rsi_entry = 0
        # print(self.rsi_entry)

        self.exit_dowm,self.exit_up = self.am_xminute.donchian(self.exit_dc_length)

    def on_xhour_bar(self, bar: BarData):
        """"""
        am_hour = self.am_hour
        am_hour.update_bar(bar)

        self.atr_stop_array[:-1] = self.atr_stop_array[1:]

        if not am_hour.inited:
            return

        # 计算轨道线 nloss
        self.ema_array = am_hour.ema(3, array=True)
        self.nloss_array = am_hour.atr(16, array=True) * self.nloss_singnal

        # 计算轨道线
        self.atr_stop_array = self.atrstop(
            am_hour.close,
            self.atr_stop_array,
            self.nloss_array
        )
        # print(self.atr_stop_array)
        # 初始化
        if self.atr_stop_array[-3] == 0:
            return

        self.current_atr_stop = self.atr_stop_array[-1]
        self.last_atr_stop = self.atr_stop_array[-2]
        current_ema = self.ema_array[-1]
        last_ema = self.ema_array[-2]

        if current_ema > self.current_atr_stop and last_ema <= self.last_atr_stop:
            self.atr_entry = 1
        elif current_ema < self.current_atr_stop and last_ema >= self.last_atr_stop:
            self.atr_entry = -1

        self.put_event()

    def on_trade(self, trade: TradeData):
        """
        有成交时
        Callback of new trade data update.
        """
        self.put_event()

    def on_order(self, order: OrderData):
        """
        订单更新回调
        Callback of new order data update.
        """

        self.put_event()

    def on_stop_order(self, stop_order: StopOrder):
        """
        Callback of stop order update.
        """
        self.put_event()

    def atrstop(self, close, atrstop, nlossatr):

        # 计算轨道线
        if (close[-1] > atrstop[-2]) and (close[-2] > atrstop[-2]):
            atrstop[-1] = max(atrstop[-2], close[-1] - nlossatr[-1])

        elif (close[-1] < atrstop[-2]) and (close[-2] < atrstop[-2]):
            atrstop[-1] = min(atrstop[-2], close[-1] + nlossatr[-1])

        elif (close[-1] > atrstop[-2]):
            atrstop[-1] = (close[-1] - nlossatr[-1])

        else:
            atrstop[-1] = (close[-1] + nlossatr[-1])
        return atrstop

