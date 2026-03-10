# 老年人智能助手系统

## 项目概述

**项目名称**：老年人智能助手系统  
**版本**：1.1.0  
**开发语言**：Python 3.9+ / JavaScript  
**核心框架**：LangChain 1.0+ / FastAPI  

### 项目简介

这是一个专为老年人设计的智能语音助手系统，通过语音交互帮助老年人解决日常生活中的常见问题，包括路线导航、天气查询、联系人管理、紧急求助、周期性提醒等功能。同时提供管理后台，方便家属或工作人员管理老人信息。

### 核心功能

| 功能模块 | 描述 |
|---------|------|
| 🎤 语音交互 | Web Speech API 实现语音识别，最长录音1分钟 |
| 🤖 智能对话 | 基于通义千问(qwen-max)的大模型智能分析 |
| 🗺️ 路线导航 | 百度地图API，支持查询去亲友家的路线 |
| 🌤️ 天气查询 | 和风天气API，查询当地天气情况 |
| 📞 联系人管理 | 数据库存储亲友信息，支持查询电话、地址 |
| 🆘 紧急求助 | 一键获取位置，发送邮件通知紧急联系人 |
| 📝 记事提醒 | 支持一次性提醒和周期性提醒（每天/每周/每月） |
| 📧 邮件提醒 | 定时发送提醒邮件到老人邮箱 |
| 👨‍💼 管理后台 | 用户管理、联系人管理、记事管理、对话记录查看 |
| 📊 批量导入 | Excel批量导入老人信息 |

---

## 技术架构

### 系统架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                         前端 (HTML/JavaScript)                   │
│  ┌─────────────────────┐        ┌─────────────────────┐         │
│  │    智能助手按钮      │        │      SOS按钮        │         │
│  │  Web Speech API     │        │  Geolocation API    │         │
│  │    语音 → 文字      │        │     获取位置        │         │
│  └──────────┬──────────┘        └──────────┬──────────┘         │
│             │                              │                     │
│             ▼                              ▼                     │
│    POST /api/assistant            POST /api/sos                  │
└─────────────┼──────────────────────────────┼─────────────────────┘
              │                              │
              ▼                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    后端 (Python + FastAPI)                       │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │               LangChain 1.0+ Agent                       │   │
