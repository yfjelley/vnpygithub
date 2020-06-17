# _*_coding : UTF-8 _*_
#开发团队 ：yunya
#开发人员 ：Administrator
#开发时间 : 2020/5/14 16:50
#文件名称 ：多策略组合回测.py
#开发工具 ： PyCharm

"""
jupyter notebook
"""



# 导入库
from importlib import reload
from vnpy.app.cta_strategy.backtesting import BacktestingEngine, OptimizationSetting
from datetime import datetime


# 定义使用的函数
def run_backtesting(strategy_class, setting, vt_symbol, interval, start, end, rate, slippage, size, pricetick, capital):
    engine = BacktestingEngine()
    engine.set_parameters(
        vt_symbol=vt_symbol,
        interval=interval,
        start=start,
        end=end,
        rate=rate,
        slippage=slippage,
        size=size,
        pricetick=pricetick,
        capital=capital
    )
    engine.add_strategy(strategy_class, setting)
    engine.load_data()
    engine.run_backtesting()
    df = engine.calculate_result()
    return df

# 运行策略函数
def show_portafolio(df):
    engine = BacktestingEngine()
    engine.calculate_statistics(df)
    engine.show_chart(df)


# 导入第一个策略
from vnpy.huicheshuju.class_strategy.AtrStop_UT import AtrStop_Ut
import AtrStop_UT
from vnpy.huicheshuju.class_strategy.RSI_Vix_Dc import RsiVixDcStrategy
from vnpy.huicheshuju.class_strategy.Vix_Keltnerl import VixKeltnerl
reload(AtrStop_UT)

df1 = run_backtesting(
    strategy_class=AtrStop_Ut,
    setting={
        "atrstop_window":36,
        "nloss_singnal":2.6,
        "sl_multiplier":10.0,
        "distance_line":1.4,
        "fixd_size":1,
        "atr_window":30
        },
    vt_symbol="BTCUSD.BINANCE",
    interval="1m",
    start=datetime(2017,1,1),
    end=datetime(2020,5,30),
    rate= 2/1000,
    slippage=0.5,
    size=1,
    pricetick=0.5,
    capital=10000,
    )

# 运行第一个策略
show_portafolio(df1)


# 导入第二个策略
from vnpy.huicheshuju.class_strategy.Vix_Keltnerl import VixKeltnerl
import Boll_Control_Proportion_vix
reload(Boll_Control_Proportion_vix)

setting={
    "win_open":10,
    "kk_window":50,
    "sl_multiplier":13,
    "fixed_size":1}


setting={
    "win_open":36,
    "boll_window":24,
    "prop":1.8,
    "sl_multiplier":4.4,
    "fixed_size":1,}
df2 = run_backtesting(
    strategy_class=Boll_Control_Proportion_vix.Boll_Control_Proportion_vix,
    setting={},
    vt_symbol="BTCUSD.BINANCE",
    interval="1m",
    start=datetime(2017, 1, 1),
    end=datetime(2020, 5, 30),
    rate=0.75/10000,
    slippage=0.5,
    size=10,
    pricetick=0.5,
    capital=1_000_000,
    )

# 运行第二个策略
show_portafolio(df2)

# 显示两个策略的结果
dfp = df1 + df2
dfp =dfp.dropna()
show_portafolio(dfp)