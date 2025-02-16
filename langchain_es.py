from langchain_elasticsearch import ElasticsearchStore
from uuid import uuid4
from langchain_core.documents import Document
from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings
# 参考：https://python.langchain.com/docs/integrations/vectorstores/elasticsearch/#query-directly
# 初始化向量模型
client = NVIDIAEmbeddings(
  model="nvidia/nv-embedqa-e5-v5",
    #api_key用自己的https://build.nvidia.com/nvidia/nv-embedqa-e5-v5?snippet_tab=LangChain
  api_key="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",
  truncate="NONE",
  )
# 用向量模型初始化es来做向量存储
vector_store = ElasticsearchStore(
    "langchain-demo", embedding=client, es_url="http://localhost:9200"
)
# 造2条数据
document_1 = Document(
    page_content="I had chocalate chip pancakes and scrambled eggs for breakfast this morning.",
    metadata={"source": "tweet"},
)
document_2 = Document(
    page_content="The weather forecast for tomorrow is cloudy and overcast, with a high of 62 degrees.",
    metadata={"source": "news"},
)
documents = [
    document_1,
    document_2,
]
uuids = [str(uuid4()) for _ in range(len(documents))]
# 插入数据到es
vector_store.add_documents(documents=documents, ids=uuids)
# 查询数据
results = vector_store.similarity_search(
    query="LangChain provides abstractions to make working with LLMs easy",
    k=2,
    filter=[{"term": {"metadata.source.keyword": "tweet"}}],
)
for res in results:
    print(f"* {res.page_content} [{res.metadata}]")