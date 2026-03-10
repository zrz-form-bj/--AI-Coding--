@echo off
chcp 65001 >nul
echo ========================================
echo    老年人智能助手 - 启动脚本
echo ========================================
echo.

cd backend

echo [1/3] 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未找到Python，请先安装Python 3.9+
    pause
    exit /b 1
)

echo [2/3] 安装依赖...
pip install -r requirements.txt -q

echo [3/3] 检查配置文件...
if not exist .env (
    echo ⚠️  未找到.env配置文件，正在从模板创建...
    copy .env.example .env >nul
    echo.
    echo ========================================
    echo    ⚠️  请先配置.env文件中的API密钥
    echo ========================================
    echo.
    echo 必需配置项：
    echo   - DASHSCOPE_API_KEY (通义千问)
    echo   - BAIDU_MAP_AK (百度地图)
    echo.
    echo 可选配置项：
    echo   - 阿里云短信（用于SOS功能）
    echo   - 天气API
    echo   - 邮件服务
    echo.
    notepad .env
)

echo.
echo ========================================
echo    正在启动后端服务...
echo ========================================
echo.
echo API文档: http://localhost:8000/docs
echo.
python main.py
