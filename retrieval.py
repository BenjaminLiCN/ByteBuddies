from langchain_elasticsearch import ElasticsearchStore
from uuid import uuid4
from langchain_core.documents import Document
from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings
from elasticsearch import Elasticsearch
from llm_calling import process_final_query, process_query
import json
from collections import Counter
from datetime import datetime
import time

index_name = "langchain-demo"
table_index_name = "table_caption_embedding"

client = NVIDIAEmbeddings(
    model="nvidia/llama-3.2-nv-embedqa-1b-v2",
    api_key="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",
    truncate="NONE",
)

vector_store = ElasticsearchStore(
    index_name, embedding=client, es_url="http://localhost:9200"
)
table_vector_store = ElasticsearchStore(
    table_index_name, embedding=client, es_url="http://localhost:9200"
)

#{"query": ["What was NVIDIA's revenue in the third quarter of 2024?", "Can I make a profit by buying NVIDIA stock now?"], "keywords": {"year": ["2024"], "quarter": ["Q3"]}, "action": ["retrieval", "build_graph"]}
def kline_point():
    return kline_point
def most_common_file_name(query):
    file_names = [ref["metadata"]["file_name"] for ref in query["f_references"]]
    print('file_names', file_names)
    count = Counter(file_names)
    # 找到出现次数最多的file_name
    most_common = count.most_common(1)  # 返回一个列表，里面是一个元组 (file_name, 次数)
    print('most_common', most_common)
    return most_common[0] if most_common else []
def final_query(history, query):

    print('history')
    # print(f"final_query 函数中获取的 query: {query}")  # 增加调试信息
    # print('final query', query)
    process_final_query_time = time.time()
    final_result = process_final_query(history, query)
    print(f"process_final_query耗时: {time.time() - process_final_query_time:.4f} 秒")
    return final_result
def query_from_frontend(data):
    
    print('query_from_frontend', data)
    # {'query': ["What was NVIDIA's revenue in the third quarter of 2024?", 'Should I buy NVIDIA stock now to make a profit?'], 'keywords': {'year': [2024], 'quarter': ['Q3']}, 'action': ['retrieval', 'build_graph']}
    search_pre_filter = []
    if len(data['keywords']['year']) > 0:
        search_pre_filter.append({"terms": {"metadata.year": data['keywords']['year']}})
    if len(data['keywords']['quarter']) > 0:
        search_pre_filter.append({"terms": {"metadata.quarter": [s.replace("Q", "") for s in data['keywords']['quarter']]}})
    similarity_search_time = time.time()
    results = vector_store.similarity_search(
        query=data['query'][0],
        k=20,
        filter=search_pre_filter,
    )
    #print(f"doc_result{results}")
    table_results = table_vector_store.similarity_search(
        query=data['query'][0],
        k=3,
        filter=search_pre_filter,
    )
    #print(f"table_results{table_results}")
    print(f"similarity_search耗时: {time.time()-similarity_search_time:.4f} 秒")
    docs = []
    keywords = []
    for doc in results:
        # 获取 metadata
        metadata = doc.metadata
        # 获取 page_content
        print(metadata)
        page_content = doc.page_content
        file_name = doc.metadata['file_name']
        docs.append({"metadata":metadata, "page_content":page_content, "file_name": file_name})
        keywords.append(page_content)
    for table_doc in table_results:
        docs.append({"metadata":table_doc.metadata, "page_content":table_doc.page_content})
    global kline_point
    kline_point = []
    if len(data['keywords']['begin_date'])>0 or len(data['keywords']['end_date'])>0:
        for point in get_k_line_points(data['keywords']['begin_date'], data['keywords']['end_date']):
            data['query'].append(point)
            kline_point.append(point)
    
    query = {"query": data['query'], "f_references": docs}
    print(f"keywords_from_frontend query{keywords}")
    return (keywords,query)
    #[Document(metadata={'year': '2022', 'type': 'text', 'quarter': '2', 'page_idx': 24, 'table_footnote': '', 'table_caption': ''}, page_content='Headquartered in Santa Clara, California, NVIDIA was incorporated in California in April 1993 and reincorporated in Delaware in April 1998.'), Document(metadata={'year': '2022', 'type': 'text', 'quarter': '2', 'page_idx': 39, 'table_footnote': '', 'table_caption': ''}, page_content='Investor Relations: NVIDIA Corporation, 2788 San Tomas Expressway, Santa Clara, CA 95051.')]

def is_valid_json(input_str):
    try:
        data = json.loads(input_str)
        return True, data
    except json.JSONDecodeError:
        return False, None
        
def get_k_line_points(begin_date_str: str, end_date_str: str):
    # 定义最小日期和最大日期
    min_date = datetime.min
    max_date = datetime.max

    # 将非空日期字符串转换为 datetime 对象
    begin_date = datetime.strptime(begin_date_str, '%Y-%m-%d') if len(begin_date_str)>0 else min_date
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d') if len(end_date_str)>0 else max_date

    # 打开并读取 JSON 文件
    with open('5_year_json/nvidia_data.json', 'r', encoding='utf-8') as file:
        data = json.load(file)

    # 过滤并生成符合条件的点
    for point in data:
        point_date = datetime.strptime(point['date'], '%Y-%m-%d')
        if begin_date <= point_date <= end_date:
            yield point