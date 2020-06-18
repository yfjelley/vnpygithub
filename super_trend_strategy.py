# _*_coding : UTF-8 _*_
#开发团队 ：yunya
#开发人员 ：Administrator
#开发时间 : 2020/6/14 20:25
#文件名称 ：super_trend_strategy.py
#开发工具 ： PyCharm

import talib

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
from vnpy.trader.constant import Interval


class KeltnerBanditStrategy(CtaTemplate):
    """"""
    author = "用Python的交易员"

    open_window = 5
    minute_window = 15
    hour_window = 1
    atr_length = 30
    atr_multiplier = 2.0

    kk_window = 20
    kk_dev = 2.0
    cci_window = 10
    cci_stop = 44
    atr_window = 10
    risk_level = 5000

    trading_size = 0
    kk_up = 0
    kk_down = 0
    cci_value = 0
    atr_value = 0

    param_houreters = [
        "kk_window", "kk_dev", "cci_window",
        "cci_stop", "atr_window", "risk_level"
    ]
    variables = [
        "trading_size", "kk_up", "kk_down",
        "cci_value", "atr_value"
    ]

    def __init__(self, cta_engine, strategy_nam_houre, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_nam_houre, vt_symbol, setting)

        self.bg_hour = BarGenerator(
            self.on_bar, self.hour_window, self.on_hour_bar, interval=Interval.HOUR)
        self.am_hour = ArrayManager()

        self.bg_minute = BarGenerator(
            self.on_bar,self.minute_window,self.on_xminute_bar,interval=Interval.MINUTE
            )
        self.am_minute = ArrayManager()

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
        self.bg_hour.update_tick(tick)

    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        self.bg_hour.update_bar(bar)
        self.bg_minute.update_bar(bar)

    def on_xminute_bar(self,bar:BarData):
        """
        核心未完成，等前面三个指标有满意结果后做回测。

        super_trend 逻辑 是kc通道的变种，取原版kc上轨最小值为压力线，取原版下轨最大值为支撑线。
        突破 上轨压力线做多，下穿下轨压力线做空。

        过度信号：


        """
        self.cancel_all()

        am_minute = self.am_minute
        am_minute.update_bar(bar)
        if not am_minute.inited:
            return

        self.kk_up, self.kk_down = am_minute.keltner(self.kk_window, self.kk_dev)
        self.cci_value = am_minute.cci(self.cci_window)

        if self.pos == 0:
            if self.supertrend_entry > 0:
                self.buy(self.kk_up, self.trading_size, True)
            elif self.supertrend_entry < 0:
                self.short(self.kk_down, self.trading_size, True)

        elif self.pos > 0:
            if self.cci_value < - self.cci_stop:
                self.sell(bar.close_price - 10, abs(self.pos), False)

        elif self.pos < 0:
            if self.cci_value > self.cci_stop:
                self.cover(bar.close_price + 10, abs(self.pos), False)

        self.put_event()

    def on_hour_bar(self, bar: BarData):
        """"""
        am_hour = self.am_hour
        am_hour.update_bar(bar)
        if not am_hour.inited:
            return

        up,dowm = self.supertrend(
            self.am_hour.close,self.am_hour.high,self.am_hour.low,
            self.atr_length,self.atr_multiplier
        )

        if self.am_hour.close[-1] > up:
            self.supertrend_entry = 1

        elif self.am_hour.close[-1] < dowm:
            self.supertrend_entry = -1

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
    def supertrend(self,close,high,low,atr_length,multiplier ):
        """
        atr= changeATR ? atr(Periods) : atr2
        up=src-(Multiplier*atr)
        up1 = nz(up[1],up)
        up := close[1] > up1 ? max(up,up1) : up
        dn=src+(Multiplier*atr)
        dn1 = nz(dn[1], dn)
        dn := close[1] < dn1 ? min(dn, dn1) : dn
        """
        ema_value = (close + high + low) / 3
        atr_value = talib.ATR(high,low,close,atr_length)

        down_array = ema_value - (atr_value * multiplier )
        up_array = ema_value + (atr_value * multiplier)

        if close[-2] > down_array[-2]:
            up = max(down_array[-1,down_array[-2]])
        else:
            up = down_array[-1]

        if close[-2] < up_array[-2]:
            down = min(up_array[-1],up_array[-2])
        else:
            down = up_array[-1]

        return up,down