#!/usr/bin/env python3
"""
AI系统自我进化集成模块
将经验系统集成到主要的AI问答组件中
"""

import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
from pathlib import Path

# 导入现有系统组件
import sys
sys.path.append(str(Path(__file__).parent.parent))

from ai_evolution.experience_system import ExperienceKnowledgeBase, AdaptiveLearningEngine
from qa_engine.answer_generator import AnswerGenerator, QuestionContext, AnswerResult
from knowledge_base.vector_store import VectorStore, SearchResult

class EvolutionaryAnswerGenerator(AnswerGenerator):
    """具有自我进化能力的答案生成器"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 初始化经验系统
        self.experience_kb = ExperienceKnowledgeBase("experience_kb")
        self.learning_engine = AdaptiveLearningEngine(self.experience_kb)
        
        self.logger = logging.getLogger(__name__)
        
        # 性能监控指标
        self.performance_metrics = {
            "total_questions": 0,
            "knowledge_retrieval_failures": 0,
            "low_confidence_answers": 0,
            "user_satisfaction_feedback": []
        }
        
    async def generate_answer(self, context: QuestionContext) -> AnswerResult:
        """增强的答案生成，包含自我学习能力"""
        
        # 记录问题
        self.performance_metrics["total_questions"] += 1
        
        # 检查是否有相似的历史问题经验
        similar_experience = self.experience_kb.suggest_solution(
            context.question, 
            {"domain": context.domain}
        )
        
        if similar_experience["status"] == "found_solution":
            self.logger.info(f"找到相似经验: {similar_experience['experience_id']}")
            # 可以基于历史经验调整生成策略
            
        # 调用原始的答案生成
        start_time = datetime.now()
        result = await super().generate_answer(context)
        generation_time = (datetime.now() - start_time).total_seconds()
        
        # 分析答案质量并学习
        await self._analyze_and_learn(context, result, generation_time)
        
        return result
        
    async def _analyze_and_learn(self, context: QuestionContext, result: AnswerResult, generation_time: float):
        """分析答案质量并从中学习"""
        
        # 检测潜在问题
        issues = []
        
        if result.confidence < 0.5:
            issues.append("低置信度答案")
            self.performance_metrics["low_confidence_answers"] += 1
            
        if len(result.sources) == 0:
            issues.append("未找到相关知识源")
            self.performance_metrics["knowledge_retrieval_failures"] += 1
            
        if generation_time > 10.0:
            issues.append("生成时间过长")
            
        if "抱歉" in result.answer or "无法" in result.answer:
            issues.append("可能的答案质量问题")
            
        # 如果发现问题，记录到经验库
        if issues:
            await self._record_quality_issue(context, result, issues, generation_time)
            
        # 记录用户交互模式
        self.learning_engine.analyze_user_interaction({
            "question": context.question,
            "domain": context.domain,
            "confidence": result.confidence,
            "sources_count": len(result.sources),
            "generation_time": generation_time,
            "issues": issues
        })
        
    async def _record_quality_issue(self, context: QuestionContext, result: AnswerResult, issues: List[str], generation_time: float):
        """记录质量问题到经验库"""
        from ai_evolution.experience_system import ExperienceRecord
        import uuid
        
        experience = ExperienceRecord(
            id=str(uuid.uuid4()),
            timestamp=datetime.now().isoformat(),
            category="quality_issue",
            problem_description=f"问答质量问题: {', '.join(issues)}。问题: {context.question[:100]}",
            solution_description="待优化 - 需要进一步分析和改进",
            code_changes=[],
            impact_metrics={
                "confidence": result.confidence,
                "sources_count": len(result.sources),
                "generation_time": generation_time,
                "domain": context.domain
            },
            lessons_learned=[
                f"问题类型: {', '.join(issues)}",
                f"领域: {context.domain or '通用'}",
                f"问题长度: {len(context.question)} 字符"
            ],
            tags=["质量问题", "自动检测"] + issues,
            confidence_score=0.6
        )
        
        self.experience_kb.add_experience(experience)
        
    async def get_proactive_suggestions(self) -> List[Dict[str, Any]]:
        """获取主动优化建议"""
        suggestions = self.learning_engine.suggest_proactive_optimizations()
        
        # 基于性能指标添加具体建议
        if self.performance_metrics["knowledge_retrieval_failures"] > 5:
            suggestions.append({
                "type": "knowledge_base_optimization",
                "description": "检测到多次知识检索失败，建议优化知识库或调整搜索策略",
                "confidence": 0.8,
                "priority": "high"
            })
            
        if self.performance_metrics["low_confidence_answers"] > 10:
            suggestions.append({
                "type": "model_optimization", 
                "description": "检测到多个低置信度答案，建议优化生成模型或增强知识库",
                "confidence": 0.7,
                "priority": "medium"
            })
            
        return suggestions
        
    def get_evolution_statistics(self) -> Dict[str, Any]:
        """获取进化统计信息"""
        kb_stats = self.experience_kb.get_statistics()
        
        return {
            "experience_knowledge_base": kb_stats,
            "performance_metrics": self.performance_metrics,
            "success_rate": 1 - (self.performance_metrics["knowledge_retrieval_failures"] / max(self.performance_metrics["total_questions"], 1)),
            "avg_confidence": self.performance_metrics.get("avg_confidence", 0),
            "evolution_enabled": True
        }

class EvolutionaryVectorStore(VectorStore):
    """具有自我进化能力的向量存储"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.experience_kb = ExperienceKnowledgeBase("vector_store_experiences")
        
        # 搜索性能监控
        self.search_metrics = {
            "total_searches": 0,
            "empty_results": 0,
            "low_similarity_results": 0,
            "avg_search_time": 0
        }
        
    async def search(self, query, *args, **kwargs) -> List[SearchResult]:
        """增强的搜索，包含性能监控和学习"""
        start_time = datetime.now()
        
        results = await super().search(query, *args, **kwargs)
        
        search_time = (datetime.now() - start_time).total_seconds()
        
        # 更新监控指标
        self.search_metrics["total_searches"] += 1
        self.search_metrics["avg_search_time"] = (
            (self.search_metrics["avg_search_time"] * (self.search_metrics["total_searches"] - 1) + search_time)
            / self.search_metrics["total_searches"]
        )
        
        if len(results) == 0:
            self.search_metrics["empty_results"] += 1
            await self._record_search_issue(query, "empty_results", search_time)
            
        elif results and results[0].similarity_score < 0.3:
            self.search_metrics["low_similarity_results"] += 1
            await self._record_search_issue(query, "low_similarity", search_time)
            
        return results
        
    async def _record_search_issue(self, query, issue_type: str, search_time: float):
        """记录搜索问题"""
        from ai_evolution.experience_system import ExperienceRecord
        import uuid
        
        experience = ExperienceRecord(
            id=str(uuid.uuid4()),
            timestamp=datetime.now().isoformat(),
            category="search_issue",
            problem_description=f"向量搜索问题: {issue_type}。查询: {query.query_text[:100]}",
            solution_description="需要优化搜索策略或改进知识库内容",
            code_changes=[],
            impact_metrics={
                "search_time": search_time,
                "query_length": len(query.query_text),
                "similarity_threshold": query.similarity_threshold
            },
            lessons_learned=[
                f"搜索问题类型: {issue_type}",
                f"查询词长度: {len(query.query_text)}",
                f"搜索时间: {search_time:.2f}秒"
            ],
            tags=["搜索优化", issue_type],
            confidence_score=0.7
        )
        
        self.experience_kb.add_experience(experience)

