#!/usr/bin/env python3
"""
智能行业知识问答系统 - DeepSeek大模型客户端
提供DeepSeek模型的统一接口，支持文本生成、知识问答和内容分析
"""

import os
import json
import asyncio
import aiohttp
from typing import Dict, List, Any, Optional, Union, AsyncGenerator
from dataclasses import dataclass, asdict
from datetime import datetime
import logging
from enum import Enum

# OpenAI兼容接口
import openai

class ModelType(Enum):
    """模型类型枚举"""
    DEEPSEEK_CHAT = "deepseek-chat"
    DEEPSEEK_CODER = "deepseek-coder"
    DEEPSEEK_67B = "deepseek-67b-chat"

class MessageRole(Enum):
    """消息角色枚举"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"

@dataclass
class ChatMessage:
    """聊天消息"""
    role: MessageRole
    content: str
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
            
    def to_dict(self) -> Dict[str, str]:
        return {
            "role": self.role.value,
            "content": self.content
        }

@dataclass
class GenerationConfig:
    """生成配置"""
    model: ModelType = ModelType.DEEPSEEK_CHAT
    temperature: float = 0.7
    max_tokens: int = 2048
    top_p: float = 0.9
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stream: bool = False
    stop: Optional[List[str]] = None

@dataclass
class ChatResponse:
    """聊天响应"""
    content: str
    model: str
    usage: Dict[str, int]
    finish_reason: str
    response_time: float
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

class DeepSeekClient:
    """DeepSeek大模型客户端"""
    
    def __init__(self, 
                 api_key: str = None,
                 base_url: str = "https://api.deepseek.com/v1",
                 timeout: int = 60,
                 max_retries: int = 3):
        """
        初始化DeepSeek客户端
        
        Args:
            api_key: DeepSeek API密钥
            base_url: API基础URL
            timeout: 请求超时时间(秒)
            max_retries: 最大重试次数
        """
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        
        if not self.api_key:
            raise ValueError("DeepSeek API密钥未设置，请设置DEEPSEEK_API_KEY环境变量或传入api_key参数")
            
        # 配置OpenAI客户端以兼容DeepSeek API
        self.client = openai.AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout
        )
        
        self.logger = logging.getLogger(__name__)
        
        # 默认配置
        self.default_config = GenerationConfig()
        
        # 请求历史（用于调试和监控）
        self.request_history: List[Dict[str, Any]] = []
        
    async def chat_completion(self,
                            messages: List[ChatMessage],
                            config: GenerationConfig = None) -> ChatResponse:
        """
        聊天补全
        
        Args:
            messages: 消息列表
            config: 生成配置
            
        Returns:
            ChatResponse: 聊天响应
        """
        config = config or self.default_config
        start_time = datetime.now()
        
        try:
            # 准备请求参数
            request_messages = [msg.to_dict() for msg in messages]
            
            request_params = {
                "model": config.model.value,
                "messages": request_messages,
                "temperature": config.temperature,
                "max_tokens": config.max_tokens,
                "top_p": config.top_p,
                "frequency_penalty": config.frequency_penalty,
                "presence_penalty": config.presence_penalty,
                "stream": config.stream
            }
            
            if config.stop:
                request_params["stop"] = config.stop
                
            self.logger.info(f"发送DeepSeek请求: {config.model.value}")
            
            # 发送请求
            response = await self.client.chat.completions.create(**request_params)
            
            # 计算响应时间
            response_time = (datetime.now() - start_time).total_seconds()
            
            # 解析响应
            chat_response = ChatResponse(
                content=response.choices[0].message.content,
                model=response.model,
                usage=response.usage.model_dump() if response.usage else {},
                finish_reason=response.choices[0].finish_reason,
                response_time=response_time
            )
            
            # 记录请求历史
            self._log_request(request_params, chat_response, success=True)
            
            self.logger.info(f"DeepSeek响应成功，耗时: {response_time:.2f}秒")
            return chat_response
            
        except Exception as e:
            response_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"DeepSeek请求失败: {e}")
            
            # 记录失败请求
            self._log_request(request_params if 'request_params' in locals() else {}, 
                            None, success=False, error=str(e))
            raise
            
    async def chat_completion_stream(self,
                                   messages: List[ChatMessage],
                                   config: GenerationConfig = None) -> AsyncGenerator[str, None]:
        """
        流式聊天补全
        
        Args:
            messages: 消息列表
            config: 生成配置
            
        Yields:
            str: 流式响应内容片段
        """
        config = config or self.default_config
        config.stream = True
        
        try:
            # 准备请求参数
            request_messages = [msg.to_dict() for msg in messages]
            
            request_params = {
                "model": config.model.value,
                "messages": request_messages,
                "temperature": config.temperature,
                "max_tokens": config.max_tokens,
                "top_p": config.top_p,
                "frequency_penalty": config.frequency_penalty,
                "presence_penalty": config.presence_penalty,
                "stream": True
            }
            
            if config.stop:
                request_params["stop"] = config.stop
                
            self.logger.info(f"发送DeepSeek流式请求: {config.model.value}")
            
            # 发送流式请求
            stream = await self.client.chat.completions.create(**request_params)
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            self.logger.error(f"DeepSeek流式请求失败: {e}")
            raise
            
    async def generate_answer(self,
                            question: str,
                            context: str = "",
                            domain: str = "",
                            config: GenerationConfig = None) -> str:
        """
        生成问答回答
        
        Args:
            question: 问题
            context: 上下文信息
            domain: 领域信息
            config: 生成配置
            
        Returns:
            str: 生成的答案
        """
        # 构建提示词
        system_prompt = self._build_qa_system_prompt(domain)
        user_prompt = self._build_qa_user_prompt(question, context)
        
        messages = [
            ChatMessage(MessageRole.SYSTEM, system_prompt),
            ChatMessage(MessageRole.USER, user_prompt)
        ]
        
        response = await self.chat_completion(messages, config)
        return response.content
        
    async def analyze_content(self,
                            content: str,
                            analysis_type: str = "summary",
                            config: GenerationConfig = None) -> str:
        """
        内容分析
        
        Args:
            content: 要分析的内容
            analysis_type: 分析类型 (summary, keywords, topics, sentiment)
            config: 生成配置
            
        Returns:
            str: 分析结果
        """
        system_prompt = self._build_analysis_system_prompt(analysis_type)
        user_prompt = f"请分析以下内容：\n\n{content}"
        
        messages = [
            ChatMessage(MessageRole.SYSTEM, system_prompt),
            ChatMessage(MessageRole.USER, user_prompt)
        ]
        
        response = await self.chat_completion(messages, config)
        return response.content
        
    async def extract_knowledge(self,
                              content: str,
                              domain: str = "",
                              config: GenerationConfig = None) -> Dict[str, Any]:
        """
        从内容中提取结构化知识
        
        Args:
            content: 原始内容
            domain: 领域信息
            config: 生成配置
            
        Returns:
            Dict[str, Any]: 结构化知识
        """
        system_prompt = self._build_knowledge_extraction_prompt(domain)
        user_prompt = f"请从以下内容中提取结构化知识：\n\n{content}"
        
        messages = [
            ChatMessage(MessageRole.SYSTEM, system_prompt),
            ChatMessage(MessageRole.USER, user_prompt)
        ]
        
        response = await self.chat_completion(messages, config)
        
        try:
            # 尝试解析JSON格式的响应
            knowledge = json.loads(response.content)
            return knowledge
        except json.JSONDecodeError:
            # 如果不是JSON格式，返回文本格式
            return {
                "raw_text": response.content,
                "extraction_method": "text",
                "domain": domain
            }
            
    async def translate_content(self,
                              content: str,
                              target_language: str = "中文",
                              config: GenerationConfig = None) -> str:
        """
        内容翻译
        
        Args:
            content: 要翻译的内容
            target_language: 目标语言
            config: 生成配置
            
        Returns:
            str: 翻译结果
        """
        system_prompt = f"你是一个专业的翻译助手，请将用户提供的内容翻译成{target_language}，保持原意不变，语言自然流畅。"
        user_prompt = f"请翻译以下内容：\n\n{content}"
        
        messages = [
            ChatMessage(MessageRole.SYSTEM, system_prompt),
            ChatMessage(MessageRole.USER, user_prompt)
        ]
        
        response = await self.chat_completion(messages, config)
        return response.content
        
    def _build_qa_system_prompt(self, domain: str = "") -> str:
        """构建问答系统提示词"""
        base_prompt = """你是一个专业的知识问答助手，具备以下能力：
