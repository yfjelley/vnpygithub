# _*_coding : UTF-8 _*_
#开发团队 ：yunya
#开发人员 ：Administrator
#开发时间 : 2020/6/16 21:04
#文件名称 ：back_testing_to_csv.py
#开发工具 ： PyCharm


import pathlib
from enum import Enum

import pandas as pd
pd.set_option('expand_frame_repr', False)
import os


class Backtest(Enum):
    """
    Direction of order/trade/position. backtest
    """
    DNA = "DNA" # 遗传算法类型
    EX = "EX" #"穷举多进程算法"




def to_csv_result(result,class_name,signal_name,symbol,exchange,tag,description,backtest):
    df1 = pd.DataFrame()
    df2 = pd.DataFrame()
    df_ = pd.DataFrame()

    for d in result:
        a = d[0:2]
        c = d[2]
        de = pd.DataFrame([a], columns={'参数': 0, class_name: 1})
        dc = pd.DataFrame([c])
        df1 = df1.append(de)
        df2 = df2.append(dc)

    df_ = pd.concat([df1, df2], axis=1)

    # 通过 异常来解决遗传算法和穷举算法分别保存
    df = df_
    try:
        df = df.rename(columns={
            'start_date': "首个交易日",
            'end_date': '最后交易日',
            'total_days': '总交易日',
            'profit_days': '盈利交易日',
            'loss_days': '亏损交易日',
            'capital': '起始资金',
            'end_balance': '结束资金',
            'max_drawdown': '最大回撤',
            'max_ddpercent': '百分比最大回撤',
            'max_drawdown_duration': '最长回撤天数',
            'total_net_pnl': '总盈亏',
            'daily_net_pnl': '日均盈亏',
            'total_commission': '总手续费',
            'daily_commission': '日均手续费',
            'total_slippage': '总滑点',
            'daily_slippage': '日均滑点',
            'total_turnover': '总成交金额',
            'daily_turnover': '日均成交金额',
            'total_trade_count': '总成交笔数',
            'daily_trade_count': '日均成交笔数',
            'total_return': '总收益率',
            'annual_return': '年化收益',
            'daily_return': '日均收益率',
            'return_std': '收益标准差',
            'sharpe_ratio': 'Sharpe Ratio',
            'return_drawdown_ratio': '收益回撤比'
        })

        df = df[["参数", '总盈亏', 'Sharpe Ratio', '收益回撤比', '年化收益', '收益标准差', '百分比最大回撤', '最长回撤天数', '日均成交笔数', '日均滑点']]

    except KeyError:
        df = df_
    # 回测结果保存文件名
    file_name = '_'.join([
        str(signal_name),
        str(symbol),
        str(exchange),
        str(class_name),
        str(tag),
        str(backtest),
        '.csv'])

    # 回测结果保存路径
    _ = os.path.abspath(os.path.dirname(__file__))  # 返回当前文件路径
    root_path = os.path.abspath(os.path.join(_, "data"))  # 返回根目录文件夹
    result_path = root_path + "\\" + file_name

    # 可能因打开文件，忘记关闭。跑完算法因无法保存文件而浪费算力
    try:
        pd.DataFrame(columns=[description]).to_csv(result_path, index=False)
        df.to_csv(result_path, index=False, mode='a')
        print(f"保存成功，位置为：{root_path}，文件名为：{file_name}")
    except IOError:
        print(f"同名文件被打开，以副本形式保存")
        file_name = '_'.join([
            str(signal_name),
            str(symbol),
            str(exchange),
            str(class_name),
            str(tag),
            str("副本"),
            '.csv'])
        result_path = root_path + "\\" + file_name
        pd.DataFrame(columns=[description]).to_csv(result_path, index=False)
        df.to_csv(result_path, index=False, mode='a')
        print(f"保存成功，位置为：{root_path}，文件被打开，文件以副本方式保存，文件名为：{file_name}")


#
#
# def to_csv(result,signal_name,symbol,open_window,tag,description):
#     df1 = pd.DataFrame()
#     df2 = pd.DataFrame()
#     df = pd.DataFrame()
#     for d in result:
#         print(d)
#         a = d[0:2]
#         c = d[2]
#         de = pd.DataFrame([a], columns={'参数': 0, 'total_net_pnl_new': 1})
#         dc = pd.DataFrame([c])
#         df1 = df1.append(de)
#         df2 = df2.append(dc)
#
#     df = pd.concat([df1, df2], axis=1)
#     df = df.rename(columns={
#         'start_date': "首个交易日",
#         'end_date': '最后交易日',
#         'total_days': '总交易日',
#         'profit_days': '盈利交易日',
#         'loss_days': '亏损交易日',
#         'capital': '起始资金',
#         'end_balance': '结束资金',
#         'max_drawdown': '最大回撤',
#         'max_ddpercent': '百分比最大回撤',
#         'max_drawdown_duration': '最长回撤天数',
#         'total_net_pnl': '总盈亏',
#         'daily_net_pnl': '日均盈亏',
#         'total_commission': '总手续费',
#         'daily_commission': '日均手续费',
#         'total_slippage': '总滑点',
#         'daily_slippage': '日均滑点',
#         'total_turnover': '总成交金额',
#         'daily_turnover': '日均成交金额',
#         'total_trade_count': '总成交笔数',
#         'daily_trade_count': '日均成交笔数',
#         'total_return': '总收益率',
#         'annual_return': '年化收益',
#         'daily_return': '日均收益率',
#         'return_std': '收益标准差',
#         'sharpe_ratio': 'Sharpe Ratio',
#         'return_drawdown_ratio': '收益回撤比'
#     })
#
#     df = df[["参数", '总盈亏', 'Sharpe Ratio', '收益回撤比', '年化收益', '收益标准差', '百分比最大回撤', '最长回撤天数', '日均成交笔数', '日均滑点']]
#     print(df)
#
#     # ===存储参数数据
#     p = os.path.join(root_path,
#                      '%s-%s-%s-%s.csv' % (signal_name, symbol,open_window, tag))
#     pd.DataFrame(columns=[description]).to_csv(p, index=False)
#     df.to_csv(p, index=False, mode='a')
#
