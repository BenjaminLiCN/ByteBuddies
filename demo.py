import json
import hashlib
from typing import List
from sentence_transformers import SentenceTransformer
import chromadb
from openai import OpenAI

# 初始化OpenAI客户端
openAIClient = OpenAI(
    api_key="",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

# 加载预训练的句子嵌入模型
model = SentenceTransformer('all-mpnet-base-v2')

# 加载JSON数据
with open('pte_data.json', 'r', encoding='utf-8') as f:
    pte_data = json.load(f)

# 初始化ChromaDB客户端
client = chromadb.Client()
collection = client.create_collection(name="pte_collection")

# 题型映射表
QUESTION_MAPPING = {
    "RA": "Read Aloud",
    "RS": "Repeat Sentence",
    "DI": "Describe Image",
    "RL": "Retell Lecture",
    "ASQ": "Answer Short Question"
}

def generate_id(text: str) -> str:
    """生成唯一ID"""
    return hashlib.md5(text.encode()).hexdigest()

def store_data_in_chromadb():
    """将JSON数据存储到ChromaDB"""
    ids = []
    embeddings = []
    metadatas = []
    documents = []

    for question_type, data in pte_data.items():
        # 处理每个题型的数据
        sections = {
            '题型介绍': 'intro',
            '答题技巧': 'skill',
            '答题时长': 'time'
        }
        
        for section_name, section_key in sections.items():
            text = data[section_name]
            ids.append(generate_id(f"{question_type}_{section_key}"))
            embeddings.append(model.encode(text).tolist())
            metadatas.append({
                "question_type": question_type,
                "section": section_key,
                "content_type": "instruction"
            })
            documents.append(text)

        # 处理练习目标
        for level, goal in data['练习目标'].items():
            ids.append(generate_id(f"{question_type}_{level}_goal"))
            embeddings.append(model.encode(goal).tolist())
            metadatas.append({
                "question_type": question_type,
                "section": "goal",
                "level": level,
                "content_type": "instruction"
            })
            documents.append(goal)

        # 处理评分维度
        if '评分维度' in data:
            for dimension, description in data['评分维度'].items():
                ids.append(generate_id(f"{question_type}_{dimension}"))
                embeddings.append(model.encode(description).tolist())
                metadatas.append({
                    "question_type": question_type,
                    "section": "scoring",
                    "dimension": dimension,
                    "content_type": "criteria"
                })
                documents.append(description)

    # 批量添加数据
    collection.add(
        ids=ids,
        embeddings=embeddings,
        metadatas=metadatas,
        documents=documents
    )

def get_relevant_texts(user_input: str, question_type: str, top_k: int = 5) -> List[str]:
    """获取相关文本"""
    user_embedding = model.encode(user_input).tolist()
    results = collection.query(
        query_embeddings=[user_embedding],
        n_results=top_k,
        where={"question_type": question_type}
    )
    return [f"[来源：{m['section']}] {d}" for d, m in zip(results['documents'][0], results['metadatas'][0])]

def generate_prompt(context: List[str], question: str, question_type: str) -> str:
    """生成提示词"""
    full_question_type = QUESTION_MAPPING.get(question_type, question_type)
    context_str = "\n".join(context)
    
    return f"""你是一名专业的PTE考试评分专家，请根据以下评分规则和考生回答进行分析：

【题型】{full_question_type}
【评分规则】
{context_str}

【考生回答】
{question}

请按以下结构用中文回答：
1. 当前问题评分维度分析（发音/流利度/内容）
2. 具体改进建议
3. 示范回答（如适用）
保持专业友好的语气，使用PTE考试专业术语。"""

def generate_answer(prompt: str) -> str:
    """生成回答"""
    try:
        response = openAIClient.chat.completions.create(
            model="qwen-plus",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=500
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"生成建议时遇到错误，请稍后再试。错误信息：{str(e)}"

def analyze_response(question_type: str, user_answer: str) -> str:
    """分析用户回答"""
    user_input = f"题目: {question_type}, 解答: {user_answer}"
    relevant_texts = get_relevant_texts(user_input, question_type)
    prompt = generate_prompt(relevant_texts, user_answer, question_type)
    return generate_answer(prompt)

if __name__ == "__main__":
    # 存储数据到ChromaDB
    store_data_in_chromadb()

    # 示例使用
    user_question_type = "RA"
    user_answer = "The bill calls for the establishment of the National Landslide Hazards Reduction Program within one year of becoming law."
    
    analysis_result = analyze_response(user_question_type, user_answer)
    print("分析结果：")
    print(analysis_result)