#!/usr/bin/env python3
"""
智能行业知识问答系统 - 领域适配器基类
为不同行业领域提供专业化的问答能力
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging

# 前向引用类型
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from qa_engine.answer_generator import QuestionContext, AnswerResult
    from knowledge_base.vector_store import SearchResult

@dataclass
class DomainKnowledge:
    """领域知识定义"""
    domain_name: str
    key_concepts: List[str]
    terminology: Dict[str, str]
    common_questions: List[str]
    expert_sources: List[str]
    quality_indicators: List[str]

class DomainAdapter(ABC):
    """领域适配器抽象基类"""
    
    def __init__(self, domain_name: str):
        """
        初始化领域适配器
        
        Args:
            domain_name: 领域名称
        """
        self.domain_name = domain_name
        self.logger = logging.getLogger(f"{__name__}.{domain_name}")
        
        # 加载领域知识
        self.domain_knowledge = self._init_domain_knowledge()
        
    @abstractmethod
    def _init_domain_knowledge(self) -> DomainKnowledge:
        """初始化领域知识（子类必须实现）"""
        pass
        
    @abstractmethod
    async def build_system_prompt(self, question: str) -> str:
        """
        构建领域特定的系统提示词
        
        Args:
            question: 用户问题
            
        Returns:
            str: 系统提示词
        """
        pass
        
    async def preprocess_question(self, question: str) -> str:
        """
        预处理问题（可重写）
        
        Args:
            question: 原始问题
            
        Returns:
            str: 预处理后的问题
        """
        # 默认实现：术语标准化
        processed_question = question
        
        for term, standard_term in self.domain_knowledge.terminology.items():
            processed_question = processed_question.replace(term, standard_term)
            
        return processed_question
        
    async def post_process_answer(self, 
                                answer_result: 'AnswerResult',
                                context: 'QuestionContext', 
                                knowledge_results: List['SearchResult']) -> 'AnswerResult':
        """
        后处理答案（可重写）
        
        Args:
            answer_result: 原始答案结果
            context: 问题上下文
            knowledge_results: 知识检索结果
            
        Returns:
            AnswerResult: 后处理后的答案结果
        """
        # 默认实现：添加领域特定的质量检查
        answer_result.confidence = self._adjust_confidence_for_domain(
            answer_result.confidence, answer_result.answer
        )
        
        return answer_result
        
    def _adjust_confidence_for_domain(self, base_confidence: float, answer: str) -> float:
        """根据领域特征调整置信度"""
        adjusted_confidence = base_confidence
        
        # 检查是否包含领域关键概念
        concept_count = sum(1 for concept in self.domain_knowledge.key_concepts 
                          if concept.lower() in answer.lower())
        
        if concept_count > 0:
            adjusted_confidence += 0.1 * min(concept_count, 3) / 3
            
        # 检查质量指标
        quality_score = 0
        for indicator in self.domain_knowledge.quality_indicators:
            if indicator.lower() in answer.lower():
                quality_score += 0.05
                
        adjusted_confidence += quality_score
        
        return min(adjusted_confidence, 1.0)
        
    async def validate_answer_quality(self, answer: str, question: str) -> Tuple[bool, List[str]]:
        """
        验证答案质量
        
        Args:
            answer: 生成的答案
            question: 原始问题
            
        Returns:
            Tuple[bool, List[str]]: (是否通过验证, 问题列表)
        """
        issues = []
        
        # 基础质量检查
        if len(answer.strip()) < 20:
            issues.append("答案过短")
            
        # 领域术语检查
        domain_terms_found = sum(1 for term in self.domain_knowledge.key_concepts 
                               if term.lower() in answer.lower())
        
        if domain_terms_found == 0:
            issues.append("答案缺乏领域专业术语")
            
        # 答案相关性检查
        if not self._is_answer_relevant(answer, question):
            issues.append("答案与问题相关性不足")
            
        return len(issues) == 0, issues
        
    def _is_answer_relevant(self, answer: str, question: str) -> bool:
        """检查答案与问题的相关性"""
        # 简单的关键词匹配检查
        question_words = set(question.lower().split())
        answer_words = set(answer.lower().split())
        
        # 计算词汇重叠度
        overlap = len(question_words & answer_words)
        total_question_words = len(question_words)
        
        return overlap / total_question_words > 0.2 if total_question_words > 0 else False
        
    def get_domain_info(self) -> Dict[str, Any]:
        """获取领域信息"""
        return {
            "domain_name": self.domain_name,
            "key_concepts_count": len(self.domain_knowledge.key_concepts),
            "terminology_count": len(self.domain_knowledge.terminology),
            "common_questions_count": len(self.domain_knowledge.common_questions),
            "expert_sources_count": len(self.domain_knowledge.expert_sources)
        }
        
    async def suggest_related_questions(self, question: str) -> List[str]:
        """
        建议相关问题
        
        Args:
            question: 当前问题
            
        Returns:
            List[str]: 相关问题列表
        """
        # 基于常见问题推荐
        related = []
        
        question_lower = question.lower()
        for common_q in self.domain_knowledge.common_questions:
            # 简单的相似度匹配
            common_words = set(common_q.lower().split()) & set(question_lower.split())
            if len(common_words) >= 2:  # 至少有2个共同词汇
                related.append(common_q)
                
        return related[:5]  # 返回最多5个相关问题