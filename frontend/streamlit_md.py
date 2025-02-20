import streamlit as st
import random
import time

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Let's start chatting! 👇"}]

# 初始化关键词索引
if "keyword_index" not in st.session_state:
    st.session_state.keyword_index = 0

showPdf = False
for message in st.session_state.messages:
    if message["role"] == "user" and message["content"] == "pdf":
        showPdf = True
    if message["role"] == "user" and message["content"] == "exitpdf":
        showPdf = False

messageContainer = None
inputContainer = None
if showPdf:
    col1, col2 = st.columns([3, 2])
    messageContainer = col1.container(height=400)
    inputContainer = col1.container()
    with col2.container():
        # 按钮放在顶部
        col3, col4 = st.columns(2)
        if col3.button("上一个关键词"):
            if st.session_state.keyword_index > 0:
                st.session_state.keyword_index -= 1

        if col4.button("下一个关键词"):
            keywords = ["LLM", "Domain Experts", "Integration", "Methodology", "Approach", "Solution", "Results", "Findings", "Analysis", "Conclusion", "Summary", "Future Work"]
            if st.session_state.keyword_index < len(keywords) - 1:
                st.session_state.keyword_index += 1

        # Assuming the PDF has been converted to Markdown and stored in a variable
        markdown_content = """
        # NeurIPS 2023 Paper

        ## Abstract
        This is a **sample** abstract for the NeurIPS 2023 paper. The paper discusses the integration of LLMs with domain experts.

        ## Introduction
        In this section, we introduce the problem and the proposed solution. **Keywords**: LLM, Domain Experts, Integration.

        ## Methodology
        The methodology section explains the approach taken to solve the problem. **Keywords**: Methodology, Approach, Solution.

        ## Results
        The results section presents the findings of the study. **Keywords**: Results, Findings, Analysis.

        ## Conclusion
        The conclusion summarizes the key points and future work. **Keywords**: Conclusion, Summary, Future Work.
        """

        keywords = ["LLM", "Domain Experts", "Integration", "Methodology", "Approach", "Solution", "Results", "Findings", "Analysis", "Conclusion", "Summary", "Future Work"]

        # 先移除所有高亮
        for keyword in keywords:
            markdown_content = markdown_content.replace(f"<mark>{keyword}</mark>", keyword)

        # 高亮当前索引对应的关键词
        current_keyword = keywords[st.session_state.keyword_index]
        marked_content = markdown_content.replace(current_keyword, f"<mark id='current-keyword'>{current_keyword}</mark>")

        # 创建一个可滚动的容器
        scrollable_container = f"""
        <div id="scrollable-container" style="height: 500px; overflow-y: auto; border: 1px solid #ccc; padding: 10px;">
            {marked_content}
        </div>
        """

        # 滚动到当前高亮的关键词位置
        js = """
        <script>
            function scrollToKeyword() {
                var scrollableContainer = document.getElementById('scrollable-container');
                var keywordElement = document.getElementById('current-keyword');
                if (scrollableContainer && keywordElement) {
                    var containerHeight = scrollableContainer.clientHeight;
                    var keywordOffsetTop = keywordElement.offsetTop;
                    var scrollTop = keywordOffsetTop - (containerHeight / 2);
                    scrollableContainer.scrollTop = scrollTop;
                }
            }
            window.onload = scrollToKeyword;
        </script>
        """

        # Display the Markdown content in a scrollable container
        st.markdown(scrollable_container, unsafe_allow_html=True)
        st.components.v1.html(js, height=0)

else:
    messageContainer = st.container()
    inputContainer = st.container()

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with messageContainer.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := inputContainer.chat_input("What is up?", disabled=False):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message in chat message container
    with messageContainer.chat_message("user"):
        st.markdown(prompt)
    # Display assistant response in chat message container
    with messageContainer.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        assistant_response = random.choice(
            [
                "Hello there! How can I assist you today?",
                "Hi, human! Is there anything I can help you with?",
                "Do you need help?",
            ]
        )
        st.session_state.messages.append({"role": "assistant", "content": ""})
        # Simulate stream of response with milliseconds delay
        for chunk in assistant_response.split():
            full_response += chunk + " "
            time.sleep(0.1)
            # Add a blinking cursor to simulate typing
            message_placeholder.markdown(full_response + "▌")
            st.session_state.messages[len(st.session_state.messages) - 1] = {"role": "assistant", "content": full_response}
        message_placeholder.markdown(full_response)
    st.rerun()