│  │                  (qwen-max 模型)                         │   │
│  │                         │                                │   │
│  │      ┌──────────────────┼──────────────────┐            │   │
│  │      ▼                  ▼                  ▼            │   │
│  │  ┌────────┐       ┌────────┐        ┌────────┐         │   │
│  │  │百度地图│       │天气查询│        │邮件发送│         │   │
│  │  │  Tool  │       │  Tool  │        │  Tool  │         │   │
│  │  └────────┘       └────────┘        └────────┘         │   │
│  │      │                  │                  │            │   │
│  │      ▼                  ▼                  ▼            │   │
│  │  ┌────────┐       ┌────────┐        ┌────────┐         │   │
│  │  │联系人  │       │紧急信息│        │记事功能│         │   │
│  │  │查询Tool│       │  Tool  │        │  Tool  │         │   │
│  │  └────────┘       └────────┘        └────────┘         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│              ┌───────────────┼───────────────┐                 │
│              ▼               ▼               ▼                 │
│      ┌────────────┐  ┌────────────┐  ┌────────────┐           │
│      │ 提醒调度器  │  │ 管理后台API │  │ Excel导入  │           │
│      └────────────┘  └────────────┘  └────────────┘           │
│              │               │                                  │
│              └───────────────┼──────────────────────────────────│
│                              ▼                                  │
│                     ┌──────────────┐                           │
│                     │   数据库      │                           │
│                     │   SQLite     │                           │
│                     └──────────────┘                           │
└─────────────────────────────────────────────────────────────────┘
```

### 技术栈详情

#### 前端技术
| 技术 | 用途 |
|------|------|
| HTML5 + CSS3 | 页面结构与样式 |
| JavaScript (ES6+) | 交互逻辑 |
| Web Speech API | 语音识别 |
| Geolocation API | GPS定位 |
| SpeechSynthesis API | 语音播报 |
| Fetch API | HTTP请求 |

#### 后端技术
| 技术 | 版本 | 用途 |
|------|------|------|
| Python | 3.9+ | 后端语言 |
| FastAPI | 0.109.0 | Web框架 |
| LangChain | 0.1.20 | LLM应用框架 |
| langchain-core | 0.1.52 | 核心抽象层 |
| langchain-openai | 0.1.6 | OpenAI兼容接口 |
| SQLAlchemy | 2.0.25 | ORM框架 |
| SQLite | - | 轻量级数据库 |
| aiosmtplib | 3.0.1 | 异步邮件发送 |
| openpyxl | 3.1.2 | Excel处理 |
| httpx | 0.26.0 | HTTP客户端 |

#### AI/LLM
| 组件 | 说明 |
|------|------|
| 模型 | 通义千问 qwen-max |
| 接口 | 阿里云 DashScope API |
| 框架 | LangChain Agent + Function Calling |

---

## 项目结构

```
助老AI Coding项目/
│
├── frontend/                    # 前端目录
│   ├── index.html              # 主页面（语音交互界面）
│   ├── login.html              # 登录/注册页面
│   └── admin/                  # 管理后台
│       └── index.html          # 管理后台主页面
│
├── backend/                     # 后端目录
│   ├── main.py                 # FastAPI 应用入口
│   ├── config.py               # 配置管理
│   ├── requirements.txt        # Python 依赖
│   ├── elderly_assistant.db    # SQLite 数据库
│   ├── .env                    # 环境变量配置（需手动创建）
│   ├── .env.example            # 配置模板
│   │
│   ├── models/                 # 数据模型
│   │   ├── __init__.py
│   │   ├── database.py         # 数据库模型定义
│   │   └── schemas.py          # Pydantic 请求/响应模型
│   │
│   ├── agent/                  # LangChain Agent
│   │   ├── __init__.py
│   │   ├── agent.py            # Agent 实现
│   │   ├── llm.py              # LLM 配置
│   │   ├── prompts.py          # 提示词模板
│   │   └── callbacks.py        # 回调处理
│   │
│   └── tools/                  # 工具模块
│       ├── __init__.py         # 工具导出
│       ├── baidu_map.py        # 百度地图工具
│       ├── weather.py          # 天气查询工具
│       ├── sms.py              # 短信工具（需企业认证，已停用）
│       ├── email.py            # 邮件发送工具
│       ├── contact.py          # 联系人查询工具
│       ├── emergency.py        # 紧急信息工具
│       ├── memo.py             # 记事工具
│       ├── auth.py             # 用户认证服务
│       ├── admin_service.py    # 管理后台服务
│       ├── conversation_history.py  # 对话历史服务
│       ├── reminder_scheduler.py    # 提醒调度器
│       └── excel_import.py     # Excel批量导入服务
│
├── start.bat                   # Windows 启动脚本
├── README.md                   # 项目说明
└── PROJECT_GUIDE.md            # 项目指南（本文档）
```

---

## 工具清单

### 核心工具

| 工具名称 | 功能描述 | API依赖 |
|---------|---------|---------|
| `baidu_map_navigation` | 路线规划、地址搜索 | 百度地图AK |
| `baidu_map_search_place` | 搜索附近设施 | 百度地图AK |
| `baidu_map_get_address` | 经纬度转地址 | 百度地图AK |
| `query_weather` | 当前天气查询 | 和风天气API |
| `query_weather_forecast` | 3天天气预报 | 和风天气API |
| `query_contact_phone` | 查询联系人电话 | 数据库 |
| `query_contact_address` | 查询联系人地址 | 数据库 |
| `list_all_contacts` | 列出所有联系人 | 数据库 |
| `query_home_address` | 查询家庭住址 | 数据库 |
| `make_call` | 拨打电话 | 无 |
| `send_email` | 发送邮件通知 | SMTP |
| `send_sos_email` | 发送紧急邮件 | SMTP |
| `query_time` | 查询当前时间 | 无 |

### 紧急信息工具（硬编码）

| 工具名称 | 功能描述 |
|---------|---------|
| `query_emergency_shelter` | 查询紧急避难所 |
| `query_nearby_hospital` | 查询附近医院 |
| `query_nearby_pharmacy` | 查询附近药店 |
| `query_emergency_numbers` | 查询紧急电话 |
| `query_health_tips` | 健康提醒 |
| `query_medical_help` | 医护救援信息 |

### 记事功能

| 工具名称 | 功能描述 |
|---------|---------|
| `add_memo` | 添加记事（支持一次性/周期性） |
| `list_memos` | 查看记事列表 |

---

## 数据库设计

### 表结构

#### 1. 用户表 (users)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| username | VARCHAR(50) | 用户名（唯一） |
| password_hash | VARCHAR(200) | 密码哈希 |
| phone | VARCHAR(20) | 手机号 |
| created_at | DATETIME | 创建时间 |

#### 2. 老人信息表 (elderly_info)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| user_id | INTEGER | 关联用户ID（外键） |
| name | VARCHAR(50) | 姓名 |
| phone | VARCHAR(20) | 手机号 |
| email | VARCHAR(100) | 邮箱（用于接收提醒） |
| home_address | VARCHAR(200) | 家庭住址 |
| home_lat | VARCHAR(20) | 家庭住址纬度 |
| home_lng | VARCHAR(20) | 家庭住址经度 |
| health_info | TEXT | 健康信息 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

#### 3. 联系人表 (contacts)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| elderly_id | INTEGER | 关联的老人ID（外键） |
| name | VARCHAR(50) | 姓名 |
| contact_relationship | VARCHAR(20) | 关系（女儿/儿子等） |
| phone | VARCHAR(20) | 电话 |
| email | VARCHAR(100) | 邮箱 |
| address | VARCHAR(200) | 住址 |
| lat | VARCHAR(20) | 纬度 |
| lng | VARCHAR(20) | 经度 |
| is_emergency | BOOLEAN | 是否紧急联系人 |
| created_at | DATETIME | 创建时间 |

#### 4. 记事表 (memos)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| elderly_id | INTEGER | 关联的老人ID |
| content | TEXT | 记事内容 |
| memo_type | VARCHAR(20) | 记事类型: once(一次性) / periodic(周期性) |
| reminder_time | DATETIME | 提醒时间（一次性）或提醒时间点（周期性） |
| repeat_type | VARCHAR(20) | 重复类型: daily(每天) / weekly(每周) / monthly(每月) |
| repeat_days | VARCHAR(50) | 重复日期: 周几提醒，如'1,3,5'表示周一三五 |
| end_date | DATETIME | 结束日期（周期性记事可选） |
| is_completed | BOOLEAN | 是否已完成 |
| created_at | DATETIME | 创建时间 |

#### 5. 对话历史表 (conversation_history)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| elderly_id | INTEGER | 关联的老人ID |
| role | VARCHAR(20) | 角色（user/assistant） |
| content | TEXT | 对话内容 |
| created_at | DATETIME | 创建时间 |

#### 6. 管理员表 (admin_users)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| username | VARCHAR(50) | 用户名（唯一） |
| password_hash | VARCHAR(200) | 密码哈希 |
| name | VARCHAR(50) | 姓名 |
| role | VARCHAR(20) | 角色: super_admin / admin |
| is_active | BOOLEAN | 是否激活 |
| last_login | DATETIME | 最后登录时间 |
| created_at | DATETIME | 创建时间 |

---

## API 接口文档

### 基础接口

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/` | 服务状态检查 |
| GET | `/health` | 健康检查 |

