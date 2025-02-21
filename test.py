from bs4 import BeautifulSoup
from langchain.text_splitter import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from langchain_core.documents import Document
import json

# 指定 Markdown 文件路径
markdown_file_path = "earnings_md/NVDA-2023-Q2-10Q.md"

# 读取 Markdown 文件内容
with open(markdown_file_path, "r", encoding="utf-8") as file:
    markdown_document = file.read()

# 定义需要提取的标题层级
headers_to_split_on = [
    ("#", "Header 1"),
    ("##", "Header 2"),
    ("###", "Header 3"),
]

# 初始化 MarkdownHeaderTextSplitter
markdown_splitter = MarkdownHeaderTextSplitter(
    headers_to_split_on=headers_to_split_on
)

# 分割 Markdown 文档
md_header_splits = markdown_splitter.split_text(markdown_document)

# 提取并解析 HTML 表格
def extract_html_tables(markdown_text):
    soup = BeautifulSoup(markdown_text, "lxml")
    tables = soup.find_all("table")
    extracted_tables = []

    for table in tables:
        # 提取表头
        headers = []
        header_row = table.find("tr")
        if header_row:
            headers = [th.get_text(strip=True) for th in header_row.find_all("th")]

        # 提取表格数据
        rows = []
        for row in table.find_all("tr")[1:]:  # 跳过表头
            cells = row.find_all(["td", "th"])
            row_data = [cell.get_text(strip=True) for cell in cells]
            rows.append(row_data)

        # 将表头和行数据组合成一个字典
        table_data = {
            "headers": headers,
            "rows": rows
        }
        extracted_tables.append(table_data)

    return extracted_tables

# 最终输出的文档列表
documents = []

# 遍历每个标题下的内容
for split in md_header_splits:
    title = split.metadata.get("Header 1", "") or split.metadata.get("Header 2", "") or split.metadata.get("Header 3", "")
    content = split.page_content

    # 提取内容中的表格
    tables = extract_html_tables(content)

    if tables:
        # 如果内容中有表格，将每个表格作为一个单独的文档
        for table in tables:
            document = {
                "title": title,
                "type": "table",
                "content": table
            }
            documents.append(document)
    else:
        # 如果内容中没有表格，将文本内容作为一个文档
        document = {
            "title": title,
            "type": "text",
            "content": content
        }
        documents.append(document)

# 进一步分割文本和表格以符合最大令牌长度要求
text_splitter = RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=0)
lang_docs = []
max_token_size = 60

def get_table_token_length(table):
    table_str = json.dumps(table)
    return len(table_str.split())

for doc in documents:
    if doc['type'] == 'text':
        # 对文本内容进行进一步分割
        text_chunks = text_splitter.split_text(str(doc['content']))
        for chunk in text_chunks:
            # print('chunk length', len(chunk))
            document = Document(
                page_content=chunk,
                metadata={"title": doc['title'], "type": doc['type']}
            )
            lang_docs.append(document)
    else:
        # 处理表格数据
        table = doc['content']
        table_token_length = get_table_token_length(table)
        
        if table_token_length <= max_token_size:
            # print('table chunk length', table_token_length)
            # 表格大小未超过限制，直接添加
            document = Document(
                page_content=str(table),
                metadata={"title": doc['title'], "type": doc['type']}
            )
            lang_docs.append(document)
        else:
            # 表格大小超过限制，按行分割表格
            headers = table["headers"]
            rows = table["rows"]
            current_rows = []
            for row in rows:
                new_table = {
                    "headers": headers,
                    "rows": current_rows + [row]
                }
                new_table_token_length = get_table_token_length(new_table)
                if new_table_token_length <= max_token_size:
                    current_rows.append(row)
                else:
                    # 超过限制，将当前部分作为一个新表格
                    partial_table = {
                        "headers": headers,
                        "rows": current_rows
                    }
                    # print('table chunk length', len(str(partial_table)))
                    document = Document(
                        page_content=str(partial_table),
                        metadata={"title": doc['title'], "type": doc['type']}
                    )
                    lang_docs.append(document)
                    current_rows = [row]

            # 处理最后一部分表格
            if current_rows:
                partial_table = {
                    "headers": headers,
                    "rows": current_rows
                }
                # print('table chunk length', len(str(partial_table)))
                document = Document(
                    page_content=str(partial_table),
                    metadata={"title": doc['title'], "type": doc['type']}
                )
                lang_docs.append(document)

print('数据切片完成')