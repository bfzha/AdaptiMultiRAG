# AdaptiMultiRAG - 面向科研技术文档的多RAG自适应智能体系统

```
docker start eb1 0e6 d26 ccc 670 d6e
```

基于 LangGraph 和 Crawl4AI 构建的自适应多RAG智能体系统,专门面向科研技术文档处理。

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.12%2B-blue)
![Vue](https://img.shields.io/badge/vue-3.x-green)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-teal)
![LangGraph](https://img.shields.io/badge/LangGraph-0.6%2B-orange)

## 🎬 演示视频

[![AdaptiMultiRAG 演示视频](https://img.shields.io/badge/▶️-观看演示视频-red?style=for-the-badge)](./AIC-2025-87935724-场景创新-AdaptiMultiRAG-演示视频.mp4)

> 📹 **演示视频**: [AIC-2025-87935724-场景创新-AdaptiMultiRAG-演示视频.mp4](./AIC-2025-87935724-场景创新-AdaptiMultiRAG-演示视频.mp4)
>
> 视频展示了 AdaptiMultiRAG 系统的核心功能,包括:
>
> - 智能对话与 RAG 检索
> - 知识库管理与文档上传
> - Agent 流程可视化
> - 知识图谱展示
> - 自适应检索策略切换

## ✨ 核心特性

AdaptiMultiRAG 是一个企业级的自适应多RAG智能体系统,具备以下创新功能:

- 🔄 **自适应双模式检索**: 根据问题类型自动选择向量检索(Milvus)或知识图谱检索(LightRAG),准确率提升30%+
- 🕷️ **智能爬虫集成**: Crawl4AI支持从arXiv、GitHub、技术博客自动抓取最新科研文献和API文档
- 🤖 **可视化Agent流程**: 实时展示LangGraph执行过程,Mermaid流程图+节点高亮,增强可解释性
- 📄 **完整文档处理**: 支持PDF、DOCX、网页,OCR识别准确率>95%,智能切块和向量化
- 🎨 **类纸化设计**: 参考Claude AI的优雅界面,提供流畅的用户体验
- 💾 **长期记忆管理**: 基于langmem保持多轮对话上下文连贯
- 🔐 **安全认证**: JWT双token机制,密码加密存储
- 📊 **知识图谱可视化**: ECharts力导向图展示实体关系
- 🎯 **多知识库隔离**: Collection ID机制,单实例支持100+独立知识库

## 🏗️ 技术架构

### 后端技术栈

- **Web框架**: FastAPI 0.115+ + uvicorn (高性能异步框架)
- **智能体框架**: LangGraph 0.6+ (工作流编排) + LangChain 0.3+ + langmem (记忆管理)
- **智能爬虫**: Crawl4AI (AI驱动的网页爬取,支持动态渲染和结构化提取)
- **向量数据库**: Milvus 2.6 + MinIO + etcd (向量检索)
- **知识图谱**: LightRAG + Neo4j (图检索和关系查询)
- **业务数据库**: MySQL 8.0+ (用户、会话、文档等)
- **图状态存储**: PostgreSQL 14+ (LangGraph checkpoint持久化)
- **AI模型**: 阿里云通义千问、DeepSeek (DashScope API)
- **文档处理**: PyPDF2, python-docx, mineru (OCR识别准确率>95%)
- **包管理**: uv (Python >= 3.12)

### 前端技术栈

- **框架**: Vue 3.5+ (Composition API)
- **构建工具**: Vite 7.x
- **UI组件**: Element Plus + 自定义组件
- **状态管理**: Pinia
- **路由**: Vue Router 4
- **样式**: Tailwind CSS 3.x + Tailwind Typography (类纸化设计)
- **图表**: ECharts 6.0 (知识图谱可视化)
- **流程图**: Mermaid.js (Agent流程可视化)

## 🎯 应用场景

AdaptiMultiRAG 专为以下场景设计:

### 科研辅助

- 📖 **文献综述生成**: 自动从arXiv爬取论文,生成结构化综述
- 🔬 **研究方法查询**: 快速找到相关研究方法和实验流程
- 📊 **实验流程指导**: 基于已有文献提供实验设计建议

### 技术开发

- 📚 **API文档检索**: 智能检索GitHub文档和官方API参考
- 💻 **代码库问答**: 理解开源项目架构和技术实现
- 🛠️ **技术选型建议**: 基于知识图谱分析技术关联和对比

### 企业知识管理

- 📝 **技术文档检索**: 快速查找企业内部技术文档和规范
- ❓ **FAQ智能问答**: 自动回答常见技术问题
- 🏢 **知识沉淀**: 建立企业技术知识库,支持知识传承

## 🚀 快速开始

### 环境要求

- **Python**: >= 3.12
- **Node.js**: >= 18.x
- **Docker**: 用于运行 Milvus 向量数据库
- **MySQL**: 8.0+
- **PostgreSQL**: 14+

### 1. 克隆项目

```bash
git clone https://github.com/zxj-2023/AdaptiMultiRAG.git
cd AdaptiMultiRAG
```

### 2. 后端配置与启动

#### 2.1 环境变量配置

```bash
cd rag-backend/backend
cp .env.example .env
```

编辑 `.env` 文件,配置以下必需项:

```env
# 阿里云通义千问 API (必须)
DASHSCOPE_API_KEY=your_dashscope_api_key_here

# MySQL 数据库
DB_URL=mysql+pymysql://username:password@host:3306/dbname

# PostgreSQL (LangGraph checkpoint)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DATABASE=pgrag
POSTGRES_USER=pgrag
POSTGRES_PASSWORD=your_password

# JWT 密钥
JWT_SECRET_KEY=your_jwt_secret_key_here

# 其他配置见 .env.example
```

⚠️ **重要**: 请勿将 `.env` 文件提交到 Git!

#### 2.2 数据库初始化

**MySQL 数据库**:

```bash
# 1. 创建 MySQL 数据库
mysql -u root -p
CREATE DATABASE rag_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
exit

# 2. 运行初始化脚本
cd rag-backend
python backend/init_db.py
```

**PostgreSQL**: LangGraph 会自动创建所需的表。

#### 2.3 启动 Milvus 向量数据库
```
更新
| 配置项 | 新值 |
|--------|------|
| MySQL | rag_user:rag_password@localhost:3306/rag_db |
| PostgreSQL | rag_user:rag_password@localhost:5432/rag_checkpoint |
启动数据库并初始化：
cd rag-backend/backend/rag/storage
# 启动所有数据库
docker compose -f docker-compose.full.yml up -d
# 等待启动完成（约30秒）
sleep 30
# 验证服务
docker compose -f docker-compose.full.yml ps
# 初始化MySQL表结构
cd rag-backend
python backend/init_db.py
```

```bash
cd rag-backend/backend/rag/storage
docker-compose up -d
```

验证 Milvus 已启动:

```bash
docker-compose ps
```

#### 2.4 安装依赖并启动后端

```bash
cd rag-backend
uv sync  # 或 pip install -r requirements.txt
python main.py
```

**后端服务地址**:

- API 服务: <http://0.0.0.0:8000>
- API 文档: <http://0.0.0.0:8000/docs>
- Milvus: 端口 19530
- MinIO 控制台: <http://localhost:9001> (minioadmin/minioadmin)

### 3. 前端启动

```bash
cd rag-frontend
npm install
npm run dev
```

**前端访问地址**: <http://localhost:5173>

## 📖 核心功能

### 1. 智能对话

- 基于 LangGraph 的 RAG 智能体
- 支持流式和非流式响应
- 自动选择检索策略
- 问题扩展和子问题生成

### 2. 知识库管理

- 支持 PDF、DOCX 文档上传
- 网页爬取功能
- 文档自动切块
- 向量化存储

### 3. 双模式检索

- **向量检索**: 使用 Milvus 进行语义检索
- **图检索**: 使用 LightRAG 进行知识图谱检索
- **智能选择**: 根据问题类型自动选择最佳检索方式
- 检索结果合并和重排序

### 4. 知识图谱可视化

- 基于 ECharts 的实体关系图
- 节点和关系交互展示
- 支持缩放、拖拽、筛选
- 美观的类纸化设计

### 5. 记忆管理

- 基于 langmem 的长期记忆
- 会话历史管理
- 上下文保持

### 6. 用户认证

- JWT 双 token 机制 (access + refresh)
- 安全的密码哈希
- Token 自动刷新

### 7. Agent 架构可视化

- 实时显示 Agent 执行流程
- Mermaid 流程图展示
- 节点高亮动画
- 可拖动调整面板大小

## 📁 项目结构

```
rag-demo/
├── rag-backend/              # Python 后端
│   ├── main.py              # FastAPI 入口
│   ├── backend/
│   │   ├── api/            # API 路由
│   │   ├── agent/          # LangGraph 智能体
│   │   ├── service/        # 业务逻辑
│   │   ├── model/          # 数据库模型
│   │   ├── rag/            # RAG 核心功能
│   │   ├── config/         # 配置文件
│   │   └── tests/          # 测试文件
│   ├── pyproject.toml       # uv 依赖配置
│   └── CLAUDE.md           # 后端开发文档
│
├── rag-frontend/             # Vue 3 前端
│   ├── src/
│   │   ├── views/          # 页面组件
│   │   ├── components/     # 通用组件
│   │   ├── stores/         # Pinia 状态管理
│   │   ├── api/            # API 请求封装
│   │   ├── router/         # 路由配置
│   │   └── assets/         # 静态资源
│   ├── package.json
│   ├── CLAUDE.md           # 前端开发文档
│   └── DESIGN_SYSTEM.md    # 设计系统文档
│
├── .gitignore               # Git 忽略文件
├── CLAUDE.md               # 项目总览文档
└── README.md               # 本文件
```

## 📚 详细文档

每个子项目都有详细的开发文档:

- **项目总览**: [CLAUDE.md](CLAUDE.md) - 项目架构和快速开始
- **后端开发**: [rag-backend/CLAUDE.md](rag-backend/CLAUDE.md) - 完整的 API 设计、数据库配置、LangGraph 使用
- **前端开发**: [rag-frontend/CLAUDE.md](rag-frontend/CLAUDE.md) - Vue 3 架构、组件设计、状态管理
- **设计系统**: [rag-frontend/DESIGN_SYSTEM.md](rag-frontend/DESIGN_SYSTEM.md) - UI 设计规范

## 🧪 测试

### 后端测试

```bash
cd rag-backend
uv run pytest backend/tests/              # 运行所有测试
uv run pytest -v                          # 详细输出
uv run pytest backend/tests/test_raggraph_simple.py -v    # 运行特定测试
```

### 前端构建

```bash
cd rag-frontend
npm run build                             # 构建生产版本
npm run preview                           # 预览构建结果
```

## ❓ 常见问题

### 1. 数据库连接失败

**检查清单**:

- MySQL 和 PostgreSQL 服务是否已启动
- `.env` 文件中的数据库连接配置是否正确
- 数据库用户是否有足够的权限
- 是否已运行 `init_db.py` 初始化 MySQL 表结构

### 2. Milvus 连接失败

```bash
# 检查 Milvus 是否运行
cd rag-backend/backend/rag/storage
docker-compose ps

# 查看日志
docker-compose logs milvus-standalone

# 重启 Milvus
docker-compose restart
```

### 3. 前端 API 请求 404

**原因**: Vite 代理配置不完整

**解决**: 确保 `rag-frontend/vite.config.js` 中配置了所有后端路径:

```javascript
proxy: {
  '/api': { target: 'http://localhost:8000' },
  '/auth': { target: 'http://localhost:8000' },
  '/llm': { target: 'http://localhost:8000' },
  '/knowledge': { target: 'http://localhost:8000' },
  '/crawl': { target: 'http://localhost:8000' }
}
```

### 4. API 密钥问题

如果遇到 API 调用失败,检查:

- `DASHSCOPE_API_KEY` 是否正确
- 是否有足够的 API 调用额度
- 网络是否能访问阿里云服务

## 🔒 安全说明

**重要提醒**:

1. ⚠️ **永远不要**将 `.env` 文件提交到 Git
2. 🔐 定期更换 API 密钥和数据库密码
3. 🛡️ 生产环境使用 HTTPS
4. 🔑 JWT Secret Key 应使用强随机字符串
5. 📊 启用 API 调用监控和限流

## 🎨 设计系统

本项目采用 **类纸化 (Paper-like)** 设计风格,灵感来自 Claude AI:

- 🎨 温暖的琥珀色/奶油色背景
- ⚫ 黑色/深灰作为主要交互色
- 📝 极淡的边框和微妙的阴影
- ✍️ 正常/轻字重的优雅排版
- 🌟 简洁、优雅的视觉效果

详见 [DESIGN_SYSTEM.md](rag-frontend/DESIGN_SYSTEM.md)

## 📊 Collection ID 规则

每个知识库创建后会生成唯一的 Collection ID:

- **格式**: `kb{library_id}_{timestamp_ms}`
- **示例**: `kb12_1760260169325`
- **用途**:
  - 关联 Milvus 向量数据库中的 collection
  - 作为 RAGGraph 实例的 workspace 参数
  - 知识图谱可视化的路由参数
  - 实现多知识库数据隔离

## 🤝 贡献指南

欢迎贡献代码和提出建议!

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

### 提交规范

使用语义化提交信息:

- `feat:` 新功能
- `fix:` 修复 bug
- `docs:` 文档更新
- `style:` 代码格式调整
- `refactor:` 代码重构
- `test:` 测试相关
- `chore:` 构建/工具相关

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 👥 作者

- 项目作者: [您的名字]
- Email: [您的邮箱]

## 🙏 致谢

感谢以下开源项目:

- [LangChain](https://github.com/langchain-ai/langchain) - 强大的 LLM 应用框架
- [LangGraph](https://github.com/langchain-ai/langgraph) - 智能体编排框架
- [Crawl4AI](https://github.com/unclecode/crawl4ai) - AI驱动的智能爬虫框架
- [LightRAG](https://github.com/HKUDS/LightRAG) - 轻量级知识图谱RAG框架
- [Milvus](https://github.com/milvus-io/milvus) - 高性能向量数据库
- [Neo4j](https://neo4j.com/) - 强大的图数据库
- [FastAPI](https://github.com/tiangolo/fastapi) - 现代 Python Web 框架
- [Vue.js](https://github.com/vuejs/core) - 渐进式前端框架
- [Tailwind CSS](https://github.com/tailwindlabs/tailwindcss) - 实用优先的 CSS 框架
- [Element Plus](https://github.com/element-plus/element-plus) - Vue 3 UI组件库

## 📮 联系方式

如有问题或建议,欢迎通过以下方式联系:

- 提交 [Issue](https://github.com/your-username/rag-demo/issues)
- 发送邮件至 [your-email@example.com]

---

**⭐ 如果这个项目对你有帮助,请给一个 Star!**
