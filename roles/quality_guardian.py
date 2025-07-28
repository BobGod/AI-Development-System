#!/usr/bin/env python3
"""
AI自主开发系统 - 质量守护者
负责代码质量控制、静态分析、代码规范检查、技术债务管理
"""

import asyncio
import logging
import json
import hashlib
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, asdict
import uuid

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from roles.base_role import BaseRole, Task, TaskStatus, RoleState

class QualityLevel(Enum):
    """质量等级枚举"""
    EXCELLENT = "excellent"      # 优秀 (90-100分)
    GOOD = "good"               # 良好 (80-89分)  
    ACCEPTABLE = "acceptable"    # 可接受 (70-79分)
    POOR = "poor"               # 较差 (60-69分)
    CRITICAL = "critical"       # 严重 (0-59分)

class IssueType(Enum):
    """问题类型枚举"""
    SECURITY = "security"           # 安全问题
    BUG = "bug"                    # 功能缺陷
    CODE_SMELL = "code_smell"      # 代码异味
    DUPLICATION = "duplication"    # 代码重复
    COMPLEXITY = "complexity"      # 复杂度问题
    STYLE = "style"               # 风格问题
    PERFORMANCE = "performance"    # 性能问题
    MAINTAINABILITY = "maintainability"  # 可维护性

class IssueSeverity(Enum):
    """问题严重程度枚举"""
    BLOCKER = "blocker"      # 阻断
    CRITICAL = "critical"    # 严重
    MAJOR = "major"         # 重大
    MINOR = "minor"         # 轻微
    INFO = "info"           # 信息

class TechDebtType(Enum):
    """技术债务类型枚举"""
    DESIGN_DEBT = "design_debt"     # 设计债务
    CODE_DEBT = "code_debt"         # 代码债务
    TEST_DEBT = "test_debt"         # 测试债务  
    DOC_DEBT = "doc_debt"           # 文档债务
    BUILD_DEBT = "build_debt"       # 构建债务

@dataclass
class QualityIssue:
    """质量问题数据类"""
    issue_id: str
    issue_type: IssueType
    severity: IssueSeverity
    file_path: str
    line_number: int
    message: str
    rule_id: str
    suggestion: str = ""
    created_at: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

@dataclass
class QualityMetrics:
    """质量指标数据类"""
    overall_score: float
    maintainability_index: float
    complexity_score: float
    duplication_ratio: float
    test_coverage: float
    security_issues: int
    code_smells: int
    bugs: int
    tech_debt_ratio: float
    lines_of_code: int
    analyzed_at: str = ""
    
    def __post_init__(self):
        if not self.analyzed_at:
            self.analyzed_at = datetime.now().isoformat()

@dataclass  
class TechDebt:
    """技术债务数据类"""
    debt_id: str
    debt_type: TechDebtType
    description: str
    file_path: str
    estimated_hours: float
    priority: str
    status: str = "open"
    assigned_to: str = ""
    created_at: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

