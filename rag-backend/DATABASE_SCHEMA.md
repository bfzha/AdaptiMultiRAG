# AdaptiMultiRAG 数据库表图学习文件

## 1. 数据库连接配置总览

本系统采用三数据库架构设计，分别用于业务数据存储、LangGraph状态持久化和向量检索。以下是完整的数据库连接配置信息。

### 1.1 MySQL 业务数据库

MySQL用于存储系统的核心业务数据，包括用户信息、对话记录、知识库和文档等。所有业务表都存储在`rag_db`数据库中，使用SQLAlchemy ORM进行数据操作。

| 参数 | 配置值来源 | 说明 |
|------|-----------|------|
| DB_URL | .env文件配置 | MySQL完整连接字符串，格式: mysql+pymysql://user:pass@host:3306/db |
| DB_HOST | 从DB_URL解析 | MySQL服务器地址，默认localhost |
| DB_PORT | 从DB_URL解析 | MySQL端口，默认3306 |
| DB_USER | 从DB_URL解析 | 数据库用户名，默认root |
| DB_PASSWORD | 从DB_URL解析 | 数据库密码 |
| DB_NAME | 从DB_URL解析 | 数据库名称，默认rag_db |

MySQL连接配置采用双重检查锁定模式（Double-Checked Locking Pattern）确保线程安全的单例创建。连接池配置包括`pool_pre_ping=True`防止连接失效、`pool_recycle=3600`定时回收连接。生产环境建议根据实际性能需求调整连接池大小。

### 1.2 PostgreSQL 数据库 (LangGraph)

PostgreSQL专门用于LangGraph智能体框架的状态持久化，包含两个核心功能：Checkpoint存储图执行状态、Memory Store存储langmem长期记忆数据。LangGraph会在首次运行时自动创建所需的表结构，无需手动初始化。

| 参数 | 配置值来源 | 默认值 | 说明 |
|------|-----------|--------|------|
| POSTGRES_HOST | .env文件 | localhost | PostgreSQL服务器地址 |
| POSTGRES_PORT | .env文件 | 5432 | PostgreSQL端口 |
| POSTGRES_DATABASE | .env文件 | rag_checkpoint | 数据库名称 |
| POSTGRES_USER | .env文件 | postgres | 数据库用户名 |
| POSTGRES_PASSWORD | .env文件 | 123456 | 数据库密码 |

连接字符串格式为：`postgresql://user:password@host:port/database`。系统使用psycopg2的ConnectionPool管理连接池，默认配置`min_size=1`、`max_size=5`。生产环境可根据并发需求调整连接池大小。

### 1.3 Milvus 向量数据库

Milvus是开源的向量数据库，专门用于存储和检索向量数据。在本系统中，Milvus存储知识库文档的向量嵌入，支持高效的相似度检索。Milvus通过Docker Compose部署，包含etcd、MinIO和Milvus standalone三个组件。

| 参数 | 配置值来源 | 默认值 | 说明 |
|------|-----------|--------|------|
| MILVUS_URI | .env文件 | localhost:19530 | Milvus服务器连接地址 |
| MILVUS_DB_NAME | .env文件 | default | 数据库名称 |
| MILVUS_COLLECTION_NAME | 系统自动生成 | - | Collection名称，格式: kb{library_id}_{timestamp_ms} |

Milvus默认端口19530用于客户端连接，MinIO控制台端口9001用于存储管理（默认账号minioadmin/minioadmin）。每个知识库创建时系统会自动生成唯一的Collection ID，确保不同知识库的向量数据完全隔离。

---

## 2. MySQL 表结构详解

MySQL业务数据库包含5个核心表，分别用于存储用户信息、对话会话、聊天历史、知识库和文档数据。这些表通过外键和索引建立了完整的关联关系，支持系统的所有业务功能。

### 2.1 用户表: users

users表是系统的基础认证表，存储所有注册用户的信息。表设计采用UUID作为用户标识，支持邮箱和用户名双重登录方式，使用bcrypt算法对密码进行哈希存储。

