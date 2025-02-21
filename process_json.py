import os
import json
from bs4 import BeautifulSoup

# 指定原文件夹路径
folder_path = 'jsons/'
# 指定新文件夹路径
new_folder_path = 'jsons_processed/'

# 如果新文件夹不存在，则创建它
if not os.path.exists(new_folder_path):
    os.makedirs(new_folder_path)

def extract_html_tables(markdown_text):
    try:
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
    except Exception as e:
        # 打印错误信息
        print(f"Error occurred in extract_html_tables: {e}")
        
        return []

# 遍历文件夹中的所有文件
for filename in os.listdir(folder_path):
    # 检查文件是否符合命名规则
    if filename.startswith('NVDA-'):
        # 提取年份和季度信息
        parts = filename.split('-')
        year = parts[1]
        quarter = parts[2][1]

        # 构建原文件的完整路径
        file_path = os.path.join(folder_path, filename)

        # 构建新文件的完整路径
        new_file_path = os.path.join(new_folder_path, filename)

        # 打开并读取JSON文件
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)

        # 遍历JSON数组中的每个元素
        for item in data:
            # 添加year和quarter键
            item['year'] = year
            item['quarter'] = quarter
            if item['type'] == 'table':
                if 'table_body' in item:
                    tables = extract_html_tables(item['table_body'])
                    item['table_body'] = "" if len(tables) == 0 else tables[0]
                else:
                    item['table_body'] = ""

        # 将修改后的数据写回新文件
        with open(new_file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=4)

        print(f"Processed {filename} successfully and saved to {new_file_path}.")


            # document = Document(
            #         page_content=str(item['table_body']),
            #         metadata={"year": item['year'], "type": item['type'], "quarter": item['quarter'], "page_idx": item['page_idx'], "table_footnote": item['table_footnote'], "table_caption": item['table_caption'] }
            #     )
            #     lang_docs.append(document)
            # else:
            #     document = Document(
            #         page_content=str(item['text']),
            #         metadata={"year": item['year'], "type": item['type'], "quarter": item['quarter'], "page_idx": item['page_idx'] }
            #     )
            #     lang_docs.append(document)