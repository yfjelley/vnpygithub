# _*_coding : UTF-8 _*_
#开发团队 ：yunya
#开发人员 ：Administrator
#开发时间 : 2020/6/14 22:04
#文件名称 ：atrstop_dc_strategy.py
#开发工具 ： PyCharm

from typing import Any
import numpy as np
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

class AtrStop_Dc_Strategy(CtaTemplate):
    """"""
    author = "yunya"

    atrstop_window = 46
    open_window = 5
    distance_line = 2.0
    nloss_singnal = 2.7
    dc_length = 50
    fixd_size = 1
    atr_window = 30

    atr_entry = 0
    current_atr_stop = 0.0
    last_atr_stop = 0.0
    nloss_array = 0.0
    exit_short = 0
    exit_long = 0

    ask = 0
    bid = 0
    atr_value = 0

    parameters = [
            "atrstop_window",
            "open_window",
            "nloss_singnal",
            "dc_length",
            "distance_line",
            "fixd_size",
            "atr_window"
    ]

    variables = [
        "current_atr_stop",
        "last_atr_stop",
        "exit_short",
        "exit_long",
        "atr_entry",
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

        self.bg_xmin = NewBarGenerator(
            self.on_bar,
            window=self.atrstop_window,
            on_window_bar=self.on_xmin_bar
        )
        self.am_xmin = ArrayManager()

        self.bg_5min = BarGenerator(
            self.on_bar,
            window=self.open_window,
            on_window_bar=self.on_5min_bar
        )
        self.am_5min = ArrayManager()

    def on_init(self):
        """
        Callback when strategy is inited.
        """
        self.write_log("策略初始化。。")
        self.load_bar(10)

    def on_start(self):
        """
        Callback when strategy is started.
        """
        self.write_log("策略启动。。")

    def on_stop(self):
        """
        Callback when strategy is stopped.
        """
        self.write_log("策略停止。。")

    def on_tick(self, tick: TickData):
        """
        Callback of new tick data update.
        """
        self.bg_5min.update_tick(tick)

    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        self.bg_xmin.update_bar(bar)
        self.bg_5min.update_bar(bar)

    def on_5min_bar(self, bar: BarData):

        self.cancel_all()
        self.am_5min.update_bar(bar)

        if not self.am_5min.inited or not self.am_xmin.inited:
            return
        if self.atr_stop_array[-3] == 0:
            return
        self.atr_value = self.am_5min.atr(self.atr_window)

        if not self.pos:
            self.intra_trade_high = bar.high_price
            self.intra_trade_low = bar.low_price

            up_limit = self.current_atr_stop * (1 + self.distance_line / 100)
            down_limit = self.current_atr_stop * (1 - self.distance_line / 100)

            if self.atr_entry > 0 and bar.close_price < up_limit:
                self.buy(self.current_atr_stop, self.fixd_size, True)

            elif self.atr_entry < 0 and bar.close_price > down_limit:
                self.short(self.current_atr_stop, self.fixd_size, True)

        elif self.pos > 0:
            self.sell(self.exit_long, abs(self.pos), True)

        elif self.pos < 0:
            self.cover(self.exit_short, abs(self.pos), True)
        self.put_event()

    def on_xmin_bar(self, bar: BarData):
        """"""
        am_xmin = self.am_xmin
        am_xmin.update_bar(bar)

        self.atr_stop_array[:-1] = self.atr_stop_array[1:]

        if not am_xmin.inited:
            return

        # 计算轨道线 nloss
        self.ema_array = am_xmin.ema(3, array=True)
        self.nloss_array = am_xmin.atr(16, array=True) * self.nloss_singnal

        # 计算轨道线
        self.atr_stop_array = self.atrstop(
            am_xmin.close,
            self.atr_stop_array,
            self.nloss_array
        )

        # 初始化
        if self.atr_stop_array[-3] == 0:
            return

        self.current_atr_stop = self.atr_stop_array[-1]
        self.last_atr_stop = self.atr_stop_array[-2]
        current_ema = self.ema_array[-1]
        last_ema = self.ema_array[-2]

        if last_ema <= self.last_atr_stop and current_ema > self.current_atr_stop:
            self.atr_entry = 1
        elif last_ema >= self.last_atr_stop and current_ema < self.current_atr_stop:
            self.atr_entry = -1

        self.exit_short,self.exit_long = self.am_xmin.donchian(self.dc_length)


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