**字段列表**:

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|--------|------|------|--------|------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT | 自动生成 | 用户唯一标识，自增主键 |
| username | VARCHAR(50) | UNIQUE, NOT NULL | - | 用户名，唯一约束 |
| email | VARCHAR(100) | UNIQUE, NOT NULL | - | 邮箱地址，唯一约束 |
| password_hash | VARCHAR(255) | NOT NULL | - | bcrypt加密后的密码哈希 |
| is_active | BOOLEAN | NOT NULL | True | 账户是否激活状态 |
| created_at | DATETIME | SERVER DEFAULT | CURRENT_TIMESTAMP | 账户创建时间 |
| updated_at | DATETIME | SERVER DEFAULT | CURRENT_TIMESTAMP | 最后更新时间 |

**关联关系**:
- 与conversations表：1对多关系，一个用户可以拥有多个对话会话
- 与knowledge_libraries表：1对多关系，一个用户可以创建多个知识库

**索引**:
- 主键索引：id
- 唯一索引：username, email
- 普通索引：is_active（用于查询活跃用户）

**业务用途**:
该表是系统认证的核心，支持用户注册、登录和权限验证。所有需要认证的API接口都会通过JWT token解析用户ID，然后验证该用户在users表中的存在性和激活状态。is_active字段可用于实现账户冻结、注销等管理功能。

### 2.2 对话会话表: conversations

conversations表存储用户的对话会话信息，每个会话代表一个独立的聊天上下文。会话表使用UUID作为会话标识符，支持跨会话的历史记录管理和检索。

**字段列表**:

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|--------|------|------|--------|------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT | 自动生成 | 内部自增主键 |
| conversation_id | VARCHAR(36) | UNIQUE, NOT NULL, INDEX | uuid.uuid4() | 对话会话唯一标识UUID |
| title | VARCHAR(255) | NOT NULL | - | 对话标题，默认显示首条消息 |
| user_id | INTEGER | NOT NULL | - | 所属用户ID，外键关联users.id |
| created_at | DATETIME | SERVER DEFAULT | CURRENT_TIMESTAMP | 会话创建时间 |
| updated_at | DATETIME | SERVER DEFAULT | CURRENT_TIMESTAMP | 最后更新时间 |

**关联关系**:
- 与users表：多对1关系，关联创建对话的用户
- 与chat_history表：1对多关系，一个会话包含多条聊天记录

**索引**:
- 主键索引：id
- 唯一索引：conversation_id（用于API调用时定位会话）
- 普通索引：user_id（用于查询用户的所有会话）
- 联合索引：(user_id, created_at) 用于用户会话列表分页查询

**业务用途**:
该表实现对话的逻辑隔离，每个conversation_id对应一个独立的聊天上下文。当用户创建新对话或继续历史对话时，系统通过conversation_id关联chat_history表中的消息记录。updated_at字段支持按更新时间排序的会话列表展示。

### 2.3 聊天历史表: chat_history

chat_history表是系统的核心消息存储表，采用非关系型设计，使用JSON格式存储消息的元信息（extra_data字段）。这种设计灵活地支持不同类型的消息格式和扩展属性。

**字段列表**:

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|--------|------|------|--------|------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT | 自动生成 | 记录唯一标识 |
| conversation_id | VARCHAR(36) | NOT NULL, INDEX | - | 所属对话会话ID |
| role | VARCHAR(20) | NOT NULL | - | 消息角色：user/assistant/system |
| type | VARCHAR(20) | NOT NULL | text | 消息类型：text/image/file/function_call |
| content | TEXT | NOT NULL | - | 消息正文内容 |
| extra_data | JSON | NULL | - | 扩展元数据，存储模型参数、token数量等 |

**关联关系**:
- 与conversations表：多对1关系，关联所属对话会话

**索引**:
- 主键索引：id
- 普通索引：conversation_id（用于快速查询会话消息）
- 联合索引：(conversation_id, created_at) 用于按时间顺序检索消息

**业务用途**:
该表存储所有聊天消息的完整历史，支持对话上下文重建和历史消息检索。role字段区分消息发送方，type字段支持多种消息格式，extra_data字段以JSON格式存储模型响应参数、token统计、延迟信息等扩展数据。这种设计使得系统可以灵活支持流式响应、非流式响应和各种消息类型的统一存储。

**extra_data示例结构**:
```json
{
  "model": "qwen3-max-preview",
  "tokens": 150,
  "latency_ms": 1250,
  "retrieval_mode": "auto",
  "retrieved_docs": 5
}
```

### 2.4 知识库表: knowledge_libraries

knowledge_libraries表存储知识库的核心信息，是系统RAG功能的数据基础。每个知识库对应唯一的collection_id，用于隔离Milvus向量存储和LightRAG图存储的索引数据。

