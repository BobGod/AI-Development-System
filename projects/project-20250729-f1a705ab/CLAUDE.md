# 🧠 Claude Code 项目记忆系统

这个文件记录了Claude在开发过程中积累的项目知识、调试经验和优化方案，作为项目的持久记忆。

## 📋 项目概述

**智能行业知识问答系统** - 基于DeepSeek大模型的多领域智能知识问答API
- 支持PDF、Word、Excel、图片等多种文档格式
- 使用ChromaDB向量数据库存储和检索知识
- 集成10个专业AI角色，支持多领域问答
- 具备会话记忆和上下文理解能力

## 🛠️ 核心技术栈

### 后端技术
- **Python 3.13** - 主要开发语言
- **FastAPI** - Web框架和API服务
- **DeepSeek API** - 大语言模型服务
- **ChromaDB** - 向量数据库
- **Sentence Transformers** - 文本嵌入模型(all-MiniLM-L6-v2)

### 文档处理
- **pdfplumber** - PDF解析(优选，中文支持好)
- **PyMuPDF (fitz)** - PDF解析备选方案
- **python-docx** - Word文档处理
- **openpyxl** - Excel文档处理
- **pytesseract** - OCR文字识别

### 前端技术
- **Vue.js** - 用户界面框架
- **HTML/CSS/JavaScript** - Web前端技术

## 🔧 重要调试经验

### PDF解析编码问题 (2025-07-30)

**问题**: PDF文档解析出现中文乱码，导致AI无法使用上传的文档知识

**根本原因**:
1. PyPDF2库对中文PDF支持不佳
2. 向量搜索相似度计算公式错误
3. 知识库中存在损坏的乱码数据

**解决方案**:
```python
# 1. 升级PDF解析库组合
import pdfplumber  # 优选方案
import fitz  # PyMuPDF备选

# 2. 多层级解析策略
async def _parse_pdf(self, file_path, metadata):
    # 优先使用pdfplumber
    with pdfplumber.open(str(file_path)) as pdf:
        # 提取文本...
    
    # 如果效果不好，使用PyMuPDF
    if content_insufficient:
        doc = fitz.open(str(file_path))
        # 提取文本...
    
    # 最后使用OCR
    if still_insufficient:
        # OCR处理...

# 3. 修复相似度计算
similarity_score = 1.0 / (1.0 + distance)  # 正确公式
```

**效果验证**:
- 中文提取成功率: 0% → 35.7%
- 向量搜索结果: 0个 → 5个
- AI回答置信度: 提升到0.72

**经验教训**:
- PDF解析是知识问答系统的基础，质量直接影响整体效果
- 需要针对中文内容选择合适的解析库
- 向量搜索的相似度计算必须与数据库匹配
- 端到端验证是发现问题的最有效方法

### ChromaDB向量搜索优化

**最佳实践**:
```python
# 正确的相似度计算
if distance == 0:
    similarity_score = 1.0
else:
    similarity_score = 1.0 / (1.0 + distance)

# 合理的阈值设置
similarity_threshold = 0.3  # 通常0.2-0.4范围

# 调试技巧
results = collection.query(query_texts=["测试"], n_results=5)
print(f"距离: {results['distances'][0]}")
print(f"相似度: {[1.0/(1.0+d) for d in results['distances'][0]]}")
```

## 🧠 AI自我进化系统

### 系统设计理念
基于用户反馈"让AI系统从每次优化中学习"的需求，设计了完整的自我进化框架:

### 核心组件
1. **ExperienceKnowledgeBase** - 经验知识库
   - 结构化存储调试经验和解决方案
   - 支持相似经验查找和解决方案建议
   - 自动提取优化模式

2. **AdaptiveLearningEngine** - 自适应学习引擎
   - 分析用户交互模式
   - 检测系统性能问题
   - 主动建议优化方案