1. 基于提供的上下文信息准确回答问题
2. 如果上下文信息不足，会明确说明
3. 提供详细、准确、有用的答案
4. 保持客观和专业的态度"""

        if domain:
            base_prompt += f"\n\n你专门负责{domain}领域的问题，请运用该领域的专业知识回答问题。"
            
        return base_prompt
        
    def _build_qa_user_prompt(self, question: str, context: str = "") -> str:
        """构建问答用户提示词"""
        if context:
            return f"""上下文信息：
{context}

问题：{question}

请基于上述上下文信息回答问题。如果上下文信息不足以回答问题，请说明需要什么额外信息。"""
        else:
            return f"问题：{question}"
            
    def _build_analysis_system_prompt(self, analysis_type: str) -> str:
        """构建内容分析系统提示词"""
        prompts = {
            "summary": "你是一个专业的内容摘要助手，能够快速理解文本内容并生成简洁准确的摘要。",
            "keywords": "你是一个关键词提取专家，能够从文本中识别出最重要的关键词和术语。",
            "topics": "你是一个主题分析专家，能够识别文本的主要主题和话题。",
            "sentiment": "你是一个情感分析专家，能够准确识别文本的情感倾向。",
            "entities": "你是一个实体识别专家，能够识别文本中的人名、地名、机构名等实体。"
        }
        
        return prompts.get(analysis_type, "你是一个内容分析助手，请分析用户提供的内容。")
        
    def _build_knowledge_extraction_prompt(self, domain: str = "") -> str:
        """构建知识提取提示词"""
        base_prompt = """你是一个知识提取专家，能够从文本中提取结构化的知识信息。

