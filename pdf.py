import fitz  # PyMuPDF

def find_text_in_pdf(pdf_path, search_text):
    # 打开PDF文件
    doc = fitz.open(pdf_path)
    
    # 遍历每一页
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text_instances = page.search_for(search_text)
        
        # 如果找到匹配的文字
        if text_instances:
            print(f"Text found on page {page_num + 1}")
            for inst in text_instances:
                print(f"Location: {inst}")
        else:
            print(f"Text not found on page {page_num + 1}")

# 使用示例
pdf_path = "earnings/NVDA-2022-Q1-10Q.pdf"
search_text = "Wdesk Fidelity Content"
find_text_in_pdf(pdf_path, search_text)