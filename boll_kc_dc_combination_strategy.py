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


class Boll_Kc_Dc_CombinationStrategy(CtaTemplate):
    """"""
    author = "yunya"
    open_window = 2
    xsmall_window = 15
    xbig_window = 15
    com_length = 250
    boll_dev = 2.0
    kk_dev = 2.0
    trading_size = 1

    xsmall_up_min = 0
    xsmall_down_min = 0
    xsmall_up_max = 0
    xsmall_down_max = 0
    xsmall_ema_mid = 0
    xsmall_com_width = 0

    xbig_up_min = 0
    xbig_down_min = 0
    xbig_up_max = 0
    xbig_down_max = 0
    xbig_ema_mid = 0
    xbig_com_width = 0

    long_entry = 0
    short_entry = 0
    long_stop = 0
    short_stop = 0
    exit_up = 0
    exit_down = 0

    # entry_window = 28
    # exit_window = 7
    # atr_window = 4
    # risk_level = 0.2
    #
    # trading_size = 0
    # entry_up = 0
    # entry_down = 0
    # exit_up = 0
    # exit_down = 0
    # atr_value = 0
    #


    parameters = ["entry_window", "exit_window", "atr_window", "risk_level"]
    variables = [
        "entry_up", "entry_down", "exit_up",
        "exit_down", "trading_size", "atr_value"
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
        self.bg_xbig = BarGenerator(
            on_bar=self.on_bar,
            window=self.xbig_window,
            on_window_bar=self.on_xbig_bar,
            interval=Interval.MINUTE
        )
        self.am_xbig = ArrayManager(self.com_length + 10)

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
        self.bg_xbig.update_bar(bar)

    def on_open_bar(self,bar:BarData):
        """
        :param bar:
        :return:
        """
        # 先使用挂单全撤的粗化订单管理
        self.cancel_all()

        self.am.update_bar(bar)
        if not self.am_xsmall.inited or not self.am_xbig.inited or not self.am.inited:
            return

        if self.pos == 0:
            # 如果价格突破 xsmall_up_min 线时，在xsmall_up_max 价格挂停止单
            if self.am_xsmall.close[-1] >= self.xsmall_up_min and self.am.close[-1] >=self.xsmall_up_min:
                self.buy(self.xsmall_up_max,self.trading_size,True)

            # 如果价格突破 xsmall_down_min 线时，在xsmall_down_max 价格挂停止单
            elif self.am_xsmall.close[-1] <= self.xsmall_down_min and self.am.close[-1] <= self.xsmall_down_min:
                self.short(self.xsmall_down_max,self.trading_size,True)

        elif self.pos > 0:
            # 成交价固定止损位与中轨中最大值为当前止损位
            self.exit_up = max(self.xsmall_ema_mid,self.long_stop)
            self.sell(self.exit_up,abs(self.pos),True)

        elif self.pos < 0:
            # 成交价固定止损位与中轨中最小值为当前止损位
            self.exit_down = min(self.xsmall_ema_mid,self.short_stop)
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
        if not self.am_xsmall.inited or not self.am_xbig.inited:
            return

        self.xsmall_ema_mid,self.xsmall_com_width,self.xsmall_up_min, self.xsmall_down_min,\
        self.xsmall_up_max, self.xsmall_down_max = self.boll_kc_dc_combination(
                                                                        high=self.am_xsmall.high[:-1],
                                                                        low=self.am_xsmall.low[:-1],
                                                                        close=self.am_xsmall.close[:-1],
                                                                        boll_dev=self.boll_dev,
                                                                        kk_dev=self.kk_dev,
                                                                        com_length=self.com_length
                                                                        )

        print(f"xsmall: mid:{self.xsmall_ema_mid},width:{self.xsmall_com_width},upmin:{self.xsmall_up_min},\
                downmin:{self.xsmall_down_min},upmax:{self.xsmall_up_max},downmax:{self.xsmall_down_max}" + "\n")

        self.atr_value = self.am_xsmall.atr(self.com_length)

        self.sync_data()
        self.put_event()

    def on_xbig_bar(self,bar:BarData):
        """
        :param bar:
        :return:
        """
        # x分钟 多策略合合成的通道线
        self.am_xbig.update_bar(bar)
        if not self.am_xbig.inited:
            return

        self.xbig_ema_mid,self.xbig_com_width,self.xbig_up_min,self.xbig_down_min,\
        self.xbig_up_max,self.xbig_down_max = self.boll_kc_dc_combination(
                                                                        high=self.am_xbig.high[:-1],
                                                                        close=self.am_xbig.close[:-1],
                                                                        low=self.am_xbig.low[:-1],
                                                                        boll_dev=self.boll_dev,
                                                                        kk_dev=self.kk_dev,
                                                                        com_length=self.com_length
                                                                        )
        print(f"xbig:mid:{self.xbig_ema_mid},width:{self.xbig_com_width},upmin:{self.xbig_up_min},\
                downmin:{self.xbig_down_min},upmax:{self.xbig_up_max},downmax:{self.xbig_down_max}" + "\n")

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

    def boll_kc_dc_combination(self, high, close, low, boll_dev, kk_dev, com_length):

        # 计算组合均线
        ema_com = talib.EMA(close, com_length)

        # 计算布林带
        boll_std = talib.STDDEV(close, com_length)
        boll_up = ema_com + boll_dev * boll_std
        boll_down = ema_com - boll_dev * boll_std

        # 计算肯特通道
        kc_atr = talib.ATR(high, low, close, com_length)
        kc_up = ema_com + kc_atr * kk_dev
        kc_dowm = ema_com - kc_atr * kk_dev

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