3. **EvolutionaryAnswerGenerator** - 进化版问答生成器
   - 实时监控答案质量
   - 自动记录质量问题
   - 基于历史经验优化生成策略

### 使用方式
```python
# 替换标准答案生成器
answer_generator = EvolutionaryAnswerGenerator(llm_client, vector_store, config)

# 获取进化统计
stats = answer_generator.get_evolution_statistics()

# 获取优化建议
suggestions = await answer_generator.get_proactive_suggestions()
```

## 📁 项目结构

```
project-20250729-f1a705ab/
├── code/
│   ├── ai_evolution/           # AI自我进化系统
│   │   ├── experience_system.py
│   │   └── evolution_integration.py
│   ├── knowledge_ingestion/    # 文档处理
│   │   ├── document_parser.py
│   │   └── web_crawler.py
│   ├── knowledge_base/         # 知识库管理
│   │   └── vector_store.py
│   ├── qa_engine/             # 问答引擎
│   │   └── answer_generator.py
│   ├── llm_integration/       # LLM集成
│   │   └── deepseek_client.py
│   ├── web_interface/         # Web接口
│   │   └── api_server.py
│   └── session_manager.py     # 会话管理
├── uploads/                   # 上传文件存储
├── knowledge_db/             # ChromaDB数据目录
├── experience_kb/            # 经验知识库
└── .env                      # 环境配置
```

## 🔍 调试技巧

### PDF解析问题排查
```bash
# 测试PDF解析质量
python -c "
import pdfplumber
with pdfplumber.open('test.pdf') as pdf:
    text = pdf.pages[0].extract_text()
    print(f'长度: {len(text)}')
    print(f'中文字符: {sum(1 for c in text if "\u4e00" <= c <= "\u9fff")}')
    print(f'预览: {text[:200]}')
"
```

### 向量搜索调试
```python
# 直接测试ChromaDB查询
results = collection.query(query_texts=["测试词"], n_results=5)
for i, (distance, doc) in enumerate(zip(results['distances'][0], results['documents'][0])):
    similarity = 1.0 / (1.0 + distance)
    print(f"结果{i+1}: 距离={distance:.4f}, 相似度={similarity:.4f}")
```

### API接口测试
```bash
# 测试搜索功能
curl -X POST "http://127.0.0.1:8000/search"   -H "Content-Type: application/json"   -d '{"query": "测试", "top_k": 3, "similarity_threshold": 0.3}'

# 测试问答功能  
curl -X POST "http://127.0.0.1:8000/ask"   -H "Content-Type: application/json"   -d '{"question": "测试问题", "domain": "", "user_id": "test"}'
```

## 📊 性能优化建议

### 系统监控指标
- PDF解析成功率和中文字符提取比例
- 向量搜索结果数量和平均相似度
- AI回答置信度和信息源数量
- 用户问题响应时间

### 持续改进方向
1. **文档处理**:
   - 支持更多文档格式(PPT, 图片等)
   - 改进OCR识别准确率
   - 优化大文件处理性能

2. **知识检索**:
   - 实现混合搜索(关键词+向量)
   - 优化搜索结果排序算法
   - 增加搜索结果缓存机制

3. **AI问答**:
   - 集成更多领域适配器
   - 实现多轮对话优化
   - 增强推理链展示

## 🎯 未来规划

### 短期目标 (1-2周)
- [ ] 集成AI进化系统到主要组件
- [ ] 添加自动化测试验证
- [ ] 完善用户反馈收集机制

### 中期目标 (1-2月)
- [ ] 实现在线学习能力
- [ ] 建立知识库版本管理
- [ ] 增加多模态内容支持

### 长期愿景 (3-6月)
- [ ] 完全自主的问题诊断和修复
- [ ] 跨项目经验知识共享
- [ ] AI辅助的代码生成和优化

---

*这个记忆系统会持续更新，记录每次重要的开发进展和调试经验。*
*最后更新时间: 2025-07-30*