### 用户认证

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/register` | 用户注册 |
| POST | `/api/login` | 用户登录 |

### 智能助手

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/assistant` | 智能对话接口 |

**请求示例：**
```json
{
    "text": "我要去女儿家怎么走",
    "elderly_id": 1,
    "lat": "39.9042",
    "lng": "116.4074"
}
```

**响应示例：**
```json
{
    "success": true,
    "reply": "您女儿家的地址是...",
    "action_taken": null
}
```

### SOS紧急求助

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/sos` | 发送紧急求助 |

**请求示例：**
```json
{
    "lat": "39.9042",
    "lng": "116.4074",
    "elderly_id": 1
}
```

**响应示例：**
```json
{
    "success": true,
    "message": "已向2位紧急联系人发送求助通知",
    "contacts_notified": 2,
    "location_text": "北京市朝阳区..."
}
```

### 老人信息管理

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/elderly` | 创建老人信息 |
| GET | `/api/elderly/{id}` | 获取老人信息 |

### 联系人管理

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/contacts/{elderly_id}` | 获取联系人列表 |
| POST | `/api/contacts` | 添加联系人 |
| DELETE | `/api/contacts/{id}` | 删除联系人 |

### 管理后台 API

#### 管理员认证

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/admin/login` | 管理员登录 |

