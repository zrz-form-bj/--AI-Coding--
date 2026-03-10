# 老年人智能助手

为老年人提供的智能语音助手系统，支持语音交互、路线导航、紧急求助等功能。

## 功能特点

- 🎤 **语音交互**：语音识别转文字，大模型智能分析
- 🗺️ **路线导航**：查询去亲友家的路线
- 🌤️ **天气查询**：查询天气情况
- 📞 **联系人管理**：查询亲友电话、地址
- 🆘 **紧急求助**：一键发送位置给紧急联系人

## 快速开始

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 配置API密钥

复制配置模板：
```bash
copy .env.example .env
```

编辑 `.env` 文件，配置以下必需项：

```env
# 必需配置
DASHSCOPE_API_KEY=your_dashscope_api_key    # 通义千问API
BAIDU_MAP_AK=your_baidu_map_ak              # 百度地图AK

# SOS功能需要（可选）
ALIYUN_ACCESS_KEY_ID=your_access_key
ALIYUN_ACCESS_KEY_SECRET=your_secret
ALIYUN_SMS_SIGN_NAME=短信签名
ALIYUN_SMS_TEMPLATE_CODE=模板CODE
```

### 3. 初始化数据库

```bash
python init_data.py
```

### 4. 启动服务

```bash
python main.py
```

或使用启动脚本：
```bash
cd ..
start.bat
```

### 5. 访问前端

在浏览器中打开 `frontend/index.html` 文件

## API密钥获取方式

| 服务 | 获取地址 | 免费额度 |
|------|---------|---------|
| 通义千问 | https://dashscope.console.aliyun.com/ | 100万tokens/月 |
| 百度地图 | https://lbsyun.baidu.com/ | 30万次/天 |
| 阿里云短信 | https://dysms.console.aliyun.com/ | 按量付费 |
| 和风天气 | https://dev.qweather.com/ | 1000次/天 |

## 项目结构

```
助老AI项目/
├── frontend/
│   └── index.html          # 前端页面
│
├── backend/
│   ├── main.py             # FastAPI入口
│   ├── config.py           # 配置管理
│   ├── init_data.py        # 数据库初始化
│   ├── .env.example        # 配置模板
│   ├── requirements.txt    # Python依赖
│   │
│   ├── models/
│   │   ├── database.py     # 数据库模型
│   │   └── schemas.py      # API模型
│   │
│   ├── agent/
│   │   ├── llm.py          # LLM配置
│   │   ├── agent.py        # LangChain Agent
│   │   └── prompts.py      # 提示词
│   │
│   └── tools/
│       ├── baidu_map.py    # 百度地图工具
│       ├── weather.py      # 天气查询
│       ├── sms.py          # 短信发送
│       ├── email.py        # 邮件发送
│       ├── contact.py      # 联系人查询
│       ├── emergency.py    # 紧急信息
│       └── memo.py         # 记事功能
│
└── start.bat               # Windows启动脚本
```

## API接口

### 智能助手
```
POST /api/assistant
{
    "text": "我要去女儿家怎么走",
    "elderly_id": 1,
    "lat": "39.9042",
    "lng": "116.4074"
}
```

### SOS紧急求助
```
POST /api/sos
{
    "lat": "39.9042",
    "lng": "116.4074",
    "elderly_id": 1
}
```

### 联系人管理
```
GET  /api/contacts/{elderly_id}    # 获取联系人列表
POST /api/contacts                 # 添加联系人
DELETE /api/contacts/{contact_id}  # 删除联系人
```

## 使用说明

1. **智能助手**：点击蓝色按钮，说出需求，如"我要去女儿家怎么走"
2. **紧急求助**：点击红色SOS按钮，自动发送位置给紧急联系人

## 注意事项

- 前端需要在HTTPS环境下运行（本地开发localhost除外）
- 首次使用需要授权麦克风和位置权限
- SOS短信功能需要配置阿里云短信服务

## 技术栈

- 前端：HTML + JavaScript (Web Speech API)
- 后端：Python + FastAPI
- LLM：通义千问 (qwen-max)
- 框架：LangChain 1.0+
- 数据库：SQLite