**字段列表**:

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|--------|------|------|--------|------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT | 自动生成 | 知识库内部ID |
| collection_id | VARCHAR(36) | UNIQUE, NOT NULL | uuid.uuid4() | 知识库唯一标识UUID |
| title | VARCHAR(200) | NOT NULL | - | 知识库标题 |
| description | TEXT | NULL | - | 知识库详细描述 |
| user_id | VARCHAR(100) | NOT NULL | - | 创建用户ID |
| is_active | BOOLEAN | NOT NULL | True | 是否激活状态 |
| created_at | DATETIME | SERVER DEFAULT | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | SERVER DEFAULT | CURRENT_TIMESTAMP | 更新时间 |

**关联关系**:
- 与knowledge_documents表：1对多关系，一个知识库包含多个文档

**索引**:
- 主键索引：id
- 唯一索引：collection_id（用于Milvus和LightRAG定位）
- 普通索引：user_id（用于查询用户的知识库列表）

**Collection ID生成规则**:
Collection ID是系统的核心隔离标识，生成规则为`kb{library_id}_{timestamp_ms}`格式。示例：`kb12_1760260169325`。该ID用于Milvus Collection命名、LightRAG workspace路径、聊天时的知识库定位。系统为每个知识库动态创建RAGGraph实例时，会将collection_id作为workspace参数传递。

**业务用途**:
该表是知识库管理功能的核心实体，记录知识库的基本信息和状态。title和description字段支持知识库的展示和搜索功能，is_active字段支持软删除（保留数据但标记为不可用）。collection_id字段是连接MySQL业务数据与Milvus/LightRAG存储的关键桥梁。

### 2.5 知识文档表: knowledge_documents

knowledge_documents表存储知识库中的文档记录，支持链接类型和文件类型两种文档来源。文档表记录文档的基本信息和处理状态，支持文档的增删改查管理。

**字段列表**:

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|--------|------|------|--------|------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT | 自动生成 | 文档内部ID |
| library_id | INTEGER | FOREIGN KEY, NOT NULL | - | 所属知识库ID |
| name | VARCHAR(200) | NOT NULL | - | 文档名称 |
| type | VARCHAR(20) | NOT NULL | - | 文档类型：link/file/pdf等 |
| url | VARCHAR(500) | NULL | - | 文档链接地址 |
| file_path | VARCHAR(500) | NULL | - | 文件存储路径 |
| file_size | INTEGER | NULL | - | 文件大小（字节） |
| is_processed | BOOLEAN | NOT NULL | False | 是否已完成向量化处理 |
| created_at | DATETIME | SERVER DEFAULT | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | SERVER DEFAULT | CURRENT_TIMESTAMP | 更新时间 |

**关联关系**:
- 与knowledge_libraries表：多对1关系，关联所属知识库

**索引**:
- 主键索引：id
- 外键索引：library_id（用于查询知识库下的文档）
- 联合索引：(library_id, is_processed) 用于查询待处理文档

**业务用途**:
该表实现知识库内文档的细粒度管理，支持PDF、DOCX等文件上传和链接类型文档的添加。type字段区分文档来源类型，url字段存储外部链接，file_path字段存储阿里云OSS等对象存储的路径。is_processed字段标记文档是否已完成向量化处理，向量化完成后用户才能基于该文档进行RAG检索。

**文档处理流程**:
1. 用户添加文档时创建记录，is_processed=False
2. 后台异步处理文档：文本提取、切块、向量化
3. 向量化完成后更新is_processed=True，同时存储向量数据到Milvus
4. 处理失败时记录错误信息到日志，保留记录供重试

---

## 3. PostgreSQL 表结构 (LangGraph)

LangGraph框架使用PostgreSQL存储智能体执行的状态信息，包括Checkpoints（检查点，保存图执行状态）和Memory Store（记忆存储，保存langmem长期记忆）。LangGraph在首次运行时会自动创建所需表结构，无需手动干预。

### 3.1 Checkpoint 表结构

LangGraph的PostgreSQL Checkpoint存储采用`snapshots`、`writes`、`tasks`三表结构，实现图执行状态的完整持久化。这种设计支持断点续传、历史状态回溯和多版本管理。

**核心表清单**:

| 表名 | 说明 |
|------|------|
| checkpoints | 存储图执行的快照状态，包含节点状态、配置信息等 |
| checkpoint_writes | 存储状态变更的写操作记录，支持增量同步 |
| checkpoint_blobs | 存储大容量的状态二进制数据 |
| checkpoint_metadata | 存储快照的元数据信息 |

**checkpoints表主要字段**:

| 字段名 | 类型 | 说明 |
|--------|------|------|
| thread_id | VARCHAR | 线程/会话标识符 |
| checkpoint_id | VARCHAR | 检查点唯一ID |
| parent_id | VARCHAR | 父检查点ID，支持状态回溯 |
| type | VARCHAR | 检查点类型 |
| checkpoint | JSONB | 状态快照数据 |
| metadata | JSONB | 元数据信息 |
| created_at | TIMESTAMP | 创建时间 |

**checkpoint_writes表主要字段**:

| 字段名 | 类型 | 说明 |
|--------|------|------|
| thread_id | VARCHAR | 关联的线程ID |
| checkpoint_id | VARCHAR | 关联的检查点ID |
| task_id | VARCHAR | 任务ID |
| channel | VARCHAR | 通道名称 |
| value | JSONB | 写入的状态值 |
| created_at | TIMESTAMP | 创建时间 |

**业务用途**:
Checkpoints实现图执行的断点持久化，支持：
- **断点续传**：服务重启后恢复上次执行状态
- **历史回溯**：查询任意历史检查点状态
- **状态对比**：对比不同时刻的状态差异
- **调试支持**：LangGraph Studio调试模式的状态查看

### 3.2 Memory Store 表结构

LangGraph Memory Store基于langmem库实现长期记忆持久化，使用PostgreSQL作为存储后端。Memory Store支持语义记忆、事实记忆和工作记忆三种类型。

**核心表清单**:

| 表名 | 说明 |
|------|------|
| memory | 存储记忆内容的主表 |
| memory_namespace | 记忆命名空间，支持记忆分类隔离 |
| memory_index | 记忆索引，加速记忆检索 |

**memory表主要字段**:

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | UUID | 记忆唯一ID |
| namespace | VARCHAR[] | 命名空间数组，支持多级分类 |
| key | VARCHAR | 记忆键名 |
| value | JSONB | 记忆内容 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

**memory_namespace表主要字段**:

| 字段名 | 类型 | 说明 |
|--------|------|------|
| namespace | VARCHAR[] | 命名空间主键 |
| user_id | VARCHAR | 关联用户ID |
| config | JSONB | 命名空间配置 |

**业务用途**:
Memory Store实现智能体的长期记忆能力：
- **语义记忆**：存储用户偏好、对话风格等结构化信息
- **事实记忆**：存储知识库提取的关键事实
- **工作记忆**：存储当前对话的上下文摘要
- **跨会话记忆**：用户下次访问时自动加载历史记忆

### 3.3 LangGraph 配置代码示例

```python
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.store.postgres import PostgresStore
from psycopg_pool import ConnectionPool

# 从环境变量读取配置
db_config = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": int(os.getenv("POSTGRES_PORT", "5432")),
    "database": os.getenv("POSTGRES_DATABASE", "rag_checkpoint"),
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", "123456")
}

# 创建连接字符串
connection_string = (
    f"postgresql://{db_config['user']}:{db_config['password']}"
    f"@{db_config['host']}:{db_config['port']}/{db_config['database']}"
)

# 创建连接池
conn_pool = ConnectionPool(connection_string, min_size=1, max_size=5)

# 初始化Checkpoint存储
checkpointer = PostgresSaver(conn=conn_pool)
checkpointer.setup()

# 初始化Memory Store
memory_store = PostgresStore(conn=conn_pool)
memory_store.setup()

# 编译图时启用持久化
graph = workflow.compile(checkpointer=checkpointer, store=memory_store)
```

---

## 4. 前端访问配置

前端应用基于Vue 3 + Vite架构，通过HTTP客户端与后端API通信。前端使用Vite开发服务器的反向代理功能解决跨域问题，所有API请求通过代理转发到后端8000端口。

### 4.1 API 端点总览

后端FastAPI服务提供6个API路由模块，分别对应不同的业务功能。所有端点都挂载在主应用下，通过路由前缀区分不同模块。