请按照以下JSON格式返回提取的知识：
{
    "title": "内容标题",
    "main_concepts": ["主要概念1", "主要概念2"],
    "key_facts": ["关键事实1", "关键事实2"],
    "relationships": [{"subject": "主体", "relation": "关系", "object": "客体"}],
    "definitions": {"术语1": "定义1", "术语2": "定义2"},
    "procedures": ["步骤1", "步骤2"],
    "examples": ["示例1", "示例2"],
    "references": ["参考资料1", "参考资料2"]
}"""

        if domain:
            base_prompt += f"\n\n请特别关注{domain}领域的专业知识和术语。"
            
        return base_prompt
        
    def _log_request(self, 
                    request_params: Dict[str, Any],
                    response: Optional[ChatResponse],
                    success: bool,
                    error: str = "") -> None:
        """记录请求历史"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "request_params": request_params,
            "success": success,
            "error": error
        }
        
        if response:
            log_entry["response"] = {
                "content_length": len(response.content),
                "model": response.model,
                "usage": response.usage,
                "response_time": response.response_time
            }
            
        self.request_history.append(log_entry)
        
        # 保持最近1000条记录
        if len(self.request_history) > 1000:
            self.request_history = self.request_history[-1000:]
            
    async def get_models(self) -> List[str]:
        """获取可用的模型列表"""
        try:
            models = await self.client.models.list()
            return [model.id for model in models.data]
        except Exception as e:
            self.logger.error(f"获取模型列表失败: {e}")
            return [model.value for model in ModelType]
            
    def get_request_statistics(self) -> Dict[str, Any]:
        """获取请求统计信息"""
        if not self.request_history:
            return {"total_requests": 0}
            
        total_requests = len(self.request_history)
        successful_requests = sum(1 for req in self.request_history if req["success"])
        failed_requests = total_requests - successful_requests
        
        # 计算平均响应时间
        response_times = [
            req.get("response", {}).get("response_time", 0) 
            for req in self.request_history 
            if req["success"] and "response" in req
        ]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        # 统计使用的token
        total_tokens = sum(
            req.get("response", {}).get("usage", {}).get("total_tokens", 0)
            for req in self.request_history
            if req["success"] and "response" in req
        )
        
        return {
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "failed_requests": failed_requests,
            "success_rate": successful_requests / total_requests if total_requests > 0 else 0,
            "average_response_time": avg_response_time,
            "total_tokens_used": total_tokens
        }
        
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            test_messages = [
                ChatMessage(MessageRole.USER, "Hello, this is a health check.")
            ]
            
            config = GenerationConfig(max_tokens=10)
            await self.chat_completion(test_messages, config)
            return True
            
        except Exception as e:
            self.logger.error(f"健康检查失败: {e}")
            return False

# 使用示例
async def main():
    """测试DeepSeek客户端"""
    # 需要设置DEEPSEEK_API_KEY环境变量
    client = DeepSeekClient()
    
    # 测试基本聊天
    messages = [
        ChatMessage(MessageRole.USER, "请介绍一下人工智能的发展历程")
    ]
    
    try:
        response = await client.chat_completion(messages)
        print(f"回答: {response.content}")
        print(f"模型: {response.model}")
        print(f"响应时间: {response.response_time}秒")
        
        # 测试问答功能
        answer = await client.generate_answer(
            question="什么是机器学习？",
            context="机器学习是人工智能的一个分支...",
            domain="人工智能"
        )
        print(f"问答回答: {answer}")
        
        # 获取统计信息
        stats = client.get_request_statistics()
        print(f"请求统计: {stats}")
        
    except Exception as e:
        print(f"测试失败: {e}")

if __name__ == "__main__":
    asyncio.run(main())