# 系统启动时的初始化函数
async def initialize_evolutionary_system():
    """初始化进化系统"""
    logging.info("初始化AI自我进化系统...")
    
    # 创建经验知识库目录
    Path("experience_kb").mkdir(exist_ok=True)
    Path("vector_store_experiences").mkdir(exist_ok=True)
    
    # 记录系统启动经验
    kb = ExperienceKnowledgeBase()
    result = kb.record_current_session_experience()
    
    logging.info(f"AI进化系统初始化完成，记录了 {result['recorded_experiences']} 个历史经验")
    
    return kb

# 添加到现有API服务器的集成代码
def integrate_evolution_system_to_api():
    """将进化系统集成到API服务器"""
    integration_code = """
# 在 api_server.py 中添加以下代码

from ai_evolution.evolution_integration import EvolutionaryAnswerGenerator, initialize_evolutionary_system

# 在初始化函数中替换
async def initialize_system():
    # ... 现有代码 ...
    
    # 使用进化版本的答案生成器
    answer_generator = EvolutionaryAnswerGenerator(llm_client, vector_store, qa_config)
    
    # 初始化进化系统
    await initialize_evolutionary_system()
    
    # ... 其余代码 ...

# 添加新的API端点
@app.get("/evolution/statistics")
async def get_evolution_statistics():
    '''获取AI进化统计信息'''
    if not isinstance(answer_generator, EvolutionaryAnswerGenerator):
        raise HTTPException(status_code=503, detail="进化系统未启用")
        
    return answer_generator.get_evolution_statistics()

@app.get("/evolution/suggestions")
async def get_proactive_suggestions():
    '''获取主动优化建议'''
    if not isinstance(answer_generator, EvolutionaryAnswerGenerator):
        raise HTTPException(status_code=503, detail="进化系统未启用")
        
    suggestions = await answer_generator.get_proactive_suggestions()
    return {"suggestions": suggestions, "count": len(suggestions)}
"""
    
    print("请将以下代码集成到 api_server.py 中:")
    print(integration_code)

if __name__ == "__main__":
    # 测试进化系统
    asyncio.run(initialize_evolutionary_system())
    integrate_evolution_system_to_api()