#### 仪表盘

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/admin/dashboard` | 获取统计数据 |

#### 用户管理

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/admin/users` | 获取用户列表（支持搜索、分页） |
| POST | `/api/admin/users` | 创建用户 |
| GET | `/api/admin/users/{id}` | 获取用户详情 |
| PUT | `/api/admin/users/{id}` | 更新用户信息 |
| DELETE | `/api/admin/users/{id}` | 删除用户 |
| POST | `/api/admin/users/import` | 批量导入用户（Excel） |
| GET | `/api/admin/users/template/download` | 下载导入模板 |

#### 联系人管理（管理后台）

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/admin/contacts` | 获取联系人列表 |
| POST | `/api/admin/contacts` | 创建联系人 |
| PUT | `/api/admin/contacts/{id}` | 更新联系人 |
| DELETE | `/api/admin/contacts/{id}` | 删除联系人 |

#### 记事管理（管理后台）

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/admin/memos` | 获取记事列表 |
| POST | `/api/admin/memos` | 创建记事 |
| PUT | `/api/admin/memos/{id}` | 更新记事 |
| DELETE | `/api/admin/memos/{id}` | 删除记事 |

#### 对话记录

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/admin/conversations` | 获取对话历史（支持分页） |

#### 提醒管理

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/admin/trigger-reminders` | 手动触发提醒任务 |

---

## 配置说明

### 环境变量 (.env)

```env
# ========== 必需配置 ==========

# 通义千问 API Key
DASHSCOPE_API_KEY=your_dashscope_api_key

# 百度地图 AK
BAIDU_MAP_AK=your_baidu_map_ak

# ========== 可选配置 ==========

# 天气 API（和风天气）
QWEATHER_API_KEY=your_qweather_key

# 邮件服务（用于SOS和提醒通知）
SMTP_HOST=smtp.163.com
SMTP_PORT=465
SMTP_USER=your_email@163.com
SMTP_PASSWORD=your_email_auth_code

# 阿里云短信（需要企业认证，暂不使用）
ALIYUN_ACCESS_KEY_ID=
ALIYUN_ACCESS_KEY_SECRET=
ALIYUN_SMS_SIGN_NAME=
ALIYUN_SMS_TEMPLATE_CODE=

# ========== 应用配置 ==========
DATABASE_URL=sqlite+aiosqlite:///./elderly_assistant.db
APP_HOST=0.0.0.0
APP_PORT=8000

# ========== 模型配置 ==========
LLM_MODEL=qwen-max
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2000

# ========== 工具重试配置 ==========
TOOL_MAX_RETRIES=3
TOOL_RETRY_DELAY=1.0
```

### API Key 获取方式

| 服务 | 获取地址 | 免费额度 |
|------|---------|---------|
| 通义千问 | https://dashscope.console.aliyun.com/ | 100万 tokens/月 |
| 百度地图 | https://lbsyun.baidu.com/ | 30万次/天 |
| 和风天气 | https://dev.qweather.com/ | 1000次/天 |

---

## 部署指南

### 本地开发环境

#### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

#### 2. 配置环境变量

```bash
copy .env.example .env
# 编辑 .env 文件，填入 API Key
```

#### 3. 启动后端服务

```bash
python main.py
```

