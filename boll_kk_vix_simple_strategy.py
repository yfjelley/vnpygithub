# _*_coding : UTF-8 _*_
# 开发团队 ：yunya
# 开发人员 ：Administrator
# 开发时间 : 2020/6/14 14:11
# 文件名称 ：boll_kc_dc_combination _strategy.py
# 开发工具 ： PyCharm


import talib

from vnpy.app.cta_strategy import (
    CtaTemplate,
    StopOrder,
    Direction,
    TickData,
    BarData,
    TradeData,
    OrderData,
    BarGenerator,
    ArrayManager,
)
from vnpy.trader.constant import Interval
import numpy as np


class Boll_kk_vix_simple_Strategy(CtaTemplate):
    """
    本策略为反向策略，币本位  Reverse 反向
    """

    author = "yunya"

    open_window = 5
    xminute_window = 15
    com_length = 450
    exit_dc_length = 10
    fast_sma_length = 45
    slow_sma_length = 110
    cci_length = 30
    cci_exit = 26
    sl_multiplier = 8.0
    fixed_size = 1


    bollkk_ema = 0
    bollkk_up = 0
    bollkk_down = 0
    bollkk_width = 0
    cci_vlue = 0
    long_stop = 0
    short_stop = 0
    exit_up = 0
    exit_down = 0
    atr_value = 0
    long_entry = 0
    short_entry = 0
    ma_trend = 0
    exit_dc_long =0
    exit_dc_short = 0
    intra_trade_high = 0
    intra_trade_low = 0



    parameters = [
                "open_window",
                "xminute_window",
                "com_length",
                "fast_sma_length",
                "slow_sma_length",
                "cci_length",
                "cci_exit",
                "exit_dc_length",
                "sl_multiplier",
                "fixed_size",
    ]

    variables = [
                "bollkk_ema",
                "bollkk_up",
                "bollkk_down",
                "bollkk_width",
                "cci_vlue",
                "long_stop",
                "short_stop",
                "exit_up",
                "exit_down",
                "atr_value",
                "long_entry",
                "short_entry",
                "ma_trend",
    ]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        self.bg_xminute = BarGenerator(
            on_bar=self.on_bar,
            window=self.xminute_window,
            on_window_bar=self.on_xminute_bar,
            interval=Interval.MINUTE
        )
        self.am_xminute = ArrayManager(self.com_length + 10)
        self.bg = BarGenerator(self.on_bar, self.open_window, self.on_open_bar)
        self.am = ArrayManager()

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
        self.bg_xminute.update_tick(tick)

    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        self.bg.update_bar(bar)
        self.bg_xminute.update_bar(bar)

    def on_open_bar(self, bar: BarData):
        """
        :param bar:
        :return:
        """
        # 先使用挂单全撤的粗化订单管理
        self.cancel_all()

        self.am.update_bar(bar)
        if not self.am_xminute.inited or not self.am.inited:
            return

        if self.pos == 0:
            # 根据布林带宽度动态调整仓位大小
            # self.trading_size = max(int(self.risk_level / self.xminute_com_width), 1)
            self.intra_trade_high = bar.high_price
            self.intra_trade_low = bar.low_price
            if self.cci_value > self.cci_exit and self.ma_trend > 0:
                self.buy(self.bollkk_up,self.fixed_size, True)
                
            elif self.cci_value < -self.cci_exit and self.ma_trend < 0:
                self.short(self.bollkk_down, self.fixed_size, True)

        elif self.pos > 0:
            self.intra_trade_high = max(self.intra_trade_high, bar.high_price)
            self.intra_trade_low = bar.low_price

            exit_long_stop = self.intra_trade_high - self.bollkk_width * self.sl_multiplier
            exit_long_dc = max(exit_long_stop,self.exit_dc_long)
            self.exit_up = max(exit_long_dc, self.long_stop)
            self.sell(self.exit_up, abs(self.pos), True)

        elif self.pos < 0:
            self.intra_trade_high = bar.high_price
            self.intra_trade_low = min(self.intra_trade_low, bar.low_price)

            exit_short_stop = self.intra_trade_low + self.bollkk_width * self.sl_multiplier
            exit_shout_dc = min(exit_short_stop,self.exit_dc_short)
            self.exit_down = min(exit_shout_dc, self.short_stop)
            self.cover(self.exit_down, abs(self.pos), True)

        self.put_event()
        self.sync_data()

    def on_xminute_bar(self, bar: BarData):
        """
        :param bar:
        :return:
        """
        # x分钟 多策略合合成的通道线
        self.am_xminute.update_bar(bar)
        
        if not self.am_xminute.inited:
            return

        bollkk_ema_value,self.bollkk_up,self.bollkk_down,= self.boll_kk_combination(
                                                                                high=self.am_xminute.high[:-1],
                                                                                close=self.am_xminute.close[:-1],
                                                                                low=self.am_xminute.low[:-1],
                                                                                com_length=self.com_length
                                                                            )

        # 计算开平信号
        self.current_close = self.am_xminute.close[-1]
        self.last_close = self.am_xminute.close[-2]
        self.bollkk_ema = bollkk_ema_value[-1]

        self.bollkk_width = abs(self.bollkk_up - self.bollkk_down)

        self.cci_value = self.am_xminute.cci(self.cci_length)



        self.fast_ma = self.am_xminute.sma(self.fast_sma_length)
        self.slow_ma = self.am_xminute.sma(self.slow_sma_length)

        if self.fast_ma > self.slow_ma:
            self.ma_trend = 1
        else:
            self.ma_trend = -1
        self.atr_value = self.am_xminute.atr(30)
        self.exit_dc_short,self.exit_dc_long = self.am_xminute.donchian(self.exit_dc_length)
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
        if trade.direction == Direction.LONG:
            self.long_entry = trade.price  # 成交最高价
            self.long_stop = self.long_entry - 2 * self.atr_value
        else:
            self.short_entry = trade.price
            self.short_stop = self.short_entry + 2 * self.atr_value

        self.sync_data()

    def on_stop_order(self, stop_order: StopOrder):
        """
        Callback of stop order update.
        """
        pass

    def boll_kk_combination(self,high,close,low,com_length):
        """
        通过计算收盘价与收盘价均线之间的倍数，来自动调整boll 、kk 的通过宽度
        """

        # 计算组合均线
        bollkk_ema = talib.EMA(close, com_length)

        # 计算自适布林带
        boll_std = talib.STDDEV(close, com_length)
        boll_dev = abs(close - bollkk_ema) / boll_std
        
        boll_up = bollkk_ema + boll_dev * boll_std
        boll_down = bollkk_ema - boll_dev * boll_std

        # 计算自适肯特通道
        kk_atr = talib.ATR(high, low, close, com_length)
        kk_dev = abs(close - bollkk_ema) / kk_atr

        kk_up = bollkk_ema + kk_atr * kk_dev
        kk_down = bollkk_ema - kk_atr * kk_dev

        bollkk_up = max(boll_up[-1],kk_up[-1])
        bollkk_down = min(boll_down[-1],kk_down[-1])


        return bollkk_ema,bollkk_up,bollkk_down,
