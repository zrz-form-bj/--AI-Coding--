"""
配置文件 - 需要手动配置API密钥
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """应用配置"""
    
    # ========== 阿里云配置 ==========
    # 通义千问 API Key (必需)
    # 获取方式: https://dashscope.console.aliyun.com/apiKey
    DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
    
    # 阿里云短信配置 (必需)
    # 获取方式: https://dysms.console.aliyun.com/
    ALIYUN_ACCESS_KEY_ID = os.getenv("ALIYUN_ACCESS_KEY_ID", "")
    ALIYUN_ACCESS_KEY_SECRET = os.getenv("ALIYUN_ACCESS_KEY_SECRET", "")
    ALIYUN_SMS_SIGN_NAME = os.getenv("ALIYUN_SMS_SIGN_NAME", "")  # 短信签名
    ALIYUN_SMS_TEMPLATE_CODE = os.getenv("ALIYUN_SMS_TEMPLATE_CODE", "")  # 短信模板CODE
    
    # ========== 百度地图配置 ==========
    # 获取方式: https://lbsyun.baidu.com/
    BAIDU_MAP_AK = os.getenv("BAIDU_MAP_AK", "")  # 百度地图AK
    
    # ========== 天气API配置 ==========
    # 使用和风天气: https://dev.qweather.com/
    QWEATHER_API_KEY = os.getenv("QWEATHER_API_KEY", "")
    # 企业版API Host（可选），免费版留空
    # 示例: hn62b78g24.re.qweatherapi.com
    QWEATHER_API_HOST = os.getenv("QWEATHER_API_HOST", "")
    
    # ========== 邮件配置 ==========
    SMTP_HOST = os.getenv("SMTP_HOST", "smtp.163.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
    SMTP_USER = os.getenv("SMTP_USER", "")  # 发件人邮箱
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")  # 邮箱授权码
    
    # ========== 数据库配置 ==========
    # 基于 __file__ 定位 backend 目录，创建 data 子目录存放数据库
    # 本地、Render、其他服务器统一使用此路径，稳定可靠
    _BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
    _DATA_DIR = os.path.join(_BACKEND_DIR, "data")
    os.makedirs(_DATA_DIR, exist_ok=True)
    _DB_PATH = os.path.join(_DATA_DIR, "elderly_assistant.db")
    # 支持通过环境变量 DATABASE_URL 覆盖（可选）
    DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite+aiosqlite:///{_DB_PATH}")
    
    # ========== 应用配置 ==========
    APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT = int(os.getenv("APP_PORT", "8000"))
    
    # ========== 模型配置 ==========
    LLM_MODEL = os.getenv("LLM_MODEL", "qwen-max")
    LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "2000"))
    
    # ========== 工具重试配置 ==========
    TOOL_MAX_RETRIES = int(os.getenv("TOOL_MAX_RETRIES", "3"))
    TOOL_RETRY_DELAY = float(os.getenv("TOOL_RETRY_DELAY", "1.0"))


config = Config()


def validate_config():
    """验证必需的配置项"""
    missing = []
    
    if not config.DASHSCOPE_API_KEY:
        missing.append("DASHSCOPE_API_KEY (通义千问API密钥)")
    
    if not config.BAIDU_MAP_AK:
        missing.append("BAIDU_MAP_AK (百度地图AK)")
    
    if missing:
        print("=" * 60)
        print("⚠️  以下配置项缺失，请在 .env 文件中配置：")
        for item in missing:
            print(f"   - {item}")
        print("=" * 60)
        print("\n配置方法请参考 .env.example 文件\n")
    
    return len(missing) == 0