class QualityGuardian(BaseRole):
    """质量守护者 - 负责代码质量控制和技术债务管理"""
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(
            role_id="quality_guardian",
            role_name="质量守护者", 
            config=config
        )
        
        # 质量规则配置
        self.quality_rules = self._init_quality_rules()
        
        # 质量指标存储
        self.quality_metrics: Dict[str, QualityMetrics] = {}
        self.quality_issues: Dict[str, List[QualityIssue]] = {}
        self.tech_debts: Dict[str, TechDebt] = {}
        
        # 质量门禁配置
        self.quality_gates = self._init_quality_gates()
        
        # 分析工具配置
        self.analysis_tools = self._init_analysis_tools()
        
        # 质量历史记录
        self.quality_history: List[Dict] = []
        
        # 消息处理器映射
        self.message_handlers.update({
            'analyze_code': self._handle_analyze_code,
            'check_quality_gates': self._handle_check_quality_gates,  
            'scan_security': self._handle_scan_security,
            'detect_duplicates': self._handle_detect_duplicates,
            'analyze_complexity': self._handle_analyze_complexity,
            'manage_tech_debt': self._handle_manage_tech_debt,
            'generate_quality_report': self._handle_generate_quality_report,
            'update_quality_rules': self._handle_update_quality_rules
        })
        
        self.logger.info(f"{self.role_name} 初始化完成")
        
    def _init_quality_rules(self) -> Dict[str, Any]:
        """初始化质量规则"""
        return {
            'complexity': {
                'max_cyclomatic_complexity': 10,
                'max_cognitive_complexity': 15,
                'max_function_length': 50,
                'max_class_length': 500
            },
            'duplication': {
                'max_duplication_ratio': 0.05,  # 5%
                'min_duplicate_lines': 6
            },
            'coverage': {
                'min_line_coverage': 0.80,  # 80%
                'min_branch_coverage': 0.75  # 75%
            },
            'maintainability': {
                'min_maintainability_index': 80
            },
            'security': {
                'block_critical_vulnerabilities': True,
                'block_high_vulnerabilities': True,
                'allow_medium_vulnerabilities': 5,
                'allow_low_vulnerabilities': 20
            },
            'style': {
                'enforce_naming_conventions': True,
                'enforce_formatting': True,
                'max_line_length': 120
            }
        }
        
    def _init_quality_gates(self) -> Dict[str, Any]:
        """初始化质量门禁"""
        return {
            'blocking_conditions': [
                {'type': 'security', 'severity': 'critical', 'threshold': 0},
                {'type': 'security', 'severity': 'high', 'threshold': 0},
                {'type': 'bug', 'severity': 'critical', 'threshold': 0},
                {'type': 'complexity', 'max_increase': 0.1},  # 复杂度增长不超过10%
                {'type': 'coverage', 'min_decrease': 0.05}   # 覆盖率下降不超过5%
            ],
            'warning_conditions': [
                {'type': 'code_smell', 'severity': 'major', 'threshold': 5},
                {'type': 'duplication', 'max_ratio': 0.03},
                {'type': 'maintainability', 'min_score': 75}
            ]
        }
        
    def _init_analysis_tools(self) -> Dict[str, Any]:
        """初始化分析工具配置"""
        return {
            'python': {
                'linters': ['pylint', 'flake8', 'bandit', 'mypy'],
                'complexity': ['radon', 'mccabe'],
                'security': ['bandit', 'safety'],
                'style': ['black', 'isort', 'autopep8']
            },
            'javascript': {
                'linters': ['eslint', 'jshint'],
                'complexity': ['complexity-report'],
                'security': ['npm-audit', 'snyk'],
                'style': ['prettier']
            },
            'typescript': {
                'linters': ['tslint', 'eslint'],
                'complexity': ['ts-complexity'],
                'security': ['tslint-config-security'],
                'style': ['prettier']
            },
            'java': {
                'linters': ['spotbugs', 'pmd', 'checkstyle'],
                'complexity': ['pmd'],
                'security': ['spotbugs-security'],
                'style': ['checkstyle']
            }
        }
        
    async def _handle_analyze_code(self, message):
        """处理代码分析请求"""
        try:
            data = message.body.data
            file_path = data.get('file_path')
            code_content = data.get('code_content', '')
            language = data.get('language', 'unknown')
            
            self.logger.info(f"开始分析代码: {file_path}")
            
            # 执行多维度代码分析
            analysis_results = await self._perform_code_analysis(
                file_path, code_content, language
            )
            
            # 生成质量指标
            metrics = await self._calculate_quality_metrics(analysis_results)
            
            # 存储结果
            self.quality_metrics[file_path] = metrics
            self.quality_issues[file_path] = analysis_results.get('issues', [])
            
            # 记录历史
            self.quality_history.append({
                'file_path': file_path,
                'timestamp': datetime.now().isoformat(),
                'metrics': asdict(metrics),
                'issues_count': len(analysis_results.get('issues', []))
            })
            
            response_data = {
                'file_path': file_path,
                'quality_level': self._determine_quality_level(metrics.overall_score),
                'metrics': asdict(metrics),
                'issues': [asdict(issue) for issue in analysis_results.get('issues', [])],
                'recommendations': analysis_results.get('recommendations', [])
            }
            
            await self._send_response(message, 'quality_analysis_result', response_data)
            self.logger.info(f"代码分析完成: {file_path}, 质量分数: {metrics.overall_score:.1f}")
            
        except Exception as e:
            self.logger.error(f"代码分析失败: {e}")
            await self._send_error_response(message, str(e))
            
    async def _perform_code_analysis(self, file_path: str, code_content: str, language: str) -> Dict[str, Any]:
        """执行代码分析"""
        issues = []
        recommendations = []
        
        # 1. 复杂度分析
        complexity_issues = await self._analyze_complexity(code_content, language)
        issues.extend(complexity_issues)
        
        # 2. 重复代码检测
        duplication_issues = await self._detect_duplicates(code_content, file_path)
        issues.extend(duplication_issues)
        
        # 3. 安全扫描
        security_issues = await self._scan_security(code_content, language)
        issues.extend(security_issues)
        
        # 4. 代码风格检查
        style_issues = await self._check_code_style(code_content, language)
        issues.extend(style_issues)
        
        # 5. 生成建议
        recommendations = await self._generate_recommendations(issues, code_content)
        
        return {
            'issues': issues,
            'recommendations': recommendations,
            'analysis_timestamp': datetime.now().isoformat()
        }
        
    async def _analyze_complexity(self, code_content: str, language: str) -> List[QualityIssue]:
        """分析代码复杂度"""
        issues = []
        
        if language == 'python':
            # 简化的Python复杂度分析
            lines = code_content.split('\n')
            
            for i, line in enumerate(lines, 1):
                line = line.strip()
                
                # 检查函数长度
                if line.startswith('def '):
                    func_lines = self._count_function_lines(lines, i-1)
                    if func_lines > self.quality_rules['complexity']['max_function_length']:
                        issues.append(QualityIssue(
                            issue_id=str(uuid.uuid4()),
                            issue_type=IssueType.COMPLEXITY,
                            severity=IssueSeverity.MAJOR,
                            file_path="",
                            line_number=i,
                            message=f"函数过长: {func_lines} 行 (最大 {self.quality_rules['complexity']['max_function_length']} 行)",
                            rule_id="max_function_length",
                            suggestion="考虑将函数拆分为更小的函数"
                        ))
                
                # 检查嵌套深度
                indent_level = (len(line) - len(line.lstrip())) // 4
                if indent_level > 4:
                    issues.append(QualityIssue(
                        issue_id=str(uuid.uuid4()),
                        issue_type=IssueType.COMPLEXITY,
                        severity=IssueSeverity.MINOR,
                        file_path="",
                        line_number=i,
                        message=f"嵌套层次过深: {indent_level} 层",
                        rule_id="max_nesting_depth",
                        suggestion="考虑使用早期返回或提取函数来减少嵌套"
                    ))
        
        return issues
        
    def _count_function_lines(self, lines: List[str], start_index: int) -> int:
        """计算函数行数"""
        count = 1
        base_indent = len(lines[start_index]) - len(lines[start_index].lstrip())
        
        for i in range(start_index + 1, len(lines)):
            line = lines[i].strip()
            if not line:  # 空行
                continue
                
            current_indent = len(lines[i]) - len(lines[i].lstrip())
            if current_indent <= base_indent and line:
                break
                
            count += 1
            
        return count
        
    async def _detect_duplicates(self, code_content: str, file_path: str) -> List[QualityIssue]:
        """检测重复代码"""
        issues = []
        lines = code_content.split('\n')
        
        # 简化的重复检测：查找相同的代码块
        seen_blocks = {}
        block_size = 6  # 最小重复块大小
        
        for i in range(len(lines) - block_size + 1):
            block = '\n'.join(lines[i:i+block_size])
            block_hash = hashlib.md5(block.encode()).hexdigest()
            
            if block_hash in seen_blocks:
                issues.append(QualityIssue(
                    issue_id=str(uuid.uuid4()),
                    issue_type=IssueType.DUPLICATION,
                    severity=IssueSeverity.MAJOR,
                    file_path=file_path,
                    line_number=i+1,
                    message=f"发现重复代码块 ({block_size} 行)",
                    rule_id="duplicate_code_block",
                    suggestion="考虑提取公共函数或使用设计模式消除重复"
                ))
            else:
                seen_blocks[block_hash] = i+1
                
        return issues
        
    async def _scan_security(self, code_content: str, language: str) -> List[QualityIssue]:
        """扫描安全问题"""
        issues = []
        
        # 简化的安全扫描规则
        security_patterns = {
            'hardcoded_password': {
                'pattern': r'password\s*=\s*["\'][^"\']*["\']',
                'message': '发现硬编码密码',
                'severity': IssueSeverity.CRITICAL
            },
            'sql_injection': {
                'pattern': r'execute\s*\(\s*["\'].*%.*["\']',
                'message': '可能存在SQL注入风险',
                'severity': IssueSeverity.CRITICAL
            },
            'xss_vulnerability': {
                'pattern': r'innerHTML\s*=.*\+',
                'message': '可能存在XSS漏洞',
                'severity': IssueSeverity.MAJOR
            }
        }
        
        lines = code_content.split('\n')
        for i, line in enumerate(lines, 1):
            for rule_id, rule in security_patterns.items():
                if re.search(rule['pattern'], line, re.IGNORECASE):
                    issues.append(QualityIssue(
                        issue_id=str(uuid.uuid4()),
                        issue_type=IssueType.SECURITY,
                        severity=rule['severity'],
                        file_path="",
                        line_number=i,
                        message=rule['message'],
                        rule_id=rule_id,
                        suggestion="请使用安全的编程实践"
                    ))
                    
        return issues
        
    async def _check_code_style(self, code_content: str, language: str) -> List[QualityIssue]:
        """检查代码风格"""
        issues = []
        lines = code_content.split('\n')
        
        for i, line in enumerate(lines, 1):
            # 检查行长度
            if len(line) > self.quality_rules['style']['max_line_length']:
                issues.append(QualityIssue(
                    issue_id=str(uuid.uuid4()),
                    issue_type=IssueType.STYLE,
                    severity=IssueSeverity.MINOR,
                    file_path="",
                    line_number=i,
                    message=f"行长度超限: {len(line)} 字符 (最大 {self.quality_rules['style']['max_line_length']} 字符)",
                    rule_id="max_line_length",
                    suggestion="考虑拆分长行或使用更短的变量名"
                ))
            
            # 检查命名规范（Python示例）
            if language == 'python':
                # 检查类名（应该是PascalCase）
                if re.match(r'^\s*class\s+([a-z])', line):
                    issues.append(QualityIssue(
                        issue_id=str(uuid.uuid4()),
                        issue_type=IssueType.STYLE,
                        severity=IssueSeverity.MINOR,
                        file_path="",
                        line_number=i,
                        message="类名应使用PascalCase命名规范",
                        rule_id="class_naming_convention",
                        suggestion="将类名首字母大写"
                    ))
                    
        return issues
        
    async def _generate_recommendations(self, issues: List[QualityIssue], code_content: str) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        # 按问题类型统计
        issue_counts = {}
        for issue in issues:
            issue_type = issue.issue_type.value
            issue_counts[issue_type] = issue_counts.get(issue_type, 0) + 1
            
        # 生成针对性建议
        if issue_counts.get('complexity', 0) > 0:
            recommendations.append("建议使用设计模式和重构技术降低代码复杂度")
            
        if issue_counts.get('duplication', 0) > 0:
            recommendations.append("建议提取公共方法或使用继承来消除代码重复")
            
        if issue_counts.get('security', 0) > 0:
            recommendations.append("建议使用安全编程最佳实践，避免安全漏洞")
            
        if issue_counts.get('style', 0) > 0:
            recommendations.append("建议使用代码格式化工具统一代码风格")
            
        return recommendations
        
    async def _calculate_quality_metrics(self, analysis_results: Dict[str, Any]) -> QualityMetrics:
        """计算质量指标"""
        issues = analysis_results.get('issues', [])
        
        # 按严重程度统计问题
        critical_issues = len([i for i in issues if i.severity == IssueSeverity.CRITICAL])
        major_issues = len([i for i in issues if i.severity == IssueSeverity.MAJOR])
        minor_issues = len([i for i in issues if i.severity == IssueSeverity.MINOR])
        
        # 按类型统计问题
        security_issues = len([i for i in issues if i.issue_type == IssueType.SECURITY])
        bugs = len([i for i in issues if i.issue_type == IssueType.BUG])
        code_smells = len([i for i in issues if i.issue_type == IssueType.CODE_SMELL])
        
        # 计算综合质量分数 (0-100)
        overall_score = 100.0
        overall_score -= critical_issues * 20  # 严重问题扣20分
        overall_score -= major_issues * 5      # 重大问题扣5分
        overall_score -= minor_issues * 1      # 轻微问题扣1分
        overall_score = max(0, overall_score)  # 最低0分
        
        # 简化的指标计算
        maintainability_index = max(0, 100 - major_issues * 5 - minor_issues * 2)
        complexity_score = max(0, 100 - len([i for i in issues if i.issue_type == IssueType.COMPLEXITY]) * 10)
        duplication_ratio = len([i for i in issues if i.issue_type == IssueType.DUPLICATION]) * 0.01
        tech_debt_ratio = (critical_issues * 0.1 + major_issues * 0.05 + minor_issues * 0.01)
        
        return QualityMetrics(
            overall_score=overall_score,
            maintainability_index=maintainability_index,
            complexity_score=complexity_score,
            duplication_ratio=duplication_ratio,
            test_coverage=85.0,  # 模拟值
            security_issues=security_issues,
            code_smells=code_smells,
            bugs=bugs,
            tech_debt_ratio=tech_debt_ratio,
            lines_of_code=len(analysis_results.get('code_content', '').split('\n'))
        )
        
    def _determine_quality_level(self, score: float) -> QualityLevel:
        """确定质量等级"""
        if score >= 90:
            return QualityLevel.EXCELLENT
        elif score >= 80:
            return QualityLevel.GOOD
        elif score >= 70:
            return QualityLevel.ACCEPTABLE
        elif score >= 60:
            return QualityLevel.POOR
        else:
            return QualityLevel.CRITICAL
            
    async def _handle_check_quality_gates(self, message):
        """处理质量门禁检查"""
        try:
            data = message.body.data
            file_path = data.get('file_path')
            change_type = data.get('change_type', 'modification')
            
            self.logger.info(f"检查质量门禁: {file_path}")
            
            # 获取当前质量指标
            current_metrics = self.quality_metrics.get(file_path)
            current_issues = self.quality_issues.get(file_path, [])
            
            if not current_metrics:
                await self._send_error_response(message, "未找到质量指标，请先执行代码分析")
                return
                
            # 检查阻断条件
            blocking_violations = []
            warning_violations = []
            
            for condition in self.quality_gates['blocking_conditions']:
                violation = await self._check_gate_condition(condition, current_metrics, current_issues)
                if violation:
                    blocking_violations.append(violation)
                    
            for condition in self.quality_gates['warning_conditions']:
                violation = await self._check_gate_condition(condition, current_metrics, current_issues)
                if violation:
                    warning_violations.append(violation)
                    
            # 确定门禁状态
            gate_status = "PASSED"
            if blocking_violations:
                gate_status = "BLOCKED"
            elif warning_violations:
                gate_status = "WARNING"
                
            response_data = {
                'file_path': file_path,
                'gate_status': gate_status,
                'blocking_violations': blocking_violations,
                'warning_violations': warning_violations,
                'quality_score': current_metrics.overall_score,
                'recommendations': self._generate_gate_recommendations(blocking_violations, warning_violations)
            }
            
            await self._send_response(message, 'quality_gate_status', response_data)
            self.logger.info(f"质量门禁检查完成: {file_path}, 状态: {gate_status}")
            
        except Exception as e:
            self.logger.error(f"质量门禁检查失败: {e}")
            await self._send_error_response(message, str(e))
            
    async def _check_gate_condition(self, condition: Dict, metrics: QualityMetrics, issues: List[QualityIssue]) -> Optional[str]:
        """检查门禁条件"""
        condition_type = condition.get('type')
        threshold = condition.get('threshold', 0)
        
        if condition_type == 'security':
            severity = condition.get('severity')
            count = len([i for i in issues if i.issue_type == IssueType.SECURITY and i.severity.value == severity])
            if count > threshold:
                return f"安全问题超标: {count} 个 {severity} 级别问题 (阈值: {threshold})"
                
        elif condition_type == 'bug':
            severity = condition.get('severity')
            count = len([i for i in issues if i.issue_type == IssueType.BUG and i.severity.value == severity])
            if count > threshold:
                return f"功能缺陷超标: {count} 个 {severity} 级别缺陷 (阈值: {threshold})"
                
        elif condition_type == 'coverage':
            min_decrease = condition.get('min_decrease', 0.05)
            # 这里应该与历史覆盖率比较，简化处理
            if metrics.test_coverage < 0.75:  # 假设之前覆盖率是80%
                return f"测试覆盖率下降过多: 当前 {metrics.test_coverage:.1%} (最小允许下降: {min_decrease:.1%})"
                
        elif condition_type == 'complexity':
            max_increase = condition.get('max_increase', 0.1)
            # 简化处理：如果复杂度得分低于70，认为增长过多
            if metrics.complexity_score < 70:
                return f"代码复杂度增长过多: 当前得分 {metrics.complexity_score:.1f} (最大允许增长: {max_increase:.1%})"
                
        return None
        
    def _generate_gate_recommendations(self, blocking_violations: List[str], warning_violations: List[str]) -> List[str]:
        """生成门禁建议"""
        recommendations = []
        
        if blocking_violations:
            recommendations.append("🚫 发现阻断问题，必须修复后才能合并代码")
            for violation in blocking_violations:
                recommendations.append(f"  - {violation}")
                
        if warning_violations:
            recommendations.append("⚠️ 发现警告问题，建议修复以提高代码质量")
            for violation in warning_violations:
                recommendations.append(f"  - {violation}")
                
        if not blocking_violations and not warning_violations:
            recommendations.append("✅ 代码质量良好，符合所有质量门禁要求")
            
        return recommendations
        
    async def _handle_manage_tech_debt(self, message):
        """处理技术债务管理"""
        try:
            data = message.body.data
            action = data.get('action')  # create, update, list, prioritize
            
            if action == 'create':
                debt = await self._create_tech_debt(data)
                response_data = {'action': 'created', 'debt': asdict(debt)}
            elif action == 'update':
                debt = await self._update_tech_debt(data)
                response_data = {'action': 'updated', 'debt': asdict(debt)}
            elif action == 'list':
                debts = await self._list_tech_debts(data)
                response_data = {'action': 'listed', 'debts': [asdict(d) for d in debts]}
            elif action == 'prioritize':
                prioritized_debts = await self._prioritize_tech_debts()
                response_data = {'action': 'prioritized', 'debts': [asdict(d) for d in prioritized_debts]}
            else:
                raise ValueError(f"不支持的操作: {action}")
                
            await self._send_response(message, 'tech_debt_update', response_data)
            self.logger.info(f"技术债务管理完成: {action}")
            
        except Exception as e:
            self.logger.error(f"技术债务管理失败: {e}")
            await self._send_error_response(message, str(e))
            
    async def _create_tech_debt(self, data: Dict) -> TechDebt:
        """创建技术债务记录"""
        debt = TechDebt(
            debt_id=str(uuid.uuid4()),
            debt_type=TechDebtType(data.get('debt_type', 'code_debt')),
            description=data.get('description', ''),
            file_path=data.get('file_path', ''),
            estimated_hours=data.get('estimated_hours', 0.0),
            priority=data.get('priority', 'medium'),
            assigned_to=data.get('assigned_to', '')
        )
        
        self.tech_debts[debt.debt_id] = debt
        return debt
        
    async def _handle_generate_quality_report(self, message):
        """处理质量报告生成"""
        try:
            data = message.body.data
            report_type = data.get('report_type', 'summary')  # summary, detailed, trend
            time_range = data.get('time_range', '7d')  # 7d, 30d, 90d
            
            self.logger.info(f"生成质量报告: {report_type}")
            
            if report_type == 'summary':
                report = await self._generate_summary_report()
            elif report_type == 'detailed':
                report = await self._generate_detailed_report()
            elif report_type == 'trend':
                report = await self._generate_trend_report(time_range)
            else:
                raise ValueError(f"不支持的报告类型: {report_type}")
                
            response_data = {
                'report_type': report_type,
                'generated_at': datetime.now().isoformat(),
                'report': report
            }
            
            await self._send_response(message, 'quality_report', response_data)
            self.logger.info(f"质量报告生成完成: {report_type}")
            
        except Exception as e:
            self.logger.error(f"质量报告生成失败: {e}")
            await self._send_error_response(message, str(e))
            
    async def _generate_summary_report(self) -> Dict[str, Any]:
        """生成摘要报告"""
        total_files = len(self.quality_metrics)
        if total_files == 0:
            return {'message': '暂无质量数据'}
            
        # 计算平均指标
        total_score = sum(m.overall_score for m in self.quality_metrics.values())
        avg_score = total_score / total_files
        
        total_issues = sum(len(issues) for issues in self.quality_issues.values())
        
        # 统计问题分布
        issue_distribution = {}
        for issues in self.quality_issues.values():
            for issue in issues:
                issue_type = issue.issue_type.value
                issue_distribution[issue_type] = issue_distribution.get(issue_type, 0) + 1
                
        # 质量等级分布
        quality_distribution = {}
        for metrics in self.quality_metrics.values():
            level = self._determine_quality_level(metrics.overall_score).value
            quality_distribution[level] = quality_distribution.get(level, 0) + 1
            
        return {
            'summary': {
                'total_files_analyzed': total_files,
                'average_quality_score': round(avg_score, 1),
                'total_issues': total_issues,
                'total_tech_debts': len(self.tech_debts)
            },
            'quality_distribution': quality_distribution,
            'issue_distribution': issue_distribution,
            'top_issues': self._get_top_issues(5),
            'recommendations': self._get_summary_recommendations()
        }
    
    def _get_top_issues(self, limit: int) -> List[Dict]:
        """获取最严重的问题"""
        all_issues = []
        for file_path, issues in self.quality_issues.items():
            for issue in issues:
                all_issues.append({
                    'file_path': file_path,
                    'issue': asdict(issue)
                })
                
        # 按严重程度排序
        severity_order = {
            IssueSeverity.BLOCKER: 0,
            IssueSeverity.CRITICAL: 1,
            IssueSeverity.MAJOR: 2,
            IssueSeverity.MINOR: 3,
            IssueSeverity.INFO: 4
        }
        
        all_issues.sort(key=lambda x: severity_order.get(
            IssueSeverity(x['issue']['severity']), 5
        ))
        
        return all_issues[:limit]
        
    def _get_summary_recommendations(self) -> List[str]:
        """获取总体建议"""
        recommendations = []
        
        if len(self.quality_metrics) == 0:
            return ["建议开始对代码进行质量分析"]
            
        avg_score = sum(m.overall_score for m in self.quality_metrics.values()) / len(self.quality_metrics)
        
        if avg_score < 60:
            recommendations.append("🚨 整体代码质量较差，建议立即开始重构工作")
        elif avg_score < 80:
            recommendations.append("⚠️ 代码质量需要改进，建议制定质量提升计划")
        else:
            recommendations.append("✅ 代码质量良好，建议保持现有标准")
            
        # 基于技术债务提供建议
        if len(self.tech_debts) > 10:
            recommendations.append("📋 技术债务较多，建议优先处理高优先级债务")
            
        return recommendations
        
    async def _initialize_role(self):
        """初始化角色特定资源"""
        self.logger.info(f"{self.role_name} 角色初始化完成")
        
    async def _cleanup_role(self):
        """清理角色特定资源"""
        self.logger.info(f"{self.role_name} 角色清理完成")
        
    async def _process_task(self, task: Task):
        """处理任务"""
        self.logger.info(f"处理任务: {task.task_id}")
        # 简化处理
        task.status = TaskStatus.COMPLETED
        
    async def _handle_custom_message(self, message):
        """处理自定义消息"""
        self.logger.info(f"收到自定义消息: {message}")
        return "处理完成"
        
    async def _handle_scan_security(self, message):
        """处理安全扫描请求"""
        try:
            data = message.body.data
            code_content = data.get('code_content', '')
            language = data.get('language', 'unknown')
            
            self.logger.info("开始安全扫描")
            
            # 执行安全扫描
            security_issues = await self._scan_security(code_content, language)
            
            response_data = {
                'scan_completed': True,
                'issues_found': len(security_issues),
                'security_issues': [asdict(issue) for issue in security_issues]
            }
            
            await self._send_response(message, 'security_scan_result', response_data)
            self.logger.info(f"安全扫描完成，发现 {len(security_issues)} 个问题")
            
        except Exception as e:
            self.logger.error(f"安全扫描失败: {e}")
            await self._send_error_response(message, str(e))
            
    async def _handle_detect_duplicates(self, message):
        """处理重复代码检测请求"""
        try:
            data = message.body.data
            code_content = data.get('code_content', '')
            file_path = data.get('file_path', '')
            
            self.logger.info("开始重复代码检测")
            
            # 执行重复代码检测
            duplicate_issues = await self._detect_duplicates(code_content, file_path)
            
            response_data = {
                'detection_completed': True,
                'duplicates_found': len(duplicate_issues),
                'duplicate_issues': [asdict(issue) for issue in duplicate_issues]
            }
            
            await self._send_response(message, 'duplication_report', response_data)
            self.logger.info(f"重复代码检测完成，发现 {len(duplicate_issues)} 个问题")
            
        except Exception as e:
            self.logger.error(f"重复代码检测失败: {e}")
            await self._send_error_response(message, str(e))
            
    async def _handle_analyze_complexity(self, message):
        """处理复杂度分析请求"""
        try:
            data = message.body.data
            code_content = data.get('code_content', '')
            language = data.get('language', 'unknown')
            
            self.logger.info("开始复杂度分析")
            
            # 执行复杂度分析
            complexity_issues = await self._analyze_complexity(code_content, language)
            
            response_data = {
                'analysis_completed': True,
                'complexity_issues_found': len(complexity_issues),
                'complexity_issues': [asdict(issue) for issue in complexity_issues]
            }
            
            await self._send_response(message, 'complexity_analysis', response_data)
            self.logger.info(f"复杂度分析完成，发现 {len(complexity_issues)} 个问题")
            
        except Exception as e:
            self.logger.error(f"复杂度分析失败: {e}")
            await self._send_error_response(message, str(e))
            
    async def _handle_update_quality_rules(self, message):
        """处理质量规则更新请求"""
        try:
            data = message.body.data
            rule_updates = data.get('rule_updates', {})
            
            self.logger.info("开始更新质量规则")
            
            # 更新质量规则
            for rule_category, rule_values in rule_updates.items():
                if rule_category in self.quality_rules:
                    self.quality_rules[rule_category].update(rule_values)
                    
            response_data = {
                'update_completed': True,
                'updated_rules': list(rule_updates.keys()),
                'current_rules': self.quality_rules
            }
            
            await self._send_response(message, 'quality_rules_updated', response_data)
            self.logger.info(f"质量规则更新完成，更新了 {len(rule_updates)} 个规则类别")
            
        except Exception as e:
            self.logger.error(f"质量规则更新失败: {e}")
            await self._send_error_response(message, str(e))