| 模块 | 前缀 | 主要端点 | 说明 |
|------|------|----------|------|
| auth | /auth | /login, /register, /me | 用户认证和授权 |
| chat | /llm | /chat, /chat/stream | 聊天功能（流式/非流式） |
| knowledge | /knowledge | /libraries, /documents | 知识库和文档管理 |
| rag | /rag | /query, /index | 基础RAG操作 |
| crawl | /crawl | /site, /load-document | 文档爬取和加载 |
| visual | /visual | /graph/{collection_id} | 知识图谱可视化 |

### 4.2 认证接口详情

**POST /auth/login - 用户登录**

请求参数:
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

响应格式:
```json
{
  "code": 200,
  "message": "登录成功",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIs...",
    "user": {
      "id": 1,
      "username": "username",
      "email": "user@example.com"
    }
  }
}
```

**POST /auth/register - 用户注册**

请求参数:
```json
{
  "username": "newuser",
  "email": "user@example.com",
  "password": "password123"
}
```

**GET /auth/me - 获取当前用户信息**

请求头: `Authorization: Bearer <token>`

响应格式:
```json
{
  "code": 200,
  "data": {
    "username": "username",
    "email": "user@example.com"
  }
}
```

### 4.3 聊天接口详情

**POST /llm/chat - 非流式聊天**

请求参数:
```json
{
  "content": "用户问题",
  "conversation_id": "uuid-string",
  "collection_id": "kb12_1760260169325"
}
```

**POST /llm/chat/stream - 流式聊天**

响应格式（Server-Sent Events）:
```
data: {"type": "start", "message": "开始生成..."}
data: {"type": "token", "content": "这是"}
data: {"type": "token", "content": "生成"}
data: {"type": "token", "content": "的"}
data: {"type": "token", "content": "回答"}
data: {"type": "end", "message": "生成完成"}
```

### 4.4 知识库接口详情

**GET /knowledge/libraries - 获取知识库列表**

**POST /knowledge/libraries - 创建知识库**

请求参数:
```json
{
  "title": "技术文档知识库",
  "description": "用于存储技术文档"
}
```

**GET /knowledge/libraries/{library_id} - 获取知识库详情**

**POST /knowledge/documents - 添加文档**

请求参数:
```json
{
  "library_id": 1,
  "name": "产品手册.pdf",
  "type": "pdf",
  "url": "https://oss.example.com/doc.pdf"
}
```

**DELETE /knowledge/documents/{document_id} - 删除文档**

### 4.5 认证配置参数

| 参数 | 配置值来源 | 默认值 | 说明 |
|------|-----------|--------|------|
| JWT_SECRET_KEY | .env文件 | [需要配置] | JWT签名密钥，生产环境必须使用强随机字符串 |
| JWT_ALGORITHM | .env文件 | HS256 | JWT加密算法 |
| JWT_ACCESS_TOKEN_EXPIRES | .env文件 | 86400秒（24小时） | Access Token过期时间 |
| JWT_REFRESH_TOKEN_EXPIRES | .env文件 | 604800秒（7天） | Refresh Token过期时间 |

**当前系统说明**: 根据代码分析，当前系统采用单token机制，refresh token功能已简化。Access Token有效期为24小时，过期后用户需要重新登录。

### 4.6 Vite 开发服务器配置

```javascript
// rag-frontend/vite.config.js
export default defineConfig({
  server: {
    host: "0.0.0.0",
    proxy: {
      // 认证接口代理
      '/auth': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      },
      // 聊天和对话接口代理
      '/llm': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      },
      // 知识库管理接口代理
      '/knowledge': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      },
      // 爬虫接口代理
      '/crawl': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      },
      // 可视化接口代理
      '/visual': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      },
      // 通用API接口代理（可选）
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  }
})
```

### 4.7 前端 HTTP 客户端配置

前端使用自定义HttpClient类封装fetch请求，自动处理token注入和错误处理：

```javascript
// rag-frontend/src/api/config.js
export const API_CONFIG = {
  BASE_URL: '',           // 使用相对路径，通过代理转发
  TIMEOUT: 30000,         // 请求超时30秒
  DEFAULT_HEADERS: {
    'Content-Type': 'application/json'
  }
}

// Token自动注入
getHeaders() {
  const headers = { ...API_CONFIG.DEFAULT_HEADERS }
  const token = this.getToken()
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  return headers
}
```

**Token存储位置**: localStorage的`auth_token`字段
**用户信息存储**: localStorage的`user_info`字段

---

