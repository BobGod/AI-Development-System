#!/usr/bin/env python3
"""
智能行业知识问答系统 - 医疗领域适配器
专门处理医疗健康相关的问答需求
"""

from typing import Dict, List, Any, Optional
import re
from pathlib import Path

# 本地模块
import sys
sys.path.append(str(Path(__file__).parent.parent))
from domain_adapters.base_adapter import DomainAdapter, DomainKnowledge

class MedicalAdapter(DomainAdapter):
    """医疗领域适配器"""
    
    def __init__(self):
        super().__init__("医疗健康")
        
    def _init_domain_knowledge(self) -> DomainKnowledge:
        """初始化医疗领域知识"""
        return DomainKnowledge(
            domain_name="医疗健康",
            key_concepts=[
                "诊断", "治疗", "症状", "病因", "预防", "药物", "疾病",
                "临床", "病理", "生理", "解剖", "免疫", "感染", "炎症",
                "肿瘤", "癌症", "心血管", "呼吸系统", "消化系统", "神经系统",
                "内分泌", "骨科", "皮肤科", "妇科", "儿科", "精神科",
                "手术", "检查", "化验", "影像", "CT", "MRI", "X光",
                "血液", "尿液", "基因", "遗传", "营养", "运动", "康复"
            ],
            terminology={
                # 常见医学术语标准化
                "高血压": "高血压",
                "糖尿病": "糖尿病", 
                "心脏病": "心血管疾病",
                "感冒": "上呼吸道感染",
                "发烧": "发热",
                "头痛": "头痛",
                "胃痛": "胃部疼痛",
                "咳嗽": "咳嗽",
                "失眠": "睡眠障碍",
                "抑郁": "抑郁症",
                "肥胖": "肥胖症",
                "贫血": "贫血",
                "骨折": "骨折",
                "肺炎": "肺炎",
                "肝炎": "肝炎"
            },
            common_questions=[
                "这种症状可能是什么疾病？",
                "如何预防某种疾病？",
                "这种药物有什么副作用？",
                "手术后需要注意什么？",
                "如何进行康复训练？",
                "这种检查是否必要？",
                "饮食上需要注意什么？",
                "运动对这种疾病有帮助吗？",
                "如何识别疾病的早期症状？",
                "什么情况下需要立即就医？"
            ],
            expert_sources=[
                "医学教材", "临床指南", "医学期刊", "权威医院资料",
                "WHO报告", "国家卫健委文件", "医学专家著作"
            ],
            quality_indicators=[
                "临床证据", "循证医学", "指南推荐", "专家共识",
                "随机对照试验", "荟萃分析", "病例报告", "流行病学数据"
            ]
        )
        
    async def build_system_prompt(self, question: str) -> str:
        """构建医疗领域的系统提示词"""
        base_prompt = """你是一个专业的医疗健康咨询助手，具备以下专业能力：

1. 基于循证医学原则提供准确的医疗信息
2. 遵循医疗伦理，不提供具体诊断或治疗建议
3. 强调专业医疗机构的重要性
4. 提供科学、客观的健康知识
5. 识别医疗急症并建议及时就医

重要免责声明：
- 我的回答仅供健康教育和信息参考
- 不能替代专业医疗诊断和治疗
- 任何健康问题都应咨询合格的医疗专业人员
- 急症情况请立即就医或拨打急救电话

专业原则：
- 基于权威医学资料和临床指南
- 使用准确的医学术语
- 强调预防和健康生活方式
- 提醒用户个体差异的重要性"""

        # 根据问题类型调整提示词
        if self._is_emergency_question(question):
            base_prompt += "\n\n⚠️ 注意：如果涉及紧急医疗情况，请立即就医或拨打急救电话！"
            
        if self._is_medication_question(question):
            base_prompt += "\n\n💊 药物相关提醒：任何药物的使用都应在医生指导下进行，请勿自行用药。"
            
        if self._is_diagnosis_question(question):
            base_prompt += "\n\n🩺 诊断提醒：我无法提供医疗诊断，症状描述仅供参考，请咨询专业医生。"
            
        return base_prompt
        
    async def preprocess_question(self, question: str) -> str:
        """预处理医疗相关问题"""
        # 先调用基类的预处理
        processed = await super().preprocess_question(question)
        
        # 医疗特定的预处理
        
        # 1. 敏感词检测和提醒
        sensitive_patterns = [
            r'我是不是得了.*病',
            r'帮我诊断',
            r'这是什么病',
            r'需要吃什么药',
            r'用什么药治疗'
        ]
        
        for pattern in sensitive_patterns:
            if re.search(pattern, processed, re.IGNORECASE):
                processed += " [注意：我无法提供医疗诊断，请咨询专业医生]"
                break
                
        # 2. 紧急情况检测
        emergency_keywords = [
            '胸痛', '呼吸困难', '昏迷', '大出血', '中毒', '过敏反应',
            '急性腹痛', '高热不退', '意识模糊', '抽搐'
        ]
        
        if any(keyword in processed for keyword in emergency_keywords):
            processed += " [紧急提醒：如有紧急症状，请立即就医！]"
            
        return processed
        
    async def post_process_answer(self, answer_result, context, knowledge_results):
        """医疗领域的答案后处理"""
        # 调用基类的后处理
        answer_result = await super().post_process_answer(answer_result, context, knowledge_results)
        
        # 医疗特定的后处理
        
        # 1. 添加医疗免责声明（如果没有的话）
        if "仅供参考" not in answer_result.answer and "咨询医生" not in answer_result.answer:
            disclaimer = "\n\n⚠️ 重要提醒：以上信息仅供健康教育参考，不能替代专业医疗建议。如有健康问题，请咨询合格的医疗专业人员。"
            answer_result.answer += disclaimer
            
        # 2. 检查是否提供了不当的医疗建议
        inappropriate_phrases = [
            "你应该服用", "建议你吃", "这种药物适合你", "你的诊断是"
        ]
        
        if any(phrase in answer_result.answer for phrase in inappropriate_phrases):
            answer_result.confidence *= 0.3  # 大幅降低置信度
            warning = "\n\n⚠️ 警告：请勿根据此信息自行用药或诊断，务必咨询专业医生。"
            answer_result.answer += warning
            
        # 3. 增强紧急情况的提醒
        if any(keyword in context.question for keyword in ['胸痛', '呼吸困难', '昏迷', '大出血']):
            emergency_warning = "\n\n🚨 紧急情况提醒：如出现以上症状，请立即拨打120急救电话或前往最近的急诊科！"
            answer_result.answer = emergency_warning + "\n\n" + answer_result.answer
            
        return answer_result
        
    def _is_emergency_question(self, question: str) -> bool:
        """判断是否为紧急医疗问题"""
        emergency_indicators = [
            '急救', '紧急', '昏迷', '窒息', '大出血', '中毒', 
            '严重过敏', '心脏骤停', '中风', '急性心梗'
        ]
        
        return any(indicator in question for indicator in emergency_indicators)
        
    def _is_medication_question(self, question: str) -> bool:
        """判断是否为药物相关问题"""
        medication_indicators = [
            '药', '服用', '用量', '副作用', '药物', '治疗',
            '吃什么', '用什么', '抗生素', '止痛', '降压'
        ]
        
        return any(indicator in question for indicator in medication_indicators)
        
    def _is_diagnosis_question(self, question: str) -> bool:
        """判断是否为诊断相关问题"""
        diagnosis_indicators = [
            '诊断', '是什么病', '得了', '患了', '症状',
            '检查结果', '化验单', '这是', '可能是'
        ]
        
        return any(indicator in question for indicator in diagnosis_indicators)
        
    async def validate_answer_quality(self, answer: str, question: str):
        """医疗领域的答案质量验证"""
        is_valid, issues = await super().validate_answer_quality(answer, question)
        
        # 医疗特定的质量检查
        medical_issues = []
        
        # 检查是否包含不当的医疗建议
        inappropriate_advice = [
            "你应该服用", "建议你用药", "这种药适合", "诊断为"
        ]
        
        if any(advice in answer for advice in inappropriate_advice):
            medical_issues.append("包含不当的医疗建议")
            
        # 检查是否缺少必要的免责声明
        if len(answer) > 100 and "仅供参考" not in answer and "咨询医生" not in answer:
            medical_issues.append("缺少医疗免责声明")
            
        # 检查医学术语的准确性（简单检查）
        medical_terms = ['诊断', '治疗', '症状', '疾病']
        if any(term in question for term in medical_terms) and not any(term in answer for term in medical_terms):
            medical_issues.append("医学术语使用不足")
            
        # 合并问题列表
        all_issues = issues + medical_issues
        final_valid = is_valid and len(medical_issues) == 0
        
        return final_valid, all_issues
        
    async def suggest_related_questions(self, question: str) -> List[str]:
        """为医疗问题建议相关问题"""
        related = await super().suggest_related_questions(question)
        
        # 基于问题类型添加医疗特定的相关问题
        question_lower = question.lower()
        
        if '症状' in question_lower:
            related.extend([
                "这种症状的常见原因是什么？",
                "出现这种症状时应该注意什么？",
                "什么情况下需要立即就医？"
            ])
            
        if '预防' in question_lower:
            related.extend([
                "日常生活中如何预防？",
                "饮食上有什么注意事项？",
                "运动对预防有帮助吗？"
            ])
            
        if '药物' in question_lower or '药' in question_lower:
            related.extend([
                "这种药物有什么副作用？",
                "用药期间需要注意什么？",
                "是否有替代的治疗方法？"
            ])
            
        # 去重并限制数量
        unique_related = list(dict.fromkeys(related))
        return unique_related[:8]
        
    def get_medical_specialties(self) -> List[str]:
        """获取医疗专科列表"""
        return [
            "内科", "外科", "妇产科", "儿科", "眼科", "耳鼻喉科",
            "皮肤科", "神经科", "精神科", "骨科", "泌尿科", "肿瘤科",
            "心血管科", "呼吸科", "消化科", "内分泌科", "肾内科",
            "血液科", "风湿免疫科", "感染科", "急诊科", "康复科"
        ]
        
    def classify_medical_question(self, question: str) -> str:
        """分类医疗问题"""
        question_lower = question.lower()
        
        # 按症状分类
        if any(word in question_lower for word in ['头痛', '头晕', '记忆']):
            return "神经系统"
        elif any(word in question_lower for word in ['胸痛', '心悸', '血压']):
            return "心血管系统"
        elif any(word in question_lower for word in ['咳嗽', '呼吸', '肺']):
            return "呼吸系统"
        elif any(word in question_lower for word in ['胃痛', '腹痛', '消化']):
            return "消化系统"
        elif any(word in question_lower for word in ['皮肤', '过敏', '湿疹']):
            return "皮肤系统"
        elif any(word in question_lower for word in ['关节', '骨头', '肌肉']):
            return "骨骼肌肉系统"
        elif any(word in question_lower for word in ['抑郁', '焦虑', '情绪']):
            return "心理健康"
        else:
            return "全科医学"

# 使用示例
async def main():
    """测试医疗适配器"""
    adapter = MedicalAdapter()
    
    # 测试问题预处理
    test_questions = [
        "我头痛是不是得了什么病？",
        "胸痛应该吃什么药？",
        "这种症状正常吗？"
    ]
    
    for question in test_questions:
        processed = await adapter.preprocess_question(question)
        print(f"原问题: {question}")
        print(f"处理后: {processed}")
        print(f"分类: {adapter.classify_medical_question(question)}")
        
        # 测试相关问题建议
        related = await adapter.suggest_related_questions(question)
        print(f"相关问题: {related[:3]}")
        print("-" * 50)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())