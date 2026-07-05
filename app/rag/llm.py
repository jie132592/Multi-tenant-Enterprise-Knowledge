"""
LLM 调用模块

封装 ChatGPT / 智谱 ChatGLM 调用
"""
from typing import List, Tuple, Optional

from config import settings


class LLMModel:
    """LLM模型"""
    _model = None

    @classmethod
    def get_model(cls, streaming: bool = False):
        """获取LLM大模型"""
        try:
            from langchain_openai import ChatOpenAI
            # 判断是否配置了智谱API密钥，优先使用智谱大模型
            if settings.ZHIPU_API_KEY:
                # 去除地址末尾多余斜杠，防止拼接地址出错
                base_url = settings.ZHIPU_BASE_URL.rstrip("/")
                return ChatOpenAI(
                    model=settings.ZHIPU_CHAT_MODEL,
                    openai_api_key=settings.ZHIPU_API_KEY,  # 智谱密钥
                    openai_api_base=base_url,  # 智谱接口代理地址（兼容OpenAI格式）
                    temperature=0.7,  # 温度：0精准死板，1自由发散
                    streaming=streaming  # 是否开启流式返回
                )
            else:
                # 没有智谱密钥，使用原生OpenAI/兼容OpenAI接口的第三方大模型
                base_url = settings.OPENAI_BASE_URL.rstrip('/')
                return ChatOpenAI(
                    model=settings.LLM_MODEL,
                    openai_api_key = settings.OPENAI_API_KEY,
                    openai_api_base = base_url,
                    temperature = 0.7,
                    streaming = streaming
                )
        except Exception as e:
            print(f"Failed to load LLM model: {e}")
            # 初始化模型失败，返回空
            return None

    @classmethod
    def chat_stream(cls, messages: List[dict]):
        model = cls.get_model(streaming=True)
        if model is None:
            return

        try:
            from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
            langchain_messages = []
            for msg in messages:
                if msg["role"] == "system":
                    langchain_messages.append(SystemMessage(content=msg["content"]))
                elif msg["role"] == "user":
                    langchain_messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    langchain_messages.append(AIMessage(content=msg["content"]))

            for chunk in model.stream(langchain_messages):
                if chunk.content:
                    yield chunk.content
        except Exception as e:
            print(f"聊天失败: {e}")
            # 异常时向前端返回统一提示文案
            yield "抱歉，AI 服务暂时不可用。"

    @classmethod
    def chat(cls, messages: List[dict]) -> Tuple[Optional[str], Optional[dict]]:
        """非流式"""
        model = cls.get_model(streaming=False)
        if model is None:
            return None, None
        try:
            from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
            langchain_messages = []
            for msg in messages:
                if msg["role"] == "system":
                    langchain_messages.append(SystemMessage(content=msg["content"]))
                elif msg["role"] == "user":
                    langchain_messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    langchain_messages.append(AIMessage(content=msg["content"]))

            response = model.invoke(langchain_messages)

            usage = None
            # 提取token消耗统计（输入token、输出token、总token，用于计费统计）
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                usage = {
                    "prompt_tokens": response.usage_metadata.get("input_tokens", 0),
                    "completion_tokens": response.usage_metadata.get("output_tokens", 0),
                    "total_tokens": response.usage_metadata.get("total_tokens", 0),
                }

            return response.content, usage
        except Exception as e:
            print(f"Chat failed: {e}")
            return None, None

    @classmethod
    def chat_with_rag(
            cls,
            query: str, # 用户原始提问
            content_chunk: List[dict], # Qdrant检索出来的相似向量
            history: List[dict], # 历史对话记录
    ) -> Tuple[Optional[str], Optional[dict]]:
        """带RAG知识库检索的问答，自动拼接参考文档、构建提示词，调用普通chat接口"""
        # 遍历检索结果，把段落文本拼接成参考文档文本
        context = "\n\n".join([
            f"【文档{i+1}】{chunk['payload']['content']}"
            for i, chunk in enumerate(content_chunk)
        ])

        # 系统提示词：约束AI只能基于提供的知识库内容回答，不能编造
        system_prompt = f"""你是一个专业的知识库问答助手。根据以下参考文档，直接回答用户问题。

参考文档：
{context}

要求：
1. 直接从参考文档中提取相关信息回答用户问题
2. 如果文档中有明确答案，直接给出答案
3. 如果文档中没有相关信息，回答"抱歉，我在知识库中没有找到相关信息"
4. 回答要简洁准确，直接使用文档中的原文"""
        # 初始化消息列表，第一条是系统prompt
        messages = [{"role": "system", "content": system_prompt}]
        # 拼接历史对话，只保留最近6轮，防止上下文超长超限
        if history:
            for msg in history[-6:]:
                messages.append({"role": msg["role"], "content": msg["content"]})
        # 追加当前用户提问
        messages.append({"role": "user", "content": query})

        return cls.chat(messages)