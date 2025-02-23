import streamlit as st
import random
import time
import re
import json
from llm_calling import process_query
from retrieval import query_from_frontend, final_query, most_common_file_name
from streamlit_pdf_viewer import pdf_viewer


def is_valid_json(input_str):
    try:
        data = json.loads(input_str)
        return True, data
    except json.JSONDecodeError:
        return False, None


# 初始化聊天历史
if "messages" not in st.session_state:
    st.session_state.messages = []

# 初始化关键词索引
if "keyword_index" not in st.session_state:
    st.session_state.keyword_index = 0
# 初始化文件名
if "file_name" not in st.session_state:
    st.session_state.file_name = ""
# 初始化关键词
if "keywords" not in st.session_state:
    st.session_state.keywords = []
# 初始化查询
if "query" not in st.session_state:
    st.session_state.query = None

# 定义样式
css = """
<style>
#scrollable-container {
    height: 500px;
    overflow-y: auto;
    border: 1px solid #ccc;
    padding: 10px;
    margin-bottom: 20px; /* 添加底部间距 */
}
/* 防止 Streamlit 为 Markdown 内容分配额外空间 */

"""

# 注入 CSS
st.markdown(css, unsafe_allow_html=True)
css = """
<style>
.think {
    background-color: #f0f0f0;
    padding: 10px;
    border-radius: 5px;
    margin: 5px 0;
    display: inline-block;
}
</style>
"""
st.markdown(css, unsafe_allow_html=True)  # 注入CSS样式
st.markdown("""
<style>
.custom-style {
    vertical-align: top;
    line-height: 2;
    background-color: #cfe2f3;  /* 背景色 */
    font-style: italic;        /* 斜体 */
    padding: 10px;            /* 内边距 */
    border-radius: 5px;        /* 圆角 */
}
</style>
""", unsafe_allow_html=True)

showPdf = False

messageContainer = st.container()
inputContainer = st.container()

# Display chat messages from history on app rerun
with messageContainer.chat_message("assistant"):
    st.markdown("""🌟 **您好！我是您的智能财经分析助手Ecopilot**  
📊 精通全球上市公司财报解析、财务建模与投资价值挖掘  
💡 我能为您：  
✅ 多维度解读财报核心数据（财务健康度/业务增长性/行业竞争力）  
✅ 穿透式分析企业护城河与潜在风险  
✅ 结合市场动态生成投资情景推演  
🕒 目前学习了英伟达过去5年股价和财报，未来将覆盖美股/A股/港股等多市场标的全面历史股价、财报和财经新闻数据  


👇 请告诉我您关注的标的或问题，我将为您提供机构级洞察！  
""", unsafe_allow_html=True)
for message in st.session_state.messages:
    with messageContainer.chat_message(message["role"]):
        # 替换<think>标签为带有样式的HTML
        styled_content = re.sub(r'<think>(.*?)</think>', r'<div class="think">\1</div>', message["content"])
        print(f"styled_content:{styled_content}")
        st.markdown(styled_content, unsafe_allow_html=True)
query = None
# Accept user input
if prompt := st.chat_input("What is up?", disabled=False):
    # Add user message to chat history
    # Display user message in chat message container
    with messageContainer.chat_message("user"):
        st.markdown(prompt)
    need_output_gen_resp = False

    # 显示 spinner 并开始获取关键词
    with messageContainer.chat_message("assistant"):
        try:
            # 调用 query_from_frontend 函数获取关键词生成器
            keyword_generator = process_query(st.session_state.messages, prompt)
            full_keywords = ""
            display_keywords = ""
            stopDisplay = False
            with st.status("正在思考...", expanded=True) as status:
                message_placeholder = st.empty()
                for keyword in keyword_generator:
                    full_keywords += keyword
                    if '{' in keyword:
                        stopDisplay = True
                    if not stopDisplay:
                        display_keywords += keyword
                    # 使用正则表达式将 <think> 标签内的内容包裹在带有背景色的 <span> 中
                    styled_keywords = re.sub(
                        r'<think>(.*?)</think>',
                        r'<div class="custom-style">\1</div>',
                        display_keywords,
                        flags=re.DOTALL
                    )
                    # 渲染带有背景色的文本
                    message_placeholder.markdown(styled_keywords + "▌", unsafe_allow_html=True)
                st.session_state.messages.append({"role": "user", "content": prompt})
                st.session_state.messages.append(
                    {"role": "assistant", "content_type": "html", "content": styled_keywords})
                message_placeholder.markdown(styled_keywords, unsafe_allow_html=True)
                status.update(label="思考结束!", state="complete", expanded=True)
                print(f"full_keywords{full_keywords}")
                # 使用正则表达式去掉 <think> 标签及其内容
                cleaned_keywords = re.sub(r'<think>.*?</think>', '', full_keywords, flags=re.DOTALL).strip()
                print(f"intention output cleaned_keywords{cleaned_keywords}")
                is_json, data = is_valid_json(cleaned_keywords)
                print('is_json', is_json)
                if is_json:
                    print('**************')
                    try:
                        # 执行 query_from_frontend 函数
                        keywords, q = query_from_frontend(data)
                        st.session_state.query = q
                        print('前端拿到的keywords是', keywords)
                        st.session_state.keywords.extend(keywords)
                        need_output_gen_resp = True
                    except Exception as e:
                        print(f"query_from_frontend 执行出错: {e}")
                        st.error(f"处理关键词时发生错误: {e}")
        except Exception as e:
            st.error(f"获取关键词时发生错误: {e}")

    if need_output_gen_resp:
        # Display assistant response in chat message container
        with messageContainer.chat_message("assistant"):
            with st.status("回答中💭", expanded=True) as status:
                message_placeholder = st.empty()
                full_response = ""
                styled_keywords = ""
                # 调用后端函数处理用户输入，返回生成器
                print('这次前端的q', st.session_state.query)
                response_generator = final_query(st.session_state.messages, st.session_state.query)
                names = most_common_file_name(st.session_state.query)
                if len(names) > 0 and len(keywords) > 0:
                    st.session_state.file_name = f"markdowns/{names[0]}_origin.pdf"
                    print('st.session_state.file_name', st.session_state.file_name)
                    showPdf = True
                # 流式输出
                stream_output_response_time = time.time()
                for token in response_generator:
                    # 替换<think>标签为带有样式的HTML
                    full_response += token
                    styled_keywords = re.sub(
                        r'<think>(.*?)</think>',
                        r'<div class="custom-style">\1</div>',
                        full_response,
                        flags=re.DOTALL
                    )
                    # 渲染带有背景色的文本
                    # Add a blinking cursor to simulate typing
                    message_placeholder.markdown(styled_keywords + "▌", unsafe_allow_html=True)
                st.session_state.messages.append({"role": "assistant", "content": styled_keywords})
                print(f"stream_output_response耗时: {time.time() - stream_output_response_time:.4f} 秒")
                message_placeholder.markdown(styled_keywords, unsafe_allow_html=True)
                status.update(label="思考结束!", state="complete", expanded=True)
if showPdf:
    with messageContainer:
        pdf_viewer(st.session_state.file_name,scroll_to_page=0,height=1000)