## 5. 实体关系图 (ER图)

以下是使用Mermaid语法表示的实体关系图，清晰展示所有数据表之间的关联关系。

```mermaid
erDiagram
    users ||--o{ conversations : "创建"
    users ||--o{ knowledge_libraries : "创建"
    conversations ||--o{ chat_history : "包含"
    knowledge_libraries ||--o{ knowledge_documents : "包含"
    
    users {
        int id PK "用户ID"
        varchar username UK "用户名"
        varchar email UK "邮箱"
        varchar password_hash "密码哈希"
        bool is_active "激活状态"
        datetime created_at "创建时间"
        datetime updated_at "更新时间"
    }
    
    conversations {
        int id PK "内部ID"
        varchar conversation_id UK "会话UUID"
        varchar title "会话标题"
        int user_id FK "用户ID"
        datetime created_at "创建时间"
        datetime updated_at "更新时间"
    }
    
    chat_history {
        int id PK "记录ID"
        varchar conversation_id FK "会话UUID"
        varchar role "角色"
        varchar type "消息类型"
        text content "消息内容"
        json extra_data "扩展数据"
    }
    
    knowledge_libraries {
        int id PK "知识库ID"
        varchar collection_id UK "集合UUID"
        varchar title "标题"
        text description "描述"
        varchar user_id FK "用户ID"
        bool is_active "激活状态"
        datetime created_at "创建时间"
        datetime updated_at "更新时间"
    }
    
    knowledge_documents {
        int id PK "文档ID"
        int library_id FK "知识库ID"
        varchar name "文档名称"
        varchar type "文档类型"
        varchar url "链接地址"
        varchar file_path "存储路径"
        int file_size "文件大小"
        bool is_processed "处理状态"
        datetime created_at "创建时间"
        datetime updated_at "更新时间"
    }
```

**关系说明**:

1. **users → conversations (1对多)**
   - 一个用户可以创建多个对话会话
   - 通过conversations.user_id外键关联
   - 删除用户时，对话会话保留（不建议级联删除）

2. **users → knowledge_libraries (1对多)**
   - 一个用户可以创建多个知识库
   - 通过knowledge_libraries.user_id外键关联
   - 删除用户时，知识库保留

3. **conversations → chat_history (1对多)**
   - 一个对话会话包含多条聊天记录
   - 通过chat_history.conversation_id外键关联
   - 删除对话时，聊天记录级联删除

4. **knowledge_libraries → knowledge_documents (1对多)**
   - 一个知识库包含多个文档
   - 通过knowledge_documents.library_id外键关联
   - 删除知识库时，文档记录级联删除

**数据隔离策略**:
- 所有数据表通过user_id字段实现用户级数据隔离
- 知识库通过collection_id实现向量存储的物理隔离
- 对话通过conversation_id实现上下文隔离
- API层使用`Depends(get_current_user)`装饰器自动验证权限

---

## 6. 常用查询示例

以下提供系统中最常用的数据库查询示例，帮助开发者理解数据访问模式。所有示例使用SQLAlchemy ORM语法编写。

### 6.1 查询用户所有对话并获取最近消息

```python
from backend.config.database import DatabaseFactory
from backend.model.conversation import Conversation
from backend.model.chat_history import ChatHistory
from sqlalchemy import desc

def get_user_conversations_with_latest_message(user_id: int, limit: int = 10):
    """获取用户的所有对话会话列表，包含每条会话的最后一条消息"""
    db = DatabaseFactory.create_session()
    try:
        # 查询用户的对话会话，按更新时间倒序
        conversations = (
            db.query(Conversation)
            .filter(Conversation.user_id == user_id)
            .order_by(desc(Conversation.updated_at))
            .limit(limit)
            .all()
        )
        
        result = []
        for conv in conversations:
            # 查询每个对话的最后一条消息
            latest_message = (
                db.query(ChatHistory)
                .filter(ChatHistory.conversation_id == conv.conversation_id)
                .order_by(desc(ChatHistory.id))
                .first()
            )
            
            result.append({
                'conversation_id': conv.conversation_id,
                'title': conv.title,
                'updated_at': conv.updated_at,
                'latest_message': latest_message.content if latest_message else None,
                'latest_role': latest_message.role if latest_message else None
            })
        
        return result
    finally:
        db.close()
```

### 6.2 获取知识库文档列表及处理状态

