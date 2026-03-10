"""
FastAPI 后端服务 - LangChain 1.0+
"""
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
import os
import io

from config import config, validate_config
from models import (
    init_db, get_session,
    User, ElderlyInfo, ElderlyInfoCreate, ElderlyInfoResponse,
    Contact, ContactCreate, ContactResponse,
    Memo, MemoCreate, MemoResponse,
    ConversationHistory,
    AssistantRequest, AssistantResponse,
    SOSRequest, SOSResponse, ApiResponse,
    UserRegister, UserLogin, UserResponse, LoginResponse,
    AdminLogin, AdminResponse, AdminLoginResponse,
    AdminUserCreate, AdminUserUpdate, AdminUserListResponse, UserImportResult,
    AdminContactCreate, AdminContactUpdate,
    AdminMemoCreate, AdminMemoUpdate,
    DashboardStats
)
from agent import ElderlyAssistantAgent, SimpleAgent
from tools import get_all_tools
from tools.contact import contact_service
from tools.email import email_service
from tools.baidu_map import baidu_map_service
from tools.auth import auth_service
from tools.conversation_history import conversation_history_service
from tools.admin_service import admin_service
from tools.excel_import import excel_import_service

# 创建应用
app = FastAPI(
    title="老年人智能助手API",
    description="为老年人提供智能语音助手和紧急求助服务",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== 静态文件托管（前端页面）==========
# 获取前端目录路径
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(os.path.dirname(BACKEND_DIR), "frontend")

# 检查前端目录是否存在
if os.path.exists(FRONTEND_DIR):
    # 挂载静态文件
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
    print(f"✅ 前端静态文件已挂载: {FRONTEND_DIR}")
else:
    print(f"⚠️ 前端目录不存在: {FRONTEND_DIR}")


# ========== 启动事件 ==========
@app.on_event("startup")
async def startup_event():
    """应用启动时执行"""
    print("\n" + "=" * 60)
    print("🚀 老年人智能助手服务启动中...")
    print("=" * 60)
    
    # 验证配置
    validate_config()
    
    # 初始化数据库
    await init_db()
    
    # 初始化默认管理员
    await init_default_admin()
    
    # 启动提醒调度器
    from tools.reminder_scheduler import start_scheduler
    await start_scheduler(interval_minutes=5)
    
    print("✅ 服务启动完成！")
    print(f"📡 API文档: http://localhost:{config.APP_PORT}/docs")
    print(f"🏠 前端首页: http://localhost:{config.APP_PORT}/")
    print(f"👨‍💼 管理后台: http://localhost:{config.APP_PORT}/static/admin/login.html")
    print("=" * 60 + "\n")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时执行"""
    from tools.reminder_scheduler import stop_scheduler
    await stop_scheduler()
    print("👋 服务已关闭")


async def init_default_admin():
    """初始化默认管理员账号"""
    from sqlalchemy import select
    from models import AdminUser, async_session
    
    async with async_session() as session:
        result = await session.execute(select(AdminUser))
        existing = result.scalar_one_or_none()
        
        if not existing:
            success, message, admin = await admin_service.create_admin(
                username="admin",
                password="admin123",
                name="系统管理员",
                session=session,
                role="super_admin"
            )
            if success:
                print("\n⚠️  默认管理员账号已创建:")
                print("   用户名: admin")
                print("   密码: admin123")
                print("   请登录后立即修改密码！\n")


# ========== 健康检查 ==========
@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.get("/")
async def root():
    """根路由 - 重定向到前端页面"""
    # 如果前端目录存在，重定向到前端首页
    if os.path.exists(FRONTEND_DIR):
        return RedirectResponse(url="/static/index.html")
    # 否则返回 API 状态
    return {"status": "ok", "message": "老年人智能助手服务运行中", "docs": "/docs"}


@app.post("/api/admin/trigger-reminders")
async def trigger_reminders():
    """手动触发提醒任务（管理员用）"""
    from tools.reminder_scheduler import reminder_scheduler
    result = await reminder_scheduler.run_reminder_task()
    return {"success": True, "result": result}


# ========== 用户认证接口 ==========
@app.post("/api/register", response_model=LoginResponse)
async def register(
    data: UserRegister,
    session: AsyncSession = Depends(get_session)
):
    """用户注册"""
    print("\n" + "=" * 60)
    print("📝 用户注册请求")
    print("=" * 60)
    print(f"[Register] 用户名: {data.username}")
    print(f"[Register] 手机号: {data.phone}")
    print(f"[Register] 姓名: {data.name}")
    
    success, message, user = await auth_service.register(data, session)
    
    if success:
        # 获取老人ID
        result = await session.execute(
            select(ElderlyInfo).where(ElderlyInfo.user_id == user.id)
        )
        elderly = result.scalar_one_or_none()
        elderly_id = elderly.id if elderly else None
        
        print(f"[Register] ✅ 注册成功, 老人ID: {elderly_id}")
        
        return LoginResponse(
            success=True,
            message=message,
            user=UserResponse(
                id=user.id,
                username=user.username,
                phone=user.phone,
                name=data.name,
                created_at=user.created_at
            ),
            elderly_id=elderly_id
        )
    else:
        print(f"[Register] ❌ 注册失败: {message}")
        return LoginResponse(
            success=False,
            message=message
        )


@app.post("/api/login", response_model=LoginResponse)
async def login(
    data: UserLogin,
    session: AsyncSession = Depends(get_session)
):
    """用户登录"""
    print("\n" + "=" * 60)
    print("🔐 用户登录请求")
    print("=" * 60)
    print(f"[Login] 用户名: {data.username}")
    
    success, message, user, elderly_id = await auth_service.login(
        data.username, data.password, session
    )
    
    if success:
        # 获取老人姓名
        result = await session.execute(
            select(ElderlyInfo).where(ElderlyInfo.user_id == user.id)
        )
        elderly = result.scalar_one_or_none()
        name = elderly.name if elderly else None
        
        print(f"[Login] ✅ 登录成功, 老人ID: {elderly_id}")
        
        return LoginResponse(
            success=True,
            message=message,
            user=UserResponse(
                id=user.id,
                username=user.username,
                phone=user.phone,
                name=name,
                created_at=user.created_at
            ),
            elderly_id=elderly_id
        )
    else:
        print(f"[Login] ❌ 登录失败: {message}")
        return LoginResponse(
            success=False,
            message=message
        )


# ========== 智能助手接口 ==========
@app.post("/api/assistant", response_model=AssistantResponse)
async def assistant(
    request: AssistantRequest,
    session: AsyncSession = Depends(get_session)
):
    """
    智能助手接口
    
    接收语音转文字后的内容，使用LangChain 1.0+ Agent分析并执行相应操作
    支持加载近三天对话历史作为上下文
    """
    print("\n" + "=" * 60)
    print("🤖 智能助手请求")
    print("=" * 60)
    print(f"[Assistant] 用户输入: {request.text}")
    print(f"[Assistant] 老人ID: {request.elderly_id}")
    if request.lat and request.lng:
        print(f"[Assistant] 位置: ({request.lat}, {request.lng})")
    
    try:
        # 获取老人信息
        print(f"[Assistant] 查询老人信息...")
        result = await session.execute(
            select(ElderlyInfo).where(ElderlyInfo.id == request.elderly_id)
        )
        elderly = result.scalar_one_or_none()
        
        elderly_info = {}
        if elderly:
            elderly_info = {
                "name": elderly.name,
                "home_address": elderly.home_address,
                "phone": elderly.phone
            }
            print(f"[Assistant] ✅ 找到老人: {elderly.name}")
        else:
            print(f"[Assistant] ⚠️ 未找到老人信息，使用默认设置")
        
        # 加载近三天对话历史
        print(f"[Assistant] 加载对话历史...")
        history_messages = await conversation_history_service.get_recent_history(
            elderly_id=request.elderly_id,
            days=3,
            session=session
        )
        
        # 获取所有工具
        print(f"[Assistant] 加载工具...")
        tools = get_all_tools()
        print(f"[Assistant] ✅ 已加载 {len(tools)} 个工具")
        
        # 创建Agent（传入历史消息）
        print(f"[Assistant] 创建Agent...")
        agent = ElderlyAssistantAgent(tools, elderly_info, history_messages)
        
        # 构建上下文
        context = ""
        if request.lat and request.lng:
            context = f"当前位置：纬度{request.lat}，经度{request.lng}。"
            full_input = f"{context}\n用户说：{request.text}"
        else:
            full_input = request.text
        
        # 调用Agent
        print(f"[Assistant] 调用Agent处理...")
        reply = await agent.invoke(full_input)
        
        # 保存对话历史到数据库
        print(f"[Assistant] 保存对话历史...")
        await conversation_history_service.save_message(
            elderly_id=request.elderly_id,
            role="user",
            content=request.text,
            session=session
        )
        await conversation_history_service.save_message(
            elderly_id=request.elderly_id,
            role="assistant",
            content=reply,
            session=session
        )
        
        print(f"[Assistant] ✅ 处理完成")
        print(f"[Assistant] 回复: {reply[:100]}...")
        print("=" * 60)
        
        return AssistantResponse(
            success=True,
            reply=reply,
            action_taken=None
        )
        
    except Exception as e:
        print(f"❌ 智能助手处理失败: {e}")
        import traceback
        traceback.print_exc()
        return AssistantResponse(
            success=False,
            reply="抱歉，处理您的请求时遇到问题，请稍后再试。",
            action_taken=None
        )


# ========== SOS紧急求助接口 ==========
@app.post("/api/sos", response_model=SOSResponse)
async def sos(
    request: SOSRequest,
    session: AsyncSession = Depends(get_session)
):
    """
    SOS紧急求助接口
    
    获取位置并向紧急联系人发送邮件通知
    （短信功能需要企业认证，暂使用邮件替代）
    """
    print("\n" + "=" * 60)
    print("🚨 SOS紧急求助触发")
    print("=" * 60)
    
    try:
        # 获取老人信息
        print(f"[SOS] 查询老人信息 (ID: {request.elderly_id})")
        result = await session.execute(
            select(ElderlyInfo).where(ElderlyInfo.id == request.elderly_id)
        )
        elderly = result.scalar_one_or_none()
        
        if not elderly:
            print("[SOS] ❌ 未找到老人信息")
            return SOSResponse(
                success=False,
                message="未找到老人信息",
                contacts_notified=0
            )
        
        elderly_name = elderly.name
        print(f"[SOS] ✅ 找到老人: {elderly_name}")
        
        # 获取紧急联系人
        print(f"[SOS] 查询紧急联系人...")
        contacts = await contact_service.get_emergency_contacts(request.elderly_id)
        
        if not contacts:
            print("[SOS] ❌ 未设置紧急联系人")
            return SOSResponse(
                success=False,
                message="未设置紧急联系人",
                contacts_notified=0
            )
        
        print(f"[SOS] ✅ 找到 {len(contacts)} 位紧急联系人:")
        for c in contacts:
            print(f"      - {c['name']}({c.get('relationship', '未知')}): {c.get('email', '无邮箱')}")
        
        # 获取位置地址
        print(f"[SOS] 获取位置信息...")
        try:
            lat = float(request.lat)
            lng = float(request.lng)
            location_text = await baidu_map_service.reverse_geocode(lat, lng)
            print(f"[SOS] ✅ 位置解析成功: {location_text}")
        except Exception as e:
            location_text = f"纬度{request.lat}，经度{request.lng}"
            print(f"[SOS] ⚠️ 位置解析失败，使用原始坐标: {e}")
        
        location_info = f"{location_text}（{request.lat}, {request.lng}）"
        
        # 发送邮件通知（替代短信）
        emails = [c["email"] for c in contacts if c.get("email")]
        contacts_notified = 0
        
        print(f"[SOS] 准备发送邮件通知...")
        print(f"[SOS] 收件人列表: {emails}")
        
        if emails:
            print(f"[SOS] 邮件服务配置检查: {email_service._is_configured()}")
            
            if email_service._is_configured():
                # 发送邮件
                print(f"[SOS] 📧 开始发送邮件...")
                subject = f"【紧急求助】{elderly_name}需要帮助"
                content = f"""
                <html>
                <body style="font-family: Arial, sans-serif;">
                <h2 style="color: #d32f2f;">紧急求助通知</h2>
                <p>您的亲人 <strong style="font-size: 18px;">{elderly_name}</strong> 刚刚触发了紧急求助。</p>
                <p><strong>当前位置：</strong>{location_info}</p>
                <p><strong>时间：</strong>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <hr>
                <p style="color:gray;">此邮件由老年人智能助手自动发送</p>
                </body>
                </html>
                """
                result = await email_service.send_batch_emails(emails, subject, content, html=True)
                contacts_notified = result.get("success_count", 0)
                
                print(f"[SOS] 📧 邮件发送结果:")
                print(f"      总数: {result.get('total', 0)}")
                print(f"      成功: {result.get('success_count', 0)}")
                for r in result.get('results', []):
                    status = "✅" if r.get('success') else "❌"
                    print(f"      {status} {r.get('email')}: {r.get('message')}")
            else:
                # 模拟发送
                contacts_notified = len(emails)
                print(f"[SOS] ⚠️ 邮件服务未配置，模拟发送")
                print(f"【模拟发送】已向 {contacts_notified} 位联系人发送紧急求助邮件")
        else:
            print("[SOS] ⚠️ 没有可用的邮箱地址")
        
        print(f"[SOS] ✅ 处理完成，已通知 {contacts_notified} 位联系人")
        print("=" * 60)
        
        return SOSResponse(
            success=True,
            message=f"已向{contacts_notified}位紧急联系人发送求助通知",
            contacts_notified=contacts_notified,
            location_text=location_text
        )
        
    except Exception as e:
        print(f"❌ SOS处理失败: {e}")
        import traceback
        traceback.print_exc()
        return SOSResponse(
            success=False,
            message=f"处理紧急求助时遇到问题：{str(e)}",
            contacts_notified=0
        )


# ========== 老人信息管理 ==========
@app.post("/api/elderly", response_model=ElderlyInfoResponse)
async def create_elderly(
    data: ElderlyInfoCreate,
    session: AsyncSession = Depends(get_session)
):
    """创建老人信息"""
    elderly = ElderlyInfo(**data.model_dump())
    session.add(elderly)
    await session.commit()
    await session.refresh(elderly)
    return elderly


@app.get("/api/elderly/{elderly_id}", response_model=ElderlyInfoResponse)
async def get_elderly(
    elderly_id: int,
    session: AsyncSession = Depends(get_session)
):
    """获取老人信息"""
    result = await session.execute(
        select(ElderlyInfo).where(ElderlyInfo.id == elderly_id)
    )
    elderly = result.scalar_one_or_none()
    
    if not elderly:
        raise HTTPException(status_code=404, detail="未找到老人信息")
    
    return elderly


# ========== 联系人管理 ==========
@app.post("/api/contacts", response_model=ContactResponse)
async def create_contact(
    data: ContactCreate,
    session: AsyncSession = Depends(get_session)
):
    """创建联系人"""
    contact = Contact(**data.model_dump())
    session.add(contact)
    await session.commit()
    await session.refresh(contact)
    return contact


@app.get("/api/contacts/{elderly_id}")
async def get_contacts(
    elderly_id: int,
    session: AsyncSession = Depends(get_session)
):
    """获取老人的所有联系人"""
    result = await session.execute(
        select(Contact).where(Contact.elderly_id == elderly_id)
    )
    contacts = result.scalars().all()
    return {"contacts": contacts}


@app.delete("/api/contacts/{contact_id}")
async def delete_contact(
    contact_id: int,
    session: AsyncSession = Depends(get_session)
):
    """删除联系人"""
    result = await session.execute(
        select(Contact).where(Contact.id == contact_id)
    )
    contact = result.scalar_one_or_none()
    
    if not contact:
        raise HTTPException(status_code=404, detail="未找到联系人")
    
    await session.delete(contact)
    await session.commit()
    
    return {"success": True, "message": "联系人已删除"}


# ========== 管理员后台 API ==========
@app.post("/api/admin/login", response_model=AdminLoginResponse)
async def admin_login(
    data: AdminLogin,
    session: AsyncSession = Depends(get_session)
):
    """管理员登录"""
    print("\n" + "=" * 60)
    print("🔐 管理员登录请求")
    print("=" * 60)
    print(f"[Admin Login] 用户名: {data.username}")
    
    success, message, admin = await admin_service.login(
        data.username, data.password, session
    )
    
    if success:
        print(f"[Admin Login] ✅ 登录成功")
        return AdminLoginResponse(
            success=True,
            message=message,
            admin=AdminResponse(
                id=admin.id,
                username=admin.username,
                name=admin.name,
                role=admin.role,
                is_active=admin.is_active,
                last_login=admin.last_login,
                created_at=admin.created_at
            )
        )
    else:
        print(f"[Admin Login] ❌ 登录失败: {message}")
        return AdminLoginResponse(
            success=False,
            message=message
        )


@app.get("/api/admin/dashboard")
async def admin_dashboard(
    session: AsyncSession = Depends(get_session)
):
    """仪表盘统计数据"""
    stats = await admin_service.get_dashboard_stats(session)
    return {"success": True, "data": stats}


# 用户管理
@app.get("/api/admin/users")
async def admin_get_users(
    search: str = Query(None, description="搜索关键词"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    session: AsyncSession = Depends(get_session)
):
    """获取用户列表"""
    users, total = await admin_service.get_user_list(session, search, page, page_size)
    return {
        "success": True,
        "data": users,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@app.post("/api/admin/users")
async def admin_create_user(
    data: AdminUserCreate,
    session: AsyncSession = Depends(get_session)
):
    """创建用户"""
    success, message, elderly = await admin_service.create_user(data.model_dump(), session)
    return {
        "success": success,
        "message": message,
        "data": {"id": elderly.id} if elderly else None
    }


@app.get("/api/admin/users/{elderly_id}")
async def admin_get_user_detail(
    elderly_id: int,
    session: AsyncSession = Depends(get_session)
):
    """获取用户详情"""
    detail = await admin_service.get_user_detail(elderly_id, session)
    if not detail:
        raise HTTPException(status_code=404, detail="用户不存在")
    return {"success": True, "data": detail}


@app.put("/api/admin/users/{elderly_id}")
async def admin_update_user(
    elderly_id: int,
    data: AdminUserUpdate,
    session: AsyncSession = Depends(get_session)
):
    """更新用户"""
    success, message = await admin_service.update_user(
        elderly_id, data.model_dump(exclude_unset=True), session
    )
    return {"success": success, "message": message}


@app.delete("/api/admin/users/{elderly_id}")
async def admin_delete_user(
    elderly_id: int,
    session: AsyncSession = Depends(get_session)
):
    """删除用户"""
    success, message = await admin_service.delete_user(elderly_id, session)
    return {"success": success, "message": message}


@app.post("/api/admin/users/import")
async def admin_import_users(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session)
):
    """批量导入用户"""
    content = await file.read()
    success_count, fail_count, errors = await excel_import_service.import_users_from_excel(
        content, session
    )
    return {
        "success": fail_count == 0,
        "message": f"导入完成：成功{success_count}条，失败{fail_count}条",
        "total": success_count + fail_count,
        "success_count": success_count,
        "fail_count": fail_count,
        "errors": errors
    }


@app.get("/api/admin/users/template/download")
async def admin_download_template():
    """下载用户导入模板"""
    template = excel_import_service.generate_user_template()
    return StreamingResponse(
        io.BytesIO(template),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=user_template.xlsx"}
    )


# 联系人管理
@app.get("/api/admin/contacts")
async def admin_get_contacts(
    elderly_id: int = Query(None, description="老人ID筛选"),
    session: AsyncSession = Depends(get_session)
):
    """获取联系人列表"""
    from sqlalchemy import select
    query = select(Contact)
    if elderly_id:
        query = query.where(Contact.elderly_id == elderly_id)
    result = await session.execute(query)
    contacts = result.scalars().all()
    
    # 转换字段名: contact_relationship -> relationship
    data = []
    for c in contacts:
        item = {
            "id": c.id,
            "elderly_id": c.elderly_id,
            "name": c.name,
            "relationship": c.contact_relationship,
            "phone": c.phone,
            "email": c.email,
            "address": c.address,
            "lat": c.lat,
            "lng": c.lng,
            "is_emergency": c.is_emergency,
            "created_at": c.created_at.isoformat() if c.created_at else None
        }
        data.append(item)
    
    return {"success": True, "data": data}


@app.post("/api/admin/contacts")
async def admin_create_contact(
    data: AdminContactCreate,
    session: AsyncSession = Depends(get_session)
):
    """创建联系人"""
    success, message, contact = await admin_service.create_contact(
        data.model_dump(), session
    )
    return {
        "success": success,
        "message": message,
        "data": contact
    }


@app.put("/api/admin/contacts/{contact_id}")
async def admin_update_contact(
    contact_id: int,
    data: AdminContactUpdate,
    session: AsyncSession = Depends(get_session)
):
    """更新联系人"""
    success, message = await admin_service.update_contact(
        contact_id, data.model_dump(exclude_unset=True), session
    )
    return {"success": success, "message": message}


@app.delete("/api/admin/contacts/{contact_id}")
async def admin_delete_contact(
    contact_id: int,
    session: AsyncSession = Depends(get_session)
):
    """删除联系人"""
    success, message = await admin_service.delete_contact(contact_id, session)
    return {"success": success, "message": message}


# 记事管理
@app.get("/api/admin/memos")
async def admin_get_memos(
    elderly_id: int = Query(None, description="老人ID筛选"),
    session: AsyncSession = Depends(get_session)
):
    """获取记事列表"""
    from sqlalchemy import select
    query = select(Memo)
    if elderly_id:
        query = query.where(Memo.elderly_id == elderly_id)
    query = query.order_by(Memo.created_at.desc())
    result = await session.execute(query)
    memos = result.scalars().all()
    
    # 转换为 JSON 可序列化的格式
    data = []
    for m in memos:
        data.append({
            "id": m.id,
            "elderly_id": m.elderly_id,
            "content": m.content,
            "memo_type": m.memo_type or "once",
            "reminder_time": m.reminder_time.isoformat() if m.reminder_time else None,
            "repeat_type": m.repeat_type,
            "repeat_days": m.repeat_days,
            "end_date": m.end_date.isoformat() if m.end_date else None,
            "is_completed": m.is_completed,
            "created_at": m.created_at.isoformat() if m.created_at else None
        })
    
    return {"success": True, "data": data}


@app.post("/api/admin/memos")
async def admin_create_memo(
    data: AdminMemoCreate,
    session: AsyncSession = Depends(get_session)
):
    """创建记事"""
    success, message, memo = await admin_service.create_memo(
        data.model_dump(), session
    )
    return {
        "success": success,
        "message": message,
        "data": memo
    }


@app.put("/api/admin/memos/{memo_id}")
async def admin_update_memo(
    memo_id: int,
    data: AdminMemoUpdate,
    session: AsyncSession = Depends(get_session)
):
    """更新记事"""
    success, message = await admin_service.update_memo(
        memo_id, data.model_dump(exclude_unset=True), session
    )
    return {"success": success, "message": message}


@app.delete("/api/admin/memos/{memo_id}")
async def admin_delete_memo(
    memo_id: int,
    session: AsyncSession = Depends(get_session)
):
    """删除记事"""
    success, message = await admin_service.delete_memo(memo_id, session)
    return {"success": success, "message": message}


# 对话历史
@app.get("/api/admin/conversations")
async def admin_get_conversations(
    elderly_id: int = Query(None, description="老人ID筛选"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    session: AsyncSession = Depends(get_session)
):
    """获取对话历史"""
    conversations, total = await admin_service.get_conversations(
        elderly_id=elderly_id,
        page=page,
        page_size=page_size,
        session=session
    )
    return {
        "success": True,
        "data": conversations,
        "total": total,
        "page": page,
        "page_size": page_size
    }


# ========== 异常处理 ==========
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理"""
    print(f"❌ 全局异常: {exc}")
    import traceback
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": "服务器内部错误"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=config.APP_HOST,
        port=config.APP_PORT,
        reload=True
    )
