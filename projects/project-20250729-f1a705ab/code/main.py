#!/usr/bin/env python3
"""
智能行业知识问答系统 - 主启动程序
统一的系统启动入口，支持多种运行模式
"""

import os
import sys
import asyncio
import logging
import argparse
from pathlib import Path
from typing import Dict, Any
import yaml
from dotenv import load_dotenv

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "code"))

# 导入各个模块
from web_interface.api_server import app, initialize_system
from knowledge_ingestion.document_parser import DocumentParser
from knowledge_ingestion.web_crawler import WebCrawler, CrawlConfig
from knowledge_base.vector_store import VectorStore
from llm_integration.deepseek_client import DeepSeekClient
from qa_engine.answer_generator import AnswerGenerator, QAConfig
from domain_adapters.medical_adapter import MedicalAdapter

class KnowledgeQASystem:
    """智能知识问答系统主类"""
    
    def __init__(self, config_path: str = None):
        """
        初始化系统
        
        Args:
            config_path: 配置文件路径
        """
        # 加载环境变量
        self._load_environment()
        
        self.config_path = config_path or str(project_root / "config" / "config.yaml")
        self.config = self._load_config()
        self.logger = self._setup_logging()
        
        # 系统组件
        self.components = {}
        
    def _load_environment(self):
        """加载环境变量文件"""
        env_path = project_root / ".env"
        if env_path.exists():
            load_dotenv(env_path)
            print(f"已加载环境配置文件: {env_path}")
        else:
            print(f"环境配置文件不存在: {env_path}")
            print("请复制 .env.template 为 .env 并配置相应的参数")
        
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                
            # 处理环境变量
            config = self._process_environment_variables(config)
            return config
            
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            # 返回默认配置
            return self._get_default_config()
            
    def _process_environment_variables(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """处理配置中的环境变量"""
        def replace_env_vars(obj):
            if isinstance(obj, dict):
                return {k: replace_env_vars(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [replace_env_vars(item) for item in obj]
            elif isinstance(obj, str) and obj.startswith("${") and obj.endswith("}"):
                env_var = obj[2:-1]
                return os.getenv(env_var, obj)
            else:
                return obj
                
        return replace_env_vars(config)
        
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "system": {
                "name": "智能行业知识问答系统",
                "version": "1.0.0",
                "debug": True,
                "log_level": "INFO"
            },
            "server": {
                "host": "0.0.0.0",
                "port": 8000,
                "workers": 1
            },
            "deepseek": {
                "timeout": 60,
                "max_retries": 3,
                "default_temperature": 0.3
            },
            "vector_store": {
                "persist_directory": "knowledge_db",
                "collection_name": "knowledge_base"
            }
        }
        
    def _setup_logging(self) -> logging.Logger:
        """设置日志"""
        log_level = self.config.get("system", {}).get("log_level", "INFO")
        
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler('system.log', encoding='utf-8')
            ]
        )
        
        return logging.getLogger(__name__)
        
    async def initialize_components(self):
        """初始化系统组件"""
        try:
            self.logger.info("开始初始化系统组件...")
            
            # 1. 文档解析器
            self.logger.info("初始化文档解析器...")
            parser_config = self.config.get("document_parser", {})
            self.components["document_parser"] = DocumentParser(parser_config)
            
            # 2. 向量数据库
            self.logger.info("初始化向量数据库...")
            vector_config = self.config.get("vector_store", {})
            self.components["vector_store"] = VectorStore(
                persist_directory=vector_config.get("persist_directory", "knowledge_db"),
                collection_name=vector_config.get("collection_name", "knowledge_base"),
                embedding_model=vector_config.get("embedding_model", "all-MiniLM-L6-v2")
            )
            
            # 3. LLM客户端
            self.logger.info("初始化DeepSeek客户端...")
            deepseek_config = self.config.get("deepseek", {})
            
            # 检查API密钥
            api_key = deepseek_config.get("api_key")
            if not api_key or api_key.startswith("${"):
                self.logger.warning("DeepSeek API密钥未设置，某些功能可能无法使用")
                self.logger.info("请设置环境变量 DEEPSEEK_API_KEY")
            
            self.components["llm_client"] = DeepSeekClient(
                api_key=api_key,
                base_url=deepseek_config.get("base_url", "https://api.deepseek.com/v1"),
                timeout=deepseek_config.get("timeout", 60),
                max_retries=deepseek_config.get("max_retries", 3)
            )
            
            # 4. 问答引擎
            self.logger.info("初始化问答引擎...")
            qa_config_dict = self.config.get("qa_engine", {})
            qa_config = QAConfig(
                max_context_length=qa_config_dict.get("max_context_length", 4000),
                top_k_results=qa_config_dict.get("top_k_results", 5),
                similarity_threshold=qa_config_dict.get("similarity_threshold", 0.3),
                temperature=deepseek_config.get("default_temperature", 0.3),
                max_tokens=deepseek_config.get("default_max_tokens", 1024),
                enable_reasoning=qa_config_dict.get("enable_reasoning", True),
                enable_source_citation=qa_config_dict.get("enable_source_citation", True),
                fallback_to_general=qa_config_dict.get("fallback_to_general", True)
            )
            
            self.components["answer_generator"] = AnswerGenerator(
                self.components["llm_client"],
                self.components["vector_store"],
                qa_config
            )
            
            # 注册领域适配器
            domain_config = self.config.get("domain_adapters", {})
            if domain_config.get("medical", {}).get("enabled", True):
                medical_adapter = MedicalAdapter()
                self.components["answer_generator"].register_domain_adapter("医疗健康", medical_adapter)
                self.logger.info("已注册医疗领域适配器")
            
            # 5. 网络爬虫
            self.logger.info("初始化网络爬虫...")
            crawler_config_dict = self.config.get("web_crawler", {})
            crawl_config = CrawlConfig(
                max_pages=crawler_config_dict.get("max_pages", 100),
                delay_seconds=crawler_config_dict.get("delay_seconds", 1.0),
                timeout_seconds=crawler_config_dict.get("timeout_seconds", 30),
                follow_links=crawler_config_dict.get("follow_links", True),
                max_depth=crawler_config_dict.get("max_depth", 2),
                user_agent=crawler_config_dict.get("user_agent", "Knowledge-QA-Bot/1.0")
            )
            
            self.components["web_crawler"] = WebCrawler(
                crawl_config,
                crawler_config_dict.get("crawl_data_dir", "crawl_data")
            )
            
            self.logger.info("所有系统组件初始化完成！")
            
        except Exception as e:
            self.logger.error(f"系统组件初始化失败: {e}")
            raise
            
    async def start_api_server(self):
        """启动API服务器"""
        try:
            import uvicorn
            
            server_config = self.config.get("server", {})
            
            self.logger.info(f"启动API服务器...")
            self.logger.info(f"地址: http://{server_config.get('host', '0.0.0.0')}:{server_config.get('port', 8000)}")
            
            # 初始化FastAPI应用的组件
            await initialize_system()
            
            # 启动服务器
            uvicorn.run(
                "web_interface.api_server:app",
                host=server_config.get("host", "0.0.0.0"),
                port=server_config.get("port", 8000),
                reload=server_config.get("reload", False),
                workers=server_config.get("workers", 1),
                log_level=self.config.get("system", {}).get("log_level", "INFO").lower()
            )
            
        except Exception as e:
            self.logger.error(f"启动API服务器失败: {e}")
            raise
            
    async def run_interactive_mode(self):
        """运行交互模式"""
        try:
            await self.initialize_components()
            
            self.logger.info("进入交互模式...")
            print("\n" + "="*50)
            print("🤖 智能行业知识问答系统 - 交互模式")
            print("="*50)
            print("输入 'exit' 或 'quit' 退出")
            print("输入 'help' 查看帮助")
            print("-"*50)
            
            answer_generator = self.components["answer_generator"]
            
            while True:
                try:
                    question = input("\n❓ 请输入您的问题: ").strip()
                    
                    if not question:
                        continue
                        
                    if question.lower() in ['exit', 'quit']:
                        print("\n👋 再见！")
                        break
                        
                    if question.lower() == 'help':
                        self._show_help()
                        continue
                        
                    # 询问领域
                    domain = input("🏷️  请输入专业领域 (可选，直接回车跳过): ").strip()
                    
                    print("\n🤔 正在思考中...")
                    
                    # 构建问题上下文
                    from qa_engine.answer_generator import QuestionContext
                    context = QuestionContext(
                        question=question,
                        domain=domain,
                        user_id="interactive_user"
                    )
                    
                    # 生成答案
                    result = await answer_generator.generate_answer(context)
                    
                    # 显示结果
                    print(f"\n💡 答案 (置信度: {result.confidence:.2f}):")
                    print("-" * 40)
                    print(result.answer)
                    
                    if result.sources:
                        print(f"\n📚 参考来源 ({len(result.sources)}个):")
                        for i, source in enumerate(result.sources[:3], 1):
                            print(f"  {i}. {source.get('source_file', 'Unknown')} (相似度: {source.get('similarity_score', 0):.2f})")
                            
                    if result.reasoning_steps:
                        print(f"\n🧠 推理步骤:")
                        for i, step in enumerate(result.reasoning_steps, 1):
                            print(f"  {i}. {step}")
                            
                except KeyboardInterrupt:
                    print("\n\n👋 用户中断，再见！")
                    break
                except Exception as e:
                    print(f"\n❌ 处理问题时发生错误: {e}")
                    
        except Exception as e:
            self.logger.error(f"交互模式运行失败: {e}")
            
    def _show_help(self):
        """显示帮助信息"""
        help_text = """
📖 帮助信息:

支持的命令:
- exit/quit: 退出程序
- help: 显示此帮助信息

支持的领域:
- 医疗健康: 医疗、健康、疾病相关问题
- 通用: 一般性知识问题

使用技巧:
1. 提问时尽量详细描述您的问题
2. 选择合适的领域可以获得更专业的回答
3. 系统会基于已有的知识库回答问题
4. 如果答案不满意，可以换个方式提问

示例问题:
- "什么是人工智能？"
- "高血压的症状有哪些？" (医疗健康领域)
- "如何预防感冒？" (医疗健康领域)
        """
        print(help_text)
        
    async def run_batch_document_processing(self, document_dir: str):
        """批量处理文档"""
        try:
            await self.initialize_components()
            
            document_parser = self.components["document_parser"]
            vector_store = self.components["vector_store"]
            
            doc_dir = Path(document_dir)
            if not doc_dir.exists():
                self.logger.error(f"文档目录不存在: {document_dir}")
                return
                
            self.logger.info(f"开始批量处理文档: {document_dir}")
            
            # 获取所有支持的文档
            supported_extensions = document_parser.get_supported_formats()
            document_files = []
            
            for ext in supported_extensions:
                document_files.extend(doc_dir.glob(f"*{ext}"))
                
            self.logger.info(f"找到 {len(document_files)} 个文档文件")
            
            # 批量解析
            total_chunks = 0
            successful = 0
            
            for doc_file in document_files:
                try:
                    self.logger.info(f"处理文档: {doc_file.name}")
                    
                    # 解析文档
                    result = await document_parser.parse_document(str(doc_file))
                    
                    if result.parse_status == "success":
                        # 添加到向量数据库
                        chunks_added = await vector_store.add_document(result)
                        total_chunks += chunks_added
                        successful += 1
                        
                        self.logger.info(f"✅ {doc_file.name}: 添加了 {chunks_added} 个知识块")
                    else:
                        self.logger.error(f"❌ {doc_file.name}: 解析失败 - {result.error_message}")
                        
                except Exception as e:
                    self.logger.error(f"❌ {doc_file.name}: 处理失败 - {e}")
                    
            self.logger.info(f"批量处理完成: 成功处理 {successful}/{len(document_files)} 个文档")
            self.logger.info(f"总共添加了 {total_chunks} 个知识块")
            
        except Exception as e:
            self.logger.error(f"批量文档处理失败: {e}")
            
    def show_system_info(self):
        """显示系统信息"""
        print("\n" + "="*60)
        print("🤖 智能行业知识问答系统")
        print("="*60)
        
        system_config = self.config.get("system", {})
        print(f"版本: {system_config.get('version', '1.0.0')}")
        print(f"描述: {system_config.get('description', '基于DeepSeek大模型的多领域智能知识问答系统')}")
        
        print("\n📋 系统配置:")
        print(f"  - 配置文件: {self.config_path}")
        print(f"  - 调试模式: {'是' if system_config.get('debug', False) else '否'}")
        print(f"  - 日志级别: {system_config.get('log_level', 'INFO')}")
        
        deepseek_config = self.config.get("deepseek", {})
        api_key = deepseek_config.get("api_key", "")
        api_key_status = "已设置" if api_key and not api_key.startswith("${") else "未设置"
        print(f"  - DeepSeek API: {api_key_status}")
        
        print("\n🚀 启动选项:")
        print("  server    - 启动API服务器")
        print("  interactive - 交互模式问答")
        print("  process   - 批量处理文档")
        print("  info      - 显示系统信息")
        print("="*60)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="智能行业知识问答系统")
    parser.add_argument("mode", choices=["server", "interactive", "process", "info"], 
                       help="运行模式")
    parser.add_argument("--config", "-c", default=None, help="配置文件路径")
    parser.add_argument("--document-dir", "-d", default=None, help="文档目录 (process模式)")
    parser.add_argument("--port", "-p", type=int, default=None, help="服务器端口")
    parser.add_argument("--host", default=None, help="服务器地址")
    
    args = parser.parse_args()
    
    # 创建系统实例
    system = KnowledgeQASystem(args.config)
    
    if args.mode == "info":
        system.show_system_info()
        return
        
    # 覆盖配置中的参数
    if args.port:
        system.config.setdefault("server", {})["port"] = args.port
    if args.host:
        system.config.setdefault("server", {})["host"] = args.host
        
    try:
        if args.mode == "server":
            asyncio.run(system.start_api_server())
        elif args.mode == "interactive":
            asyncio.run(system.run_interactive_mode())
        elif args.mode == "process":
            if not args.document_dir:
                print("❌ process模式需要指定 --document-dir 参数")
                return
            asyncio.run(system.run_batch_document_processing(args.document_dir))
            
    except KeyboardInterrupt:
        print("\n👋 程序被用户中断")
    except Exception as e:
        print(f"❌ 程序运行失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()