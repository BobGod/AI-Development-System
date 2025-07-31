#!/usr/bin/env python3
"""
智能行业知识问答系统 - 答案生成器
结合知识检索和大模型生成专业、准确的答案
"""

import asyncio
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import logging
from pathlib import Path

# 本地模块
import sys
sys.path.append(str(Path(__file__).parent.parent))
from llm_integration.deepseek_client import DeepSeekClient, ChatMessage, MessageRole, GenerationConfig
from knowledge_base.vector_store import VectorStore, SearchQuery, SearchResult
from domain_adapters.base_adapter import DomainAdapter

@dataclass
class QuestionContext:
    """问题上下文"""
    question: str
    domain: str = ""
    user_id: str = ""
    session_id: str = ""
    conversation_history: List[Dict[str, str]] = None
    additional_context: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.conversation_history is None:
            self.conversation_history = []
        if self.additional_context is None:
            self.additional_context = {}

@dataclass 
class AnswerResult:
    """答案结果"""
    answer: str
    confidence: float
    sources: List[Dict[str, Any]]
    reasoning_steps: List[str]
    generated_at: str = ""
    model_used: str = ""
    tokens_used: Dict[str, int] = None
    
    def __post_init__(self):
        if not self.generated_at:
            self.generated_at = datetime.now().isoformat()
        if self.tokens_used is None:
            self.tokens_used = {}

@dataclass
class QAConfig:
    """问答配置"""
    max_context_length: int = 4000
    top_k_results: int = 5
    similarity_threshold: float = 0.3
    temperature: float = 0.3
    max_tokens: int = 1024
    enable_reasoning: bool = True
    enable_source_citation: bool = True
    fallback_to_general: bool = True

