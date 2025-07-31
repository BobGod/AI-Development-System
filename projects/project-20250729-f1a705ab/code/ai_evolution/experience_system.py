#!/usr/bin/env python3
"""
AI系统自我进化和经验积累框架
Experience-Based AI Evolution System
"""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import logging

@dataclass
class ExperienceRecord:
    """经验记录"""
    id: str
    timestamp: str
    category: str  # "bug_fix", "optimization", "user_feedback", "performance_issue"
    problem_description: str
    solution_description: str
    code_changes: List[Dict[str, str]]  # [{"file": "path", "change": "description"}]
    impact_metrics: Dict[str, Any]  # 影响指标
    lessons_learned: List[str]  # 经验教训
    tags: List[str]  # 标签
    confidence_score: float  # 经验的可信度分数
    reuse_count: int = 0  # 被重用次数
    effectiveness_score: float = 0.0  # 有效性评分

@dataclass
class OptimizationPattern:
    """优化模式"""
    pattern_id: str
    name: str
    description: str
    trigger_conditions: List[str]  # 触发条件
    solution_template: str  # 解决方案模板
    success_rate: float  # 成功率
    examples: List[str]  # 应用实例

class ExperienceKnowledgeBase:
    """经验知识库"""
    
    def __init__(self, data_dir: str = "experience_kb"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        self.experiences_file = self.data_dir / "experiences.json"
        self.patterns_file = self.data_dir / "optimization_patterns.json"
        self.insights_file = self.data_dir / "ai_insights.json"
        
        self.logger = logging.getLogger(__name__)
        
        # 加载现有经验
        self.experiences = self._load_experiences()
        self.patterns = self._load_patterns()
        self.ai_insights = self._load_ai_insights()
        
    def add_experience(self, experience: ExperienceRecord):
        """添加新的经验记录"""
        self.experiences[experience.id] = experience
        self._save_experiences()
        self.logger.info(f"新增经验记录: {experience.category} - {experience.problem_description[:50]}...")
        
        # 尝试从经验中提取模式
        self._extract_patterns_from_experience(experience)
        
    def find_similar_experiences(self, problem_description: str, category: str = None) -> List[ExperienceRecord]:
        """查找相似的经验"""
        similar = []
        problem_words = set(problem_description.lower().split())
        
        for exp in self.experiences.values():
            if category and exp.category != category:
                continue
                
            exp_words = set(exp.problem_description.lower().split())
            similarity = len(problem_words & exp_words) / len(problem_words | exp_words)
            
            if similarity > 0.3:  # 相似度阈值
                similar.append(exp)
                
        return sorted(similar, key=lambda x: x.effectiveness_score, reverse=True)
        
    def suggest_solution(self, problem_description: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """基于经验建议解决方案"""
        similar_experiences = self.find_similar_experiences(problem_description)
        
        if not similar_experiences:
            return {"status": "no_experience", "suggestion": "建议记录这个新问题的解决过程"}
            
        best_experience = similar_experiences[0]
        
        return {
            "status": "found_solution",
            "experience_id": best_experience.id,
            "suggested_solution": best_experience.solution_description,
            "confidence": best_experience.confidence_score,
            "lessons": best_experience.lessons_learned,
            "similar_cases": len(similar_experiences)
        }
        
    def record_current_session_experience(self):
        """记录当前会话的经验（基于我们刚才的调试过程）"""
        
        # 记录PDF解析优化经验
        pdf_experience = ExperienceRecord(
            id=str(uuid.uuid4()),
            timestamp=datetime.now().isoformat(),
            category="optimization",
            problem_description="PDF文档解析编码问题，中文内容变成乱码，导致向量搜索无法找到相关内容",
            solution_description="1. 升级PDF解析库：PyPDF2 -> pdfplumber + PyMuPDF；2. 实现多层级解析策略；3. 清理损坏数据并重建知识库",
            code_changes=[
                {"file": "code/knowledge_ingestion/document_parser.py", "change": "替换PyPDF2为pdfplumber和PyMuPDF，实现多层级PDF解析"},
                {"file": "requirements.txt", "change": "添加pdfplumber和pymupdf依赖"}
            ],
            impact_metrics={
                "中文字符提取成功率": "从0%提升到35.7%",
                "PDF解析质量": "从乱码到完整可读",
                "知识块数量": "删除18个损坏，新增6个高质量"
            },
            lessons_learned=[
                "PyPDF2对中文PDF支持不佳，pdfplumber是更好的选择",
                "应该实现多层级解析策略：pdfplumber -> PyMuPDF -> OCR",
                "PDF解析问题会影响整个知识库的有效性",
                "需要定期检查和清理损坏的知识块"
            ],
            tags=["PDF解析", "中文编码", "知识库", "向量搜索"],
            confidence_score=0.95
        )
        
        # 记录向量搜索优化经验
        vector_search_experience = ExperienceRecord(
            id=str(uuid.uuid4()),
            timestamp=datetime.now().isoformat(),
            category="bug_fix",
            problem_description="向量搜索返回0结果，相似度计算公式错误导致所有结果被过滤",
            solution_description="修复相似度计算公式：从1.0-distance改为1.0/(1.0+distance)，适配ChromaDB的欧几里得距离",
            code_changes=[
                {"file": "code/knowledge_base/vector_store.py", "change": "修复相似度计算公式，确保分数在0-1范围内"}
            ],
            impact_metrics={
                "搜索结果数量": "从0个提升到5个",
                "相似度分数": "从负数修正到0.3-0.4合理范围",
                "API搜索成功率": "从0%提升到100%"
            },
            lessons_learned=[
                "ChromaDB使用欧几里得距离，需要正确的相似度转换公式",
                "相似度分数应该在0-1范围内，便于阈值过滤",
                "向量搜索是知识问答系统的关键环节",
                "应该有完善的搜索结果验证机制"
            ],
            tags=["向量搜索", "相似度计算", "ChromaDB", "搜索优化"],
            confidence_score=0.9
        )
        
        # 记录系统集成经验
        integration_experience = ExperienceRecord(
            id=str(uuid.uuid4()),
            timestamp=datetime.now().isoformat(),
            category="optimization",
            problem_description="AI问答系统无法使用已上传的文档知识，回答像纯粹的DeepSeek而非本地知识系统",
            solution_description="端到端优化：PDF解析 -> 向量存储 -> 搜索检索 -> AI问答，确保整个知识流转链路正常",
            code_changes=[
                {"file": "multiple", "change": "系统性优化PDF解析、向量搜索、知识检索等多个环节"}
            ],
            impact_metrics={
                "AI回答准确性": "能正确引用上传文档内容",
                "置信度": "达到0.72高置信度",
                "信息源引用": "明确标注PDF文档来源",
                "知识库利用率": "从0%提升到正常使用"
            },
            lessons_learned=[
                "知识问答系统是一个端到端的复杂链路",
                "每个环节的问题都会影响最终效果",
                "需要有系统性的调试和验证方法",
                "用户体验是检验系统有效性的最终标准"
            ],
            tags=["端到端优化", "知识问答", "系统集成", "用户体验"],
            confidence_score=0.85
        )
        
        # 添加到知识库
        self.add_experience(pdf_experience)
        self.add_experience(vector_search_experience) 
        self.add_experience(integration_experience)
        
        # 生成AI洞察
        self._generate_ai_insights()
        
        return {
            "recorded_experiences": 3,
            "categories": ["optimization", "bug_fix", "optimization"],
            "total_lessons": sum(len(exp.lessons_learned) for exp in [pdf_experience, vector_search_experience, integration_experience])
        }
        
    def _extract_patterns_from_experience(self, experience: ExperienceRecord):
        """从经验中提取优化模式"""
        # 基于经验提取可重用的模式
        if "PDF" in experience.problem_description and "编码" in experience.problem_description:
            pattern = OptimizationPattern(
                pattern_id="pdf_encoding_fix",
                name="PDF中文编码问题修复模式",
                description="当PDF解析出现中文乱码时的标准解决方案",
                trigger_conditions=[
                    "PDF内容包含中文字符",
                    "解析结果出现乱码或特殊字符",
                    "向量搜索无法找到PDF相关内容"
                ],
                solution_template="1. 检查PDF解析库 2. 升级到pdfplumber/PyMuPDF 3. 清理损坏数据 4. 重新解析",
                success_rate=0.95,
                examples=[experience.id]
            )
            self.patterns[pattern.pattern_id] = pattern
            self._save_patterns()
            
    def _generate_ai_insights(self):
        """生成AI洞察和建议"""
        insights = {
            "generated_at": datetime.now().isoformat(),
            "total_experiences": len(self.experiences),
            "categories_distribution": {},
            "top_lessons": [],
            "improvement_suggestions": []
        }
        
        # 统计经验分类分布
        for exp in self.experiences.values():
            category = exp.category
            insights["categories_distribution"][category] = insights["categories_distribution"].get(category, 0) + 1
            
        # 收集最重要的经验教训
        all_lessons = []
        for exp in self.experiences.values():
            for lesson in exp.lessons_learned:
                all_lessons.append(lesson)
                
        # 简单去重和排序（实际可以用更复杂的NLP方法）
        insights["top_lessons"] = list(set(all_lessons))[:10]
        
        # 生成改进建议
        insights["improvement_suggestions"] = [
            "建立自动化测试，验证PDF解析质量",
            "实现向量搜索结果的质量监控",
            "建立用户反馈收集机制",
            "定期清理和优化知识库",
            "增加更多文档格式支持"
        ]
        
        self.ai_insights = insights
        self._save_ai_insights()
        
    def _load_experiences(self) -> Dict[str, ExperienceRecord]:
        if self.experiences_file.exists():
            with open(self.experiences_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {k: ExperienceRecord(**v) for k, v in data.items()}
        return {}
        
    def _save_experiences(self):
        with open(self.experiences_file, 'w', encoding='utf-8') as f:
            data = {k: asdict(v) for k, v in self.experiences.items()}
            json.dump(data, f, ensure_ascii=False, indent=2)
            
    def _load_patterns(self) -> Dict[str, OptimizationPattern]:
        if self.patterns_file.exists():
            with open(self.patterns_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {k: OptimizationPattern(**v) for k, v in data.items()}
        return {}
        
    def _save_patterns(self):
        with open(self.patterns_file, 'w', encoding='utf-8') as f:
            data = {k: asdict(v) for k, v in self.patterns.items()}
            json.dump(data, f, ensure_ascii=False, indent=2)
            
    def _load_ai_insights(self) -> Dict[str, Any]:
        if self.insights_file.exists():
            with open(self.insights_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
        
    def _save_ai_insights(self):
        with open(self.insights_file, 'w', encoding='utf-8') as f:
            json.dump(self.ai_insights, f, ensure_ascii=False, indent=2)
            
    def get_statistics(self) -> Dict[str, Any]:
        """获取经验知识库统计信息"""
        return {
            "total_experiences": len(self.experiences),
            "total_patterns": len(self.patterns),
            "categories": list(set(exp.category for exp in self.experiences.values())),
            "avg_confidence": sum(exp.confidence_score for exp in self.experiences.values()) / len(self.experiences) if self.experiences else 0,
            "most_reused_experience": max(self.experiences.values(), key=lambda x: x.reuse_count, default=None),
            "latest_insight_date": self.ai_insights.get("generated_at", "无")
        }

# 自适应学习组件
class AdaptiveLearningEngine:
    """自适应学习引擎"""
    
    def __init__(self, experience_kb: ExperienceKnowledgeBase):
        self.experience_kb = experience_kb
        self.logger = logging.getLogger(__name__)
        
    def analyze_user_interaction(self, interaction_data: Dict[str, Any]):
        """分析用户交互，学习用户模式"""
        # 分析用户问题模式
        # 记录系统响应效果
        # 识别需要改进的区域
        pass
        
    def suggest_proactive_optimizations(self) -> List[Dict[str, Any]]:
        """主动建议优化方案"""
        suggestions = []
        
        # 基于经验模式生成建议
        for pattern in self.experience_kb.patterns.values():
            if pattern.success_rate > 0.8:
                suggestions.append({
                    "type": "pattern_application",
                    "pattern": pattern.name,
                    "description": f"可以应用 {pattern.name} 来预防类似问题",
                    "confidence": pattern.success_rate
                })
                
        return suggestions
        
    def continuous_improvement_check(self):
        """持续改进检查"""
        # 检查系统性能指标
        # 识别性能瓶颈
        # 建议优化措施
        pass

# 使用示例
if __name__ == "__main__":
    # 创建经验知识库
    kb = ExperienceKnowledgeBase()
    
    # 记录当前会话的经验
    result = kb.record_current_session_experience()
    print(f"记录了 {result['recorded_experiences']} 个经验")
    
    # 获取统计信息
    stats = kb.get_statistics()
    print(f"知识库统计: {stats}")
    
    # 测试经验查找
    suggestion = kb.suggest_solution("PDF文档解析出现乱码")
    print(f"解决方案建议: {suggestion}")