服务启动时会自动：
- 初始化数据库
- 创建默认管理员账号（admin / admin123）

#### 4. 访问前端

- 主页面：直接在浏览器打开 `frontend/index.html`
- 管理后台：打开 `frontend/admin/login.html`

#### 5. 使用启动脚本（Windows）

双击 `start.bat` 即可自动安装依赖并启动服务。

### 生产环境部署

#### 后端部署

```bash
# 使用 gunicorn + uvicorn
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

#### 前端部署

需要 HTTPS 环境（麦克风权限要求）：
1. 使用 Nginx 托管静态文件
2. 配置 SSL 证书
3. 修改 `API_BASE_URL` 为实际后端地址

---

## 使用说明

### 智能助手

1. 点击「智能助手」按钮
2. 允许麦克风权限
3. 说出需求，例如：
   - "我要去女儿家怎么走"
   - "今天天气怎么样"
   - "我女儿的电话是多少"
   - "现在几点了"
   - "提醒我明天早上8点吃药"

### SOS紧急求助

1. 点击「SOS紧急求助」按钮
2. 允许位置权限
3. 系统自动：
   - 获取当前位置
   - 反向地理编码获取地址
   - 发送邮件给紧急联系人

### 管理后台

1. 访问 `frontend/admin/login.html`
2. 使用管理员账号登录（默认: admin / admin123）
3. 功能：
   - 用户管理：添加、编辑、删除老人信息
   - 批量导入：通过Excel批量导入用户
   - 联系人管理：管理老人的紧急联系人
   - 记事管理：添加一次性或周期性提醒
   - 对话记录：查看老人与助手的对话历史

---

## 周期性提醒功能

### 提醒类型

| 类型 | 说明 |
|------|------|
| 一次性 (once) | 在指定时间提醒一次 |
| 每天 (daily) | 每天指定时间提醒 |
| 每周 (weekly) | 每周指定日期和时间提醒 |
| 每月 (monthly) | 每月指定日期和时间提醒 |

### 提醒机制

- 系统每5分钟检查一次即将到期的记事
- 匹配条件：提醒时间在当前时间前后5分钟内
- 发送邮件到老人填写的邮箱地址
- 支持手动触发：`POST /api/admin/trigger-reminders`

---

## 已知限制

| 限制 | 原因 | 解决方案 |
|------|------|---------|
| 短信功能不可用 | 需要企业认证 | 使用邮件替代 |
| HTTPS 要求 | 浏览器安全策略 | 本地开发可用 localhost |
| 自动拨打电话 | 浏览器安全限制 | 只能跳转拨号界面 |
| 手机访问需 HTTPS | 麦克风权限要求 | 部署到云服务器 |

---

## 更新日志

### v1.1.0 (2026-03-10)

- ✅ 新增管理后台功能
  - 用户管理（CRUD）
  - 联系人管理（CRUD）
  - 记事管理（CRUD）
  - 对话记录查看
  - 仪表盘统计
- ✅ 新增周期性提醒功能
  - 支持每天/每周/每月重复提醒
  - 后台调度器自动检查并发送提醒邮件
- ✅ 新增邮箱字段
  - 老人信息支持填写邮箱
  - 用于接收提醒通知
- ✅ 新增Excel批量导入功能
  - 支持下载模板
  - 支持批量导入用户信息
- ✅ 新增用户注册/登录功能
- ✅ 优化对话历史加载（近3天）

### v1.0.0 (2026-03-08)

- ✅ 完成基础架构搭建
- ✅ 实现 LangChain 1.0+ Agent
- ✅ 集成通义千问 qwen-max
- ✅ 实现语音识别和语音播报
- ✅ 实现百度地图路线规划
- ✅ 实现天气查询
- ✅ 实现联系人管理
- ✅ 实现 SOS 紧急求助（邮件）
- ✅ 数据库存储老人和联系人信息

---

## 技术支持

如有问题，请检查：
1. 后端服务是否正常运行
2. API Key 是否正确配置
3. 浏览器是否允许麦克风和位置权限
4. 网络连接是否正常

---

*本项目仅供学习和研究使用*
