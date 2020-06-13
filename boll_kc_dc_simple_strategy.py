# _*_coding : UTF-8 _*_
# 开发团队 ：yunya
# 开发人员 ：Administrator
# 开发时间 : 2020/6/11 19:11
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


class Boll_Kc_Dc_Reverse_Strategy(CtaTemplate):
    """
    本策略为反向策略，币本位  Reverse 反向
    """

    author = "yunya"
    open_window = 2
    xsmall_window = 15
    com_length = 250
    boll_kk_dev = 2.0
    kk_atr_length = 30
    sl_multiplier = 0.5
    risk_level = 10000

    trading_size = 0
    xsmall_up_min = 0
    xsmall_down_min = 0
    xsmall_up_max = 0
    xsmall_down_max = 0
    xsmall_ema_mid = 0
    xsmall_com_width = 0
    long_entry = 0
    short_entry = 0
    long_stop = 0
    short_stop = 0
    exit_up = 0
    exit_down = 0
    atr_value = 0

    intra_trade_high = 0
    intra_trade_low = 0

    parameters = [
        "open_window",
        "xsmall_window",
        "com_length",
        "boll_kk_dev",
        "kk_atr_length",
        "sl_multiplier",
        "risk_level",
    ]
    variables = [
            "trading_size",
            "xsmall_up_min",
            "xsmall_down_min",
            "xsmall_up_max",
            "xsmall_down_max",
            "xsmall_ema_mid",
            "xsmall_com_width",
            "long_entry",
            "short_entry",
            "long_stop",
            "short_stop",
            "exit_up",
            "exit_down",
            "atr_value",
    ]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        self.bg_xsmall = BarGenerator(
            on_bar=self.on_bar,
            window=self.xsmall_window,
            on_window_bar=self.on_xsmall_bar,
            interval=Interval.MINUTE
        )
        self.am_xsmall = ArrayManager(self.com_length + 10)
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
        self.bg_xsmall.update_tick(tick)

    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        self.bg.update_bar(bar)
        self.bg_xsmall.update_bar(bar)
  
    def on_open_bar(self,bar:BarData):
        """
        :param bar:
        :return:
        """
        # 先使用挂单全撤的粗化订单管理
        self.cancel_all()

        self.am.update_bar(bar)
        if not self.am_xsmall.inited or not self.am.inited:
            return

        if self.pos == 0:
            # 根据布林带宽度动态调整仓位大小
            self.trading_size = max(int(self.risk_level / self.xsmall_com_width), 1)
            self.intra_trade_high = bar.high_price
            self.intra_trade_low = bar.low_price

            # 如果价格突破 xsmall_up_min 线时，在xsmall_up_max 价格挂停止单
            if self.am_xsmall.close[-1] >= self.xsmall_up_min and self.am.close[-1] >=self.xsmall_up_min:
                self.buy(self.xsmall_up_max,self.trading_size,True)

            # 如果价格突破 xsmall_down_min 线时，在xsmall_down_max 价格挂停止单
            elif self.am_xsmall.close[-1] <= self.xsmall_down_min and self.am.close[-1] <= self.xsmall_down_min:
                self.short(self.xsmall_down_max,self.trading_size,True)

        elif self.pos > 0:
            # 成交价固定止损位与中轨中最大值为当前止损位
            # self.exit_up = max(self.xsmall_ema_mid,self.long_stop)

            # 成交价回定止损 与最高价回撤一定比例通道宽度值
            self.intra_trade_high = max(self.intra_trade_high,bar.high_price)
            self.intra_trade_low = bar.low_price

            exit_long_stop = self.intra_trade_high - self.xsmall_com_width * self.sl_multiplier
            self.exit_up = max(exit_long_stop,self.long_stop)
            self.sell(self.exit_up,abs(self.pos),True)

        elif self.pos < 0:
            # 成交价固定止损位与中轨中最小值为当前止损位
            # self.exit_down = min(self.xsmall_ema_mid,self.short_stop)

            # 成交价回定止损 与最高价回撤一定比例通道宽度值
            self.intra_trade_high = bar.high_price
            self.intra_trade_low = min(self.intra_trade_low,bar.low_price)

            exit_short_stop = self.intra_trade_low - self.xsmall_com_width * self.sl_multiplier
            self.exit_down = min(exit_short_stop,self.short_stop)
            self.cover(self.exit_down,abs(self.pos),True)

        self.sync_data()
        self.put_event()

    def on_xsmall_bar(self, bar: BarData):
        """
        :param bar:
        :return:
        """
        # x分钟 多策略合合成的通道线
        self.am_xsmall.update_bar(bar)
        if not self.am_xsmall.inited :
            return

        self.xsmall_ema_mid,self.xsmall_com_width,self.xsmall_up_min, self.xsmall_down_min,\
        self.xsmall_up_max, self.xsmall_down_max = self.boll_kc_dc_combination(
                                                                        high=self.am_xsmall.high[:-1],
                                                                        low=self.am_xsmall.low[:-1],
                                                                        close=self.am_xsmall.close[:-1],
                                                                        boll_kk_dev=self.boll_kk_dev,
                                                                        kk_atr_length=self.kk_atr_length,
                                                                        com_length=self.com_length
                                                                        )

        # print(f"xsmall: mid:{self.xsmall_ema_mid},width:{self.xsmall_com_width},upmin:{self.xsmall_up_min},\
        #         downmin:{self.xsmall_down_min},upmax:{self.xsmall_up_max},downmax:{self.xsmall_down_max}" + "\n")

        self.atr_value = self.am_xsmall.atr(self.kk_atr_length)

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

    def boll_kc_dc_combination(self, high, close, low, boll_kk_dev,kk_atr_length,com_length):

        # 计算组合均线
        ema_com = talib.EMA(close, com_length)

        # 计算布林带
        boll_std = talib.STDDEV(close, com_length)
        boll_up = ema_com + boll_kk_dev * boll_std
        boll_down = ema_com - boll_kk_dev * boll_std

        # 计算肯特通道
        kc_atr = talib.ATR(high, low, close, kk_atr_length)
        kc_up = ema_com + kc_atr * boll_kk_dev
        kc_dowm = ema_com - kc_atr * boll_kk_dev

        # 计算唐安奇通道
        dc_up = talib.MAX(high, com_length)
        dc_down = talib.MIN(low, com_length)

        # 计算轨道 因kc通道是直接，最小值大概率是直接，所以去除
        pass_up_min = min(dc_up[-1], boll_up[-1])
        pass_down_min = max(dc_down[-1], boll_down[-1])

        pass_up_max = max(kc_up[-1], dc_up[-1], boll_up[-1])
        pass_down_max = min(kc_dowm[-1], dc_down[-1], boll_down[-1])
        ema_mid = ema_com[-1]

        com_width = abs(pass_up_max - pass_down_max)

        return ema_mid, com_width, pass_up_min, pass_down_min, pass_up_max, pass_down_max
