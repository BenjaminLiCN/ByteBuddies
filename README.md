# ByteBuddies
第十一届英伟达Hackathon，RAG智能聊天机器人比赛，成员李敬以，陈安琪，胡涵洋，黄俊杰
# 启动方式
```
docker-compose -p byte_buddies up -d
```
# 前端依赖
```
conda install streamlit streamlit_pdf_viewer
```

在启动前需要自行安装好python需要的别的库

1. 先本地安装MinerU切片pdf成json格式，已经切好放到了earnings_json文件夹。
2. 调用ibkr券商tws api获得英伟达过去5年k线图，存入5_year_json文件夹
3. 启动es数据库
3. 调用embedding_table.py和embedding_text.py进行数据切片
4. 前端启动
```
streamlit run Ecopilot.py
```
