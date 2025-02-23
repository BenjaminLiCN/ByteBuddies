#处理表格的
import json
import os
from uuid import uuid4

from elasticsearch import Elasticsearch
from langchain.text_splitter import CharacterTextSplitter
from langchain_elasticsearch import ElasticsearchStore
from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings

index_name = "table_caption_embedding"
# 初始化向量模型
client = NVIDIAEmbeddings(
    model="nvidia/llama-3.2-nv-embedqa-1b-v2",
    # api_key用自己的https://build.nvidia.com/nvidia/nv-embedqa-e5-v5?snippet_tab=LangChain
    api_key="",
    truncate="NONE",
)
# 假设 JSON 文件名为 data.json，你可以根据实际情况修改文件名
folder_path = 'earnings_json/'
lang_docs = []

# 初始化文本分割器
text_splitter = CharacterTextSplitter(
    chunk_size=5000,  # 每个块的最大字符数，你可以根据需要调整
    chunk_overlap=500,  # 块之间的重叠字符数，你可以根据需要调整
    separator="."
)

for filename in os.listdir(folder_path):
    # 检查文件是否符合命名规则
    if filename.startswith('NVDA-'):
        # 构建原文件的完整路径
        file_path = os.path.join(folder_path, filename)

        # 打开并读取JSON文件
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)

        # 遍历JSON数组中的每个元素
        for item in data:
            if item['type'] != 'table':
                continue
            if item['table_caption'] is None:
                continue
            if ' '.join(item['table_caption']).isspace():
                continue
            page_content = ' '.join(item['table_caption']) +' '+ ' '.join(item['table_footnote'])
            # 分割文本内容
            split_docs = text_splitter.create_documents(
                [page_content],
                metadatas=[{
                    "year": item['year'],
                    "type": item['type'],
                    "quarter": item['quarter'],
                    "page_idx": item['page_idx'],
                    "table_footnote": item.get('table_footnote', ''),
                    "table_caption": item.get('table_caption', ''),
                    "table_content": json.dumps(item['table_body']),
                    "file_name": filename.split('_')[0]
                }]
            )
            # 将分割后的文档添加到列表中
            lang_docs.extend(split_docs)

es = Elasticsearch("http://localhost:9200")
if es.indices.exists(index=index_name):
    es.indices.delete(index=index_name)
    print(f"索引 {index_name} 已删除。")


# 用向量模型初始化es来做向量存储
vector_store = ElasticsearchStore(
    index_name, embedding=client, es_url="http://localhost:9200"
)
batch_size = 100
total_docs = len(lang_docs)
#下次从6001-开始处理
for i in range(0, total_docs, batch_size):
    print("start process")
    batch_docs = lang_docs[i:i + batch_size]
    uuids = [str(uuid4()) for _ in range(len(batch_docs))]
    vector_store.add_documents(documents=batch_docs, ids=uuids)
    progress = min((i + batch_size), total_docs) / total_docs * 100
    print(f"已存储 {min((i + batch_size), total_docs)} 个文档，进度: {progress:.2f}%")