```python
from backend.config.database import DatabaseFactory
from backend.model.knowledge_library import KnowledgeLibrary, KnowledgeDocument

def get_library_documents(library_id: int, user_id: int):
    """获取指定知识库的所有文档列表及处理状态"""
    db = DatabaseFactory.create_session()
    try:
        # 查询知识库信息
        library = (
            db.query(KnowledgeLibrary)
            .filter(
                KnowledgeLibrary.id == library_id,
                KnowledgeLibrary.user_id == user_id
            )
            .first()
        )
        
        if not library:
            return None
        
        # 查询所有文档
        documents = (
            db.query(KnowledgeDocument)
            .filter(KnowledgeDocument.library_id == library_id)
            .order_by(desc(KnowledgeDocument.created_at))
            .all()
        )
        
        return {
            'library': library.to_dict(),
            'documents': [doc.to_dict() for doc in documents],
            'total_count': len(documents),
            'processed_count': sum(1 for doc in documents if doc.is_processed)
        }
    finally:
        db.close()
```

### 6.3 获取对话历史消息

```python
from backend.config.database import DatabaseFactory
from backend.model.chat_history import ChatHistory
from sqlalchemy import asc

def get_conversation_history(conversation_id: str, limit: int = 50):
    """获取指定对话的历史消息记录"""
    db = DatabaseFactory.create_session()
    try:
        messages = (
            db.query(ChatHistory)
            .filter(ChatHistory.conversation_id == conversation_id)
            .order_by(asc(ChatHistory.id))  # 按时间正序返回
            .limit(limit)
            .all()
        )
        
        return [msg.to_dict() for msg in messages]
    finally:
        db.close()

def get_conversation_message_count(conversation_id: str) -> int:
    """统计对话的消息数量"""
    db = DatabaseFactory.create_session()
    try:
        count = (
            db.query(ChatHistory)
            .filter(ChatHistory.conversation_id == conversation_id)
            .count()
        )
        return count
    finally:
        db.close()
```

### 6.4 创建新用户和知识库

```python
from backend.config.database import DatabaseFactory
from backend.model.user import User
from backend.model.knowledge_library import KnowledgeLibrary
from backend.config.jwt import hash_password
import uuid

def create_user_with_library(username: str, email: str, password: str, 
                             library_title: str, library_description: str = None):
    """创建新用户并为其创建默认知识库"""
    db = DatabaseFactory.create_session()
    try:
        # 创建用户
        new_user = User(
            username=username,
            email=email,
            password_hash=hash_password(password)
        )
        db.add(new_user)
        db.flush()  # 获取用户ID
        
        # 创建知识库
        new_library = KnowledgeLibrary(
            collection_id=f"kb{new_user.id}_{int(uuid.uuid4().time * 1000)}",
            title=library_title,
            description=library_description,
            user_id=str(new_user.id)
        )
        db.add(new_library)
        
        db.commit()
        
        return {
            'user': new_user.to_dict(),
            'library': new_library.to_dict()
        }
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()
```

### 6.5 更新对话标题

```python
from backend.config.database import DatabaseFactory
from backend.model.conversation import Conversation

def update_conversation_title(conversation_id: str, new_title: str, user_id: int):
    """更新对话标题"""
    db = DatabaseFactory.create_session()
    try:
        conversation = (
            db.query(Conversation)
            .filter(
                Conversation.conversation_id == conversation_id,
                Conversation.user_id == user_id
            )
            .first()
        )
        
        if not conversation:
            return False
        
        conversation.title = new_title
        db.commit()
        
        return True
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()
```

### 6.6 统计用户活跃数据

```python
from backend.config.database import DatabaseFactory
from backend.model.user import User
from backend.model.conversation import Conversation
from backend.model.chat_history import ChatHistory
from backend.model.knowledge_library import KnowledgeLibrary
from sqlalchemy import func

def get_user_activity_stats(user_id: int):
    """获取用户的活跃统计数据"""
    db = DatabaseFactory.create_session()
    try:
        stats = {
            'total_conversations': (
                db.query(func.count(Conversation.id))
                .filter(Conversation.user_id == user_id)
                .scalar()
            ),
            'total_knowledge_libraries': (
                db.query(func.count(KnowledgeLibrary.id))
                .filter(KnowledgeLibrary.user_id == user_id)
                .scalar()
            ),
            'total_messages': (
                db.query(func.count(ChatHistory.id))
                .join(Conversation)
                .filter(Conversation.user_id == user_id)
                .scalar()
            ),
            'user_since': (
                db.query(User.created_at)
                .filter(User.id == user_id)
                .scalar()
            )
        }
        return stats
    finally:
        db.close()
```

