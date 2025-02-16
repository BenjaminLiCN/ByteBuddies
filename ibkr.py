import json
from ib_insync import IB, Stock, util

# 连接到TWS
util.startLoop()  # 启动异步事件循环
ib = IB()
ib.connect('127.0.0.1', 7497, clientId=1)  # 请根据实际情况修改端口号和客户端ID

# 定义合约
nvidia_contract = Stock('NVDA', 'SMART', 'USD')

# 获取过去五年的日线数据
end_date = ''  # 留空表示获取最新数据
duration = '5 Y'  # 过去五年
bar_size = '1 day'  # 日线数据
bars = ib.reqHistoricalData(
    nvidia_contract,
    endDateTime=end_date,
    durationStr=duration,
    barSizeSetting=bar_size,
    whatToShow='TRADES',
    useRTH=True
)

# 将数据转换为字典列表
data = []
for bar in bars:
    bar_data = {
        'date': bar.date.strftime('%Y-%m-%d'),
        'open': bar.open,
        'high': bar.high,
        'low': bar.low,
        'close': bar.close,
        'volume': bar.volume
    }
    data.append(bar_data)

# 保存为JSON文件
with open('/Users/lijingyi/ByteBuddies/nvidia_data.json', 'w') as f:
    json.dump(data, f, indent=4)

# 断开连接
ib.disconnect()