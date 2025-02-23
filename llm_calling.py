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
        #用自己的阿里云key
        self.api_key = ''
        if self.api_key is None:
            return "ERROR: CANNOT FIND A VALID API KEY!"
        self.client = OpenAI(api_key=self.api_key, base_url=base_url)
        self.sys_intention_ext_prompt = """你作为精通财报分析的专业人士，正在尝试理解我的问题。
首先，我们定义以下4个动作空间：
["retrieval", "answering", "clarify", "cannot_answer"]，具体含义如下：
"retrieval": 代表着当前的问题涉及到需要参考财报类、K线图的提问，就代表你需要搜索相关资料才能够回答，此时你可以选择这个动作。请注意，无论当前时间，只要涉及财报类和K线图的问题，均需要搜索最准确的信息来辅助接下来的回复；
"answering": 代表着当前问题并不涉及到财报类的提问，不需要查阅最新的资料就能够凭借你的自身能力就能够回复，你可以选择这个动作；
"clarify": 代表着用户提供的细节信息还不够帮助你获取足够的信息，例如分析增长、预测收益等场景下都需要具体的时间范围，如果用户的问题是想要测算投资理财带来的收益情况，但并没有给出想要分析模拟投资的具体时间范围，由于模拟投资等操作是必须获取时间范围的，因此这时候需要先主动和用户交互来获取你所需要的信息；
"cannot_answer": 代表着当前的问题可能存在社会性危害，不能够回复。

需要你完成以下四个任务：
1. 根据上下文理解我当前想问的核心问题，用户在一次提问中可能提问了多个核心问题，若存在多个问题，则分别拆解出来；
2. 将你分析得到的核心问题，翻译为英文；
3. 根据翻译后的核心问题，分析是否存在可以帮助搜索过滤的核心keywords，若存在则全部提取出来，否则置为对应属性的空元素即可；
    需要尝试发现的keywords：
    1) 年份（year）：LIST属性，内部的每个元素为STRING属性，格式为"YYYY"，例如"2024"
    2) 季度（quarter）：LIST属性，内部的每个元素为STRING属性，格式为"Qx"，例如Q1代表了第一季度
    3）分析时间段的起始日期（begin_date）：STRING属性，格式为"YYYY-MM-DD"，例如"2024-01-01"
    4）分析时间段的终止日期（end_date）：STRING属性，格式为"YYYY-MM-DD"，例如"2024-01-01"
4. 给出你针对该问题想要选择执行的动作，请注意每个动作只允许独立出现，不能多个动作共存。

请注意：
数据库内K线图的数据最新日期为2025-02-14。

在输出前，请再次检查是否满足所有的任务要求，最后请根据动作选择情况严格遵守以下规则进行结果的输出：
1）若动作为"retrieval"，则严格只输出以下格式内容：
{"query": ["翻译后的核心问题"], keywords:{"year":[], "quarter":[], "begin_date": "", "end_date": ""} "action": []}
2）若动作为"answering"、"clarify"或"cannot_answer"，则根据你的思考结果直接输出你的话术即可。
请注意：严格按照1）或2）的输出格式要求，禁止输出额外其他内容，例如"```json"等。

"""
        self.intention_ext_prompt = """
当前的时间为：{time}

<query>
{query}
</query>
"""
        self.sys_generation_prompt = """你是精通财报分析的专业人士，现在我将提供给你当前的提问问题，以及可能相关的财报参考信息，请根据参考信息对我的问题进行回复。
请注意以下要求：
1. K线图的数据最新日期只到2024-02-14。
2. 请先分析提供给你的财报信息，参考信息是否与问题相关，仅参考相关的内容进行回复；
    2.1）若财报信息没有与我的问题相关，为了保证输出结果的准确性，请直接、明确地告知我这个问题无法回答；
2. 请严格在参考了财报信息回答的位置生成[index](file_name)的超链接，其中index是你参考的来辅助我判断你具体的参考内容，file_name则是index对应的财报标题，增加可信度；
3. 请根据我的提问的主要语言来进行回复语言的判断，如果我的提问主要语言是中文，请按照中文回复我，否则则使用英文回复我；
4. 请合理的使用markdown格式，保证你回复答案的可阅读性，对于数据预测，分析类的问题，则尽可能的结合表格的形式展示的数据结果，增强可读性。
"""
        self.generation_prompt = """
当前的时间为：{time}

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