class AnswerGenerator:
    """答案生成器"""
    
    def __init__(self,
                 llm_client: DeepSeekClient,
                 vector_store: VectorStore,
                 config: QAConfig = None):
        """
        初始化答案生成器
        
        Args:
            llm_client: DeepSeek客户端
            vector_store: 向量数据库
            config: 问答配置
        """
        self.llm_client = llm_client
        self.vector_store = vector_store
        self.config = config or QAConfig()
        
        self.logger = logging.getLogger(__name__)
        
        # 领域适配器映射
        self.domain_adapters: Dict[str, DomainAdapter] = {}
        
        # 问答历史和缓存
        self.qa_history: List[Dict[str, Any]] = []
        self.answer_cache: Dict[str, AnswerResult] = {}
        
    def register_domain_adapter(self, domain: str, adapter: DomainAdapter):
        """注册领域适配器"""
        self.domain_adapters[domain] = adapter
        self.logger.info(f"注册领域适配器: {domain}")
        
    async def generate_answer(self, context: QuestionContext) -> AnswerResult:
        """
        生成答案
        
        Args:
            context: 问题上下文
            
        Returns:
            AnswerResult: 生成的答案结果
        """
        try:
            self.logger.info(f"开始生成答案: {context.question[:50]}...")
            
            # 检查缓存
            cache_key = self._generate_cache_key(context)
            if cache_key in self.answer_cache:
                cached_answer = self.answer_cache[cache_key]
                self.logger.info("使用缓存答案")
                return cached_answer
                
            # 1. 知识检索
            relevant_knowledge = await self._retrieve_knowledge(context)
            
            # 2. 构建上下文
            generation_context = await self._build_generation_context(
                context, relevant_knowledge
            )
            
            # 3. 生成答案
            answer_result = await self._generate_with_llm(
                context, generation_context, relevant_knowledge
            )
            
            # 4. 后处理和验证
            answer_result = await self._post_process_answer(
                answer_result, context, relevant_knowledge
            )
            
            # 5. 缓存结果
            self.answer_cache[cache_key] = answer_result
            
            # 6. 记录历史
            self._record_qa_history(context, answer_result)
            
            self.logger.info(f"答案生成完成，置信度: {answer_result.confidence:.3f}")
            return answer_result
            
        except Exception as e:
            self.logger.error(f"答案生成失败: {e}")
            
            # 返回错误答案
            return AnswerResult(
                answer="抱歉，我无法生成答案，请稍后重试。",
                confidence=0.0,
                sources=[],
                reasoning_steps=["答案生成过程中出现错误"]
            )
            
    async def _retrieve_knowledge(self, context: QuestionContext) -> List[SearchResult]:
        """检索相关知识"""
        try:
            # 构建搜索查询
            search_query = SearchQuery(
                query_text=context.question,
                top_k=self.config.top_k_results,
                similarity_threshold=self.config.similarity_threshold,
                domain=context.domain
            )
            
            # 执行搜索
            search_results = await self.vector_store.search(search_query)
            
            # 如果结果不足且启用了通用回退，进行通用搜索
            if (len(search_results) < 2 and 
                self.config.fallback_to_general and 
                context.domain):
                
                general_query = SearchQuery(
                    query_text=context.question,
                    top_k=self.config.top_k_results,
                    similarity_threshold=self.config.similarity_threshold * 0.8,
                    domain=""  # 不限制领域
                )
                
                general_results = await self.vector_store.search(general_query)
                
                # 合并结果，优先领域相关的
                search_results.extend(general_results)
                search_results = search_results[:self.config.top_k_results]
                
            self.logger.info(f"检索到 {len(search_results)} 个相关知识块")
            return search_results
            
        except Exception as e:
            self.logger.error(f"知识检索失败: {e}")
            return []
            
    async def _build_generation_context(self, 
                                      context: QuestionContext,
                                      knowledge_results: List[SearchResult]) -> str:
        """构建生成上下文"""
        try:
            context_parts = []
            
            # 添加领域信息
            if context.domain:
                context_parts.append(f"领域: {context.domain}")
                
            # 添加相关知识
            if knowledge_results:
                context_parts.append("相关知识:")
                
                for i, result in enumerate(knowledge_results, 1):
                    # 截断过长的内容
                    content = result.chunk.content
                    if len(content) > 500:
                        content = content[:500] + "..."
                        
                    source_info = ""
                    if result.chunk.metadata.get('source_file'):
                        source_info = f" (来源: {result.chunk.metadata['source_file']})"
                        
                    context_parts.append(
                        f"{i}. {content}{source_info}"
                    )
                    
            # 添加对话历史
            if context.conversation_history:
                context_parts.append("\n对话历史:")
                for turn in context.conversation_history[-3:]:  # 只保留最近3轮
                    if turn.get('user'):
                        context_parts.append(f"用户: {turn['user']}")
                    if turn.get('assistant'):
                        context_parts.append(f"助手: {turn['assistant']}")
                        
            # 控制总长度
            full_context = "\n".join(context_parts)
            if len(full_context) > self.config.max_context_length:
                # 截断并保留最重要的部分
                full_context = full_context[:self.config.max_context_length] + "..."
                
            return full_context
            
        except Exception as e:
            self.logger.error(f"构建生成上下文失败: {e}")
            return ""
            
    async def _generate_with_llm(self,
                               context: QuestionContext,
                               generation_context: str,
                               knowledge_results: List[SearchResult]) -> AnswerResult:
        """使用大模型生成答案"""
        try:
            # 获取领域适配器
            domain_adapter = self.domain_adapters.get(context.domain)
            
            # 构建系统提示词
            if domain_adapter:
                system_prompt = await domain_adapter.build_system_prompt(context.question)
            else:
                system_prompt = self._build_default_system_prompt(context.domain)
                
            # 构建用户提示词
            user_prompt = self._build_user_prompt(
                context.question, generation_context, knowledge_results
            )
            
            # 准备消息
            messages = [
                ChatMessage(MessageRole.SYSTEM, system_prompt),
                ChatMessage(MessageRole.USER, user_prompt)
            ]
            
            # 配置生成参数
            gen_config = GenerationConfig(
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens
            )
            
            # 生成答案
            response = await self.llm_client.chat_completion(messages, gen_config)
            
            # 解析推理步骤（如果启用）
            reasoning_steps = []
            if self.config.enable_reasoning:
                reasoning_steps = self._extract_reasoning_steps(response.content)
                
            # 构建源引用
            sources = []
            if self.config.enable_source_citation and knowledge_results:
                sources = self._build_source_citations(knowledge_results)
                
            # 计算置信度
            confidence = self._calculate_confidence(
                response.content, knowledge_results, context
            )
            
            return AnswerResult(
                answer=response.content,
                confidence=confidence,
                sources=sources,
                reasoning_steps=reasoning_steps,
                model_used=response.model,
                tokens_used=response.usage
            )
            
        except Exception as e:
            self.logger.error(f"LLM生成失败: {e}")
            raise
            
    def _build_default_system_prompt(self, domain: str = "") -> str:
        """构建默认系统提示词"""
        base_prompt = """你是一个专业的知识问答助手，具备以下能力：

1. **优先使用提供的相关知识**：当用户提供了相关知识时，你必须基于这些知识来回答问题，而不是仅依赖你的预训练知识
2. **准确引用信息来源**：在回答中明确指出信息来自哪个文档或来源
3. **保持知识一致性**：确保答案与提供的知识内容一致，不要添加与知识相矛盾的信息
4. **承认知识局限**：如果提供的知识不足以完全回答问题，会明确说明并提供尽可能的帮助
5. **提供详细准确的答案**：基于已有知识给出完整、有用的回答
6. **保持专业客观**：使用专业、客观的语言，避免主观臆测

**重要提醒**：
- 当看到"相关知识"部分时，这些是用户刚刚上传的文档内容，请优先基于这些知识回答
- 如果相关知识中包含具体的统计数据、研究结果或专业信息，请直接使用这些内容
- 在回答中明确标注信息来源，如"根据上传的文档..."或"文档中提到..."
"""

        if domain:
            base_prompt += f"\n\n你专门负责{domain}领域的问题，请运用该领域的专业知识结合提供的相关知识回答问题。"
            
        if self.config.enable_reasoning:
            base_prompt += "\n\n请在回答中包含你的推理过程，说明你是如何基于提供的知识得出结论的。"
            
        return base_prompt
        
    def _build_user_prompt(self,
                          question: str,
                          context: str,
                          knowledge_results: List[SearchResult]) -> str:
        """构建用户提示词"""
        prompt_parts = []
        
        if context:
            prompt_parts.append(f"上下文信息：\n{context}")
            
        prompt_parts.append(f"\n问题：{question}")
        
        if knowledge_results:
            prompt_parts.append("\n**请重点基于上述相关知识回答问题**")
            prompt_parts.append("这些知识来自用户上传的文档，是回答问题的核心依据。")
            
            if self.config.enable_source_citation:
                prompt_parts.append("请在答案中明确引用相关信息的来源文档。")
        else:
            prompt_parts.append("\n由于没有找到相关的上传文档内容，请基于你的通用知识回答问题，并说明这不是基于用户特定文档的回答。")
            
        if self.config.enable_reasoning:
            prompt_parts.append("请详细说明你的推理过程，特别是如何利用提供的知识得出答案。")
            
        return "\n".join(prompt_parts)
        
    async def _post_process_answer(self,
                                 answer_result: AnswerResult,
                                 context: QuestionContext,
                                 knowledge_results: List[SearchResult]) -> AnswerResult:
        """后处理答案"""
        try:
            # 获取领域适配器
            domain_adapter = self.domain_adapters.get(context.domain)
            
            if domain_adapter:
                # 使用领域适配器后处理
                answer_result = await domain_adapter.post_process_answer(
                    answer_result, context, knowledge_results
                )
                
            # 答案质量检查
            answer_result = self._quality_check(answer_result, context)
            
            return answer_result
            
        except Exception as e:
            self.logger.error(f"答案后处理失败: {e}")
            return answer_result
            
    def _quality_check(self, answer_result: AnswerResult, context: QuestionContext) -> AnswerResult:
        """答案质量检查"""
        # 检查答案长度
        if len(answer_result.answer.strip()) < 10:
            answer_result.confidence *= 0.5
            
        # 检查是否包含"不知道"等表达
        uncertain_phrases = ["不知道", "不确定", "无法确定", "抱歉"]
        if any(phrase in answer_result.answer for phrase in uncertain_phrases):
            answer_result.confidence *= 0.7
            
        # 检查是否有源引用
        if not answer_result.sources and self.config.enable_source_citation:
            answer_result.confidence *= 0.8
            
        return answer_result
        
    def _calculate_confidence(self,
                            answer: str,
                            knowledge_results: List[SearchResult],
                            context: QuestionContext) -> float:
        """计算答案置信度"""
        confidence = 0.5  # 基础置信度
        
        # 基于知识相关性
        if knowledge_results:
            avg_similarity = sum(r.similarity_score for r in knowledge_results) / len(knowledge_results)
            confidence += avg_similarity * 0.3
            
        # 基于答案长度和完整性
        if len(answer) > 50:
            confidence += 0.1
            
        # 基于领域匹配
        if context.domain and any(context.domain.lower() in r.chunk.metadata.get('topics', []) 
                                for r in knowledge_results):
            confidence += 0.1
            
        return min(confidence, 1.0)
        
    def _extract_reasoning_steps(self, answer: str) -> List[str]:
        """提取推理步骤"""
        # 简单的推理步骤提取
        steps = []
        
        # 寻找标志性的推理词汇
        reasoning_indicators = ["首先", "然后", "接下来", "最后", "因为", "所以", "由于"]
        
        sentences = answer.split('。')
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and any(indicator in sentence for indicator in reasoning_indicators):
                steps.append(sentence + '。')
                
        return steps
        
    def _build_source_citations(self, knowledge_results: List[SearchResult]) -> List[Dict[str, Any]]:
        """构建源引用"""
        sources = []
        
        for result in knowledge_results:
            source = {
                "content": result.chunk.content[:200] + "..." if len(result.chunk.content) > 200 else result.chunk.content,
                "similarity_score": result.similarity_score,
                "source_file": result.chunk.metadata.get('source_file', 'Unknown'),
                "document_id": result.chunk.metadata.get('document_id', ''),
                "chunk_id": result.chunk.chunk_id
            }
            
            # 添加URL如果是网页内容
            if result.chunk.metadata.get('url'):
                source["url"] = result.chunk.metadata['url']
                
            sources.append(source)
            
        return sources
        
    def _generate_cache_key(self, context: QuestionContext) -> str:
        """生成缓存键"""
        import hashlib
        
        key_content = f"{context.question}_{context.domain}"
        return hashlib.md5(key_content.encode()).hexdigest()
        
    def _record_qa_history(self, context: QuestionContext, result: AnswerResult):
        """记录问答历史"""
        history_entry = {
            "timestamp": datetime.now().isoformat(),
            "question": context.question,
            "domain": context.domain,
            "answer": result.answer,
            "confidence": result.confidence,
            "sources_count": len(result.sources),
            "user_id": context.user_id,
            "session_id": context.session_id
        }
        
        self.qa_history.append(history_entry)
        
        # 保持最近1000条记录
        if len(self.qa_history) > 1000:
            self.qa_history = self.qa_history[-1000:]
            
    async def batch_generate_answers(self, 
                                   contexts: List[QuestionContext],
                                   max_concurrent: int = 3) -> List[AnswerResult]:
        """批量生成答案"""
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def generate_with_semaphore(context: QuestionContext) -> AnswerResult:
            async with semaphore:
                return await self.generate_answer(context)
                
        tasks = [generate_with_semaphore(context) for context in contexts]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常结果
        final_results = []
        for result in results:
            if isinstance(result, AnswerResult):
                final_results.append(result)
            else:
                # 生成错误答案
                error_answer = AnswerResult(
                    answer="批量处理时出现错误，请重试。",
                    confidence=0.0,
                    sources=[],
                    reasoning_steps=[]
                )
                final_results.append(error_answer)
                
        return final_results
        
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        if not self.qa_history:
            return {"total_questions": 0}
            
        total_questions = len(self.qa_history)
        avg_confidence = sum(entry["confidence"] for entry in self.qa_history) / total_questions
        
        # 统计领域分布
        domain_counts = {}
        for entry in self.qa_history:
            domain = entry["domain"] or "通用"
            domain_counts[domain] = domain_counts.get(domain, 0) + 1
            
        return {
            "total_questions": total_questions,
            "average_confidence": avg_confidence,
            "domain_distribution": domain_counts,
            "cache_size": len(self.answer_cache),
            "registered_domains": list(self.domain_adapters.keys())
        }
        
    def clear_cache(self):
        """清理缓存"""
        self.answer_cache.clear()
        self.logger.info("答案缓存已清理")

# 使用示例
async def main():
    """测试答案生成器"""
    from llm_integration.deepseek_client import DeepSeekClient
    from knowledge_base.vector_store import VectorStore
    
    # 初始化组件（需要配置API密钥等）
    llm_client = DeepSeekClient()
    vector_store = VectorStore()
    
    generator = AnswerGenerator(llm_client, vector_store)
    
    # 测试问答
    context = QuestionContext(
        question="什么是人工智能？",
        domain="人工智能",
        user_id="test_user"
    )
    
    try:
        result = await generator.generate_answer(context)
        print(f"问题: {context.question}")
        print(f"答案: {result.answer}")
        print(f"置信度: {result.confidence:.3f}")
        print(f"源数量: {len(result.sources)}")
        
        # 获取统计信息
        stats = generator.get_statistics()
        print(f"统计信息: {stats}")
        
    except Exception as e:
        print(f"测试失败: {e}")

if __name__ == "__main__":
    asyncio.run(main())