### 6.7 软删除知识库

```python
from backend.config.database import DatabaseFactory
from backend.model.knowledge_library import KnowledgeLibrary

def soft_delete_library(library_id: int, user_id: int):
    """软删除知识库（设置is_active=False）"""
    db = DatabaseFactory.create_session()
    try:
        library = (
            db.query(KnowledgeLibrary)
            .filter(
                KnowledgeLibrary.id == library_id,
                KnowledgeLibrary.user_id == user_id
            )
            .first()
        )
        
        if not library:
            return False
        
        library.is_active = False
        db.commit()
        
        return True
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

def get_active_libraries_only(user_id: int):
    """仅查询激活状态的知识库"""
    db = DatabaseFactory.create_session()
    try:
        libraries = (
            db.query(KnowledgeLibrary)
            .filter(
                KnowledgeLibrary.user_id == user_id,
                KnowledgeLibrary.is_active == True
            )
            .order_by(desc(KnowledgeLibrary.updated_at))
            .all()
        )
        
        return [lib.to_dict() for lib in libraries]
    finally:
        db.close()
```

---

## 附录：完整环境配置清单

以下是系统中所有可配置的环境变量完整清单，按功能分类整理。

### 数据库配置

| 变量名 | 默认值 | 是否必需 | 说明 |
|--------|--------|----------|------|
| DB_URL | mysql+pymysql://root:password@localhost:3306/rag_db | 是 | MySQL完整连接字符串 |
| POSTGRES_HOST | localhost | 是 | PostgreSQL主机地址 |
| POSTGRES_PORT | 5432 | 是 | PostgreSQL端口 |
| POSTGRES_DATABASE | rag_checkpoint | 是 | PostgreSQL数据库名 |
| POSTGRES_USER | postgres | 是 | PostgreSQL用户名 |
| POSTGRES_PASSWORD | 123456 | 是 | PostgreSQL密码 |
| MILVUS_URI | localhost:19530 | 是 | Milvus连接地址 |
| MILVUS_DB_NAME | default | 否 | Milvus数据库名 |

### API密钥配置

| 变量名 | 是否必需 | 说明 |
|--------|----------|------|
| DASHSCOPE_API_KEY | 是 | 阿里云DashScope API密钥，用于通义千问模型 |
| DEEPSEEK_API_KEY | 否 | DeepSeek API密钥（可选） |
| MINERU_API_URL | 否 | MinerU OCR服务地址 |
| MINERU_API_KEY | 否 | MinerU API密钥 |

### 认证配置

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| JWT_SECRET_KEY | [需要配置] | JWT签名密钥，生产环境必须修改 |
| JWT_ALGORITHM | HS256 | JWT加密算法 |
| JWT_ACCESS_TOKEN_EXPIRES | 86400 | Access Token过期时间（秒） |
| JWT_REFRESH_TOKEN_EXPIRES | 604800 | Refresh Token过期时间（秒） |

### 应用配置

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| APP_ENV | development | 应用运行模式 |
| LOG_LEVEL | INFO | 日志级别 |
| API_HOST | 0.0.0.0 | API服务绑定地址 |
| API_PORT | 8000 | API服务端口 |

### LangGraph配置

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| LANGGRAPH_ENABLE_CHECKPOINT | true | 是否启用Checkpoint |
| LANGGRAPH_STUDIO_MODE | false | Studio调试模式 |

### 文档处理配置

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| CHUNK_SIZE | 1000 | 文档切块大小 |
| CHUNK_OVERLAP | 200 | 文档切块重叠大小 |
| MAX_DOCUMENT_SIZE | 50 | 最大文档大小（MB） |

### 检索配置

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| DEFAULT_RETRIEVAL_MODE | auto | 默认检索模式 |
| VECTOR_SEARCH_TOP_K | 5 | 向量检索返回数量 |
| GRAPH_SEARCH_MODE | hybrid | 图检索模式 |

---

本文档完整记录了AdaptiMultiRAG系统的数据库表结构、连接配置和API接口信息。建议开发人员在进行系统开发、数据分析和问题排查时参考此文档。
