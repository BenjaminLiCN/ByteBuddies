from dotenv import load_dotenv
from openai import OpenAI
import os
import sys
import time
import datetime


class DeepSeekChat:
    # define the base model(DeepSeek - R1) and the api key
    def __init__(self, api_key=None, base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"):
        load_dotenv()
        self.api_key = 'sk-b607e13505ac4ce3bf0a656644564b92'
        if self.api_key is None:
            return "ERROR: CANNOT FIND A VALID API KEY!"
        self.client = OpenAI(api_key=self.api_key, base_url=base_url)
        self.sys_intention_ext_prompt = """As a professional proficient in financial report analysis, you are attempting to understand my question. Please note that if the question is posed in English, you must think and respond in English!

First, we define the following four action spaces:
["retrieval", "answering", "clarify", "cannot_answer"], with the specific meanings as follows:
- **"retrieval"**: Indicates that the current question involves financial reports or candlestick charts (K-line charts), requiring you to search for relevant information to answer. Note that regardless of the current time, any question involving financial reports or candlestick charts requires searching for the most accurate information to support your response.
- **"answering"**: Indicates that the current question does not involve financial reports and can be answered based on your existing knowledge without consulting the latest information.
- **"clarify"**: Indicates that the details provided by the user are insufficient to gather enough information. For example, in scenarios such as analyzing growth or forecasting revenue, you may need a specific time frame. If the user's question involves simulating investment returns but does not provide a specific time frame for analysis, you need to proactively interact with the user to obtain the required details.
- **"cannot_answer"**: Indicates that the current question may involve social harm and cannot be answered.

You are required to complete the following four tasks:
1. Understand the core question(s) I am asking based on the context. If multiple core questions are present in a single query, break them down separately.
2. Translate the identified core question(s) into English.
3. Based on the translated core question(s), analyze whether there are keywords that can help filter searches. If keywords exist, extract all of them; otherwise, set the corresponding attribute to an empty element. The keywords to identify include:
    - **Year (year)**: A LIST attribute where each element is a STRING in the format "YYYY" (e.g., "2024").
    - **Quarter (quarter)**: A LIST attribute where each element is a STRING in the format "Qx" (e.g., "Q1" for the first quarter).
    - **Start date of the analysis period (begin_date)**: A STRING attribute in the format "YYYY-MM-DD" (e.g., "2024-01-01").
    - **End date of the analysis period (end_date)**: A STRING attribute in the format "YYYY-MM-DD" (e.g., "2024-01-01").
4. Provide the action you want to execute for the question. Note that only one action is allowed to appear independently, and multiple actions cannot coexist.

Please note:
The latest candlestick chart data in the database is as of 2025-02-14.

Before outputting, double-check that all task requirements are met. Finally, strictly follow the output rules based on the chosen action:
1) If the action is "retrieval," output strictly in the following format:
{"query": ["Translated core question(s)"], "keywords": {"year": [], "quarter": [], "begin_date": "", "end_date": ""}, "action": "retrieval"}
2) If the action is "answering," "clarify," or "cannot_answer," provide your response directly in natural language, DO NOT output a JSON format.

Please ensure strict adherence to the format and rules, avoiding any extra content.
"""

        self.intention_ext_prompt = """
Current Time：{time}

<query>
{query}
</query>
"""

        self.sys_generation_prompt = """You are a professional expert in financial statement analysis. I will provide you with my current question (please note, if the question is in English, please respond in English!) along with potentially relevant financial statement reference information. Please respond to my question based on the reference information provided.

Please pay attention to the following requirements:

1. **The latest date of data in the K-line chart is up to 2024-02-14.**

2. **First, analyze whether the financial statement information provided is relevant to the question, and only refer to relevant content in your response;**

   2.1) **If the financial statement information is not related to my question, to ensure the accuracy of the output, please directly and explicitly inform me that this question cannot be answered.**

3. **In your response, where you have referred to the financial statement information, please strictly generate hyperlinks in the format `[index](file_name)`, where `index` helps me identify the specific content you referenced, and `file_name` is the corresponding financial statement title of the `index`, to enhance credibility.**

4. **Please determine the language of your response based on the main language of my question. If the main language of my question is Chinese, please reply to me in Chinese; otherwise, please respond in English.**

5. **Please appropriately use markdown formatting to ensure the readability of your answer. For data prediction and analysis questions, present data results in the form of tables as much as possible to enhance readability.**
"""

        self.generation_prompt = """
Current Time：{time}

<query>
{query}
</query>

<financial_report_references>
{f_references}
</financial_report_references>
"""

    # define the main calling function, return the full response at once
    def calling(self, messages):
        completion = self.client.chat.completions.create(
            model="deepseek-r1",
            messages=messages,
            # stream=True
        )
        return completion.choices[0].message.content

        # full_response = ""
        # for chunk in completion:
        #     if not chunk.choices:
        #         continue
        #     delta = chunk.choices[0].delta
        #     if delta.content is not None:
        #         full_response += delta.content

        # return full_response
    def calling_with_streaming_response(self, messages):
        completion = self.client.chat.completions.create(
            model="deepseek-r1",
            messages=messages,
            stream=True
        )

        is_thinking = False
        has_sent_think = False
        think_st_cnt = 0
        think_end_cnt = 0
        # catch the stream output
        for chunk in completion:
            if not chunk.choices:
                continue
            
            delta = chunk.choices[0].delta

            if hasattr(delta, 'reasoning_content') and (delta.reasoning_content is not None or delta.content == ''):
                if not has_sent_think and think_st_cnt == 0:
                    yield "<think>\n"
                    think_st_cnt += 1
                    has_sent_think = True
                    is_thinking = True
                if delta.reasoning_content is not None:
                    yield delta.reasoning_content
            elif not hasattr(delta, 'reasoning_content') or delta.reasoning_content is None:
                if is_thinking and think_end_cnt == 0:
                    yield "\n</think>\n\n"
                    think_end_cnt += 1
                    is_thinking = False
                    has_sent_think = False
                if delta.content is not None:
                    yield delta.content

        if is_thinking:
            yield '</think>'
    def get_intention_extarctor_prompt(self, messages, query, time):
        input_query = self.intention_ext_prompt.format(time=time, query=query)
        tmp_mes = [{"role": "system", "content": self.sys_intention_ext_prompt}]
        for val in messages:
            tmp_mes.append(val)
        tmp_mes.append({"role": "user", "content": input_query})
        return tmp_mes

    def generate_final_answer(self, messages, query, time, f_references):
        input_query = self.generation_prompt.format(time=time, query=query, f_references=f_references)
        tmp_mes = [{"role": "system", "content": self.sys_generation_prompt}]
        for val in messages:
            tmp_mes.append(val)
        tmp_mes.append({"role": "user", "content": input_query})
        return tmp_mes

def process_final_query(history, retrieved_data):
    chat = DeepSeekChat()
    current_time = datetime.datetime.now()
    messages = chat.generate_final_answer(messages=history, query=retrieved_data['query'], time=current_time, f_references=retrieved_data['f_references'])
    response = chat.calling_with_streaming_response(messages)
    return response
def process_query(history, query):
    chat = DeepSeekChat()
    current_time = datetime.datetime.now()
    messages = chat.get_intention_extarctor_prompt(messages=history, query=query, time=current_time)
    response = chat.calling_with_streaming_response(messages)
    return response

# example
# if __name__ == "__main__":
#     chat = DeepSeekChat()
#     current_time = datetime.datetime.now()
#     query = "2024年第三季度nvidia的营收如何，我现在买nvidia的股票能有收益吗？"
#     from retrieval import query_from_frontend
#     messages = query_from_frontend(query)
#     print(messages)
    # messages = chat.get_intention_extarctor_prompt(messages=[], query=query, time=current_time)
    # print(messages)
