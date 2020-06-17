from itertools import combinations
from tqdm import tqdm

def pbo_cal(opr,S=10,ind='sortino'):
    '''
    【回测过拟合概率计算】
    opr：参数组收益序列表
    S：划分的时间序列子集数
    ind：指定夏普率或索迪诺比率作为评价指标 [sharpe, sortino]
    '''

    assert S%2 == 0,'划分的时间序列子集数必须为偶数'

    Snum = opr.shape[0] // S                                        # 得到每份子集长度
    sub_oprs = [opr.iloc[Snum*i:Snum*(i+1)] for i in range(S)]      # 划分得到子集list，多余的部分舍去
    logits = []                                                     # 初始化logit变量集

    for c in tqdm(list(combinations(list(range(S)), S//2))):
        # 遍历每种组合：抽取一半的子集
        c_ = set(range(S)) - set(c)
        train = pd.concat([sub_oprs[i] for i in c])
        test = pd.concat([sub_oprs[i] for i in c_])
        # 一半子集组合为训练集，另一半补集组合为测试集

        if ind == 'sharpe':
            train_ratio = train.mean() / train.std() 
            test_ratio = test.mean() / test.std()
        
        if ind == 'sortino':
            train_ratio = train.mean() / train.mask(train>0,0).std()
            test_ratio = test.mean() / test.mask(test>0,0).std()
        # 计算训练集及测试集，每组参数对应的评价指标
        
        w = test_ratio.rank()[train_ratio.idxmax()] / (test_ratio.shape[0] + 1)
        # 训练集最优参数组在测试集的相对排名

        logits.append(np.log(w/(1-w)))
    
    logits = pd.DataFrame(sorted(logits),columns=['logit'])
    logits['cum_prob'] = (logits.index + 1) / logits.shape[0]
    # 计算logit变量经验分布
    
    return logits.loc[logits['logit']<=0,'cum_prob'].max()
    # 返回pbo，pbo越小策略越有效