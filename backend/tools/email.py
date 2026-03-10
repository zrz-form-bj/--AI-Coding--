"""
邮件发送工具
"""
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
from langchain.tools import tool
from config import config


class EmailService:
    """邮件服务"""
    
    def __init__(self):
        self.smtp_host = config.SMTP_HOST
        self.smtp_port = config.SMTP_PORT
        self.smtp_user = config.SMTP_USER
        self.smtp_password = config.SMTP_PASSWORD
    
    def _is_configured(self) -> bool:
        """检查是否已配置"""
        return all([self.smtp_host, self.smtp_user, self.smtp_password])
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        content: str,
        html: bool = False
    ) -> dict:
        """
        发送邮件
        
        参数:
            to_email: 收件人邮箱
            subject: 邮件主题
            content: 邮件内容
            html: 是否为HTML格式
        
        返回:
            发送结果
        """
        if not self._is_configured():
            return {
                "success": False,
                "message": "邮件服务未配置，请先在.env文件中配置SMTP相关信息"
            }
        
        try:
            # 创建邮件
            message = MIMEMultipart()
            message["From"] = self.smtp_user
            message["To"] = to_email
            message["Subject"] = subject
            
            # 添加正文
            content_type = "html" if html else "plain"
            message.attach(MIMEText(content, content_type, "utf-8"))
            
            # 发送邮件
            await aiosmtplib.send(
                message,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_user,
                password=self.smtp_password,
                use_tls=True
            )
            
            return {
                "success": True,
                "message": "邮件发送成功"
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"邮件发送失败：{str(e)}"
            }
    
    async def send_batch_emails(
        self,
        to_emails: List[str],
        subject: str,
        content: str,
        html: bool = False
    ) -> dict:
        """
        批量发送邮件
        
        参数:
            to_emails: 收件人邮箱列表
            subject: 邮件主题
            content: 邮件内容
        
        返回:
            发送结果
        """
        results = []
        for email in to_emails:
            result = await self.send_email(email, subject, content, html)
            results.append({
                "email": email,
                **result
            })
        
        success_count = sum(1 for r in results if r.get("success"))
        
        return {
            "success": success_count > 0,
            "total": len(to_emails),
            "success_count": success_count,
            "results": results
        }


# 创建服务实例
email_service = EmailService()


# ========== LangChain Tools ==========

@tool
async def send_email(
    to_email: str,
    subject: str,
    content: str
) -> str:
    """
    发送邮件工具。
    向指定邮箱发送邮件。
    
    参数:
        to_email: 收件人邮箱
        subject: 邮件主题
        content: 邮件内容
    
    返回:
        发送结果
    """
    result = await email_service.send_email(to_email, subject, content)
    
    if result["success"]:
        return f"邮件已成功发送到 {to_email}"
    else:
        return f"邮件发送失败：{result['message']}"


@tool
async def send_sos_email(
    emails: str,
    elderly_name: str,
    location: str
) -> str:
    """
    SOS紧急邮件发送工具。
    向多个联系人发送包含老人位置信息的紧急邮件。
    
    参数:
        emails: 邮箱列表，用逗号分隔
        elderly_name: 老人姓名
        location: 位置信息
    
    返回:
        发送结果
    """
    email_list = [e.strip() for e in emails.split(",") if e.strip()]
    
    if not email_list:
        return "没有提供有效的邮箱地址"
    
    subject = f"【紧急求助】{elderly_name}需要帮助"
    content = f"""
    <html>
    <body>
    <h2>紧急求助通知</h2>
    <p>您的亲人 <strong>{elderly_name}</strong> 刚刚触发了紧急求助。</p>
    <p><strong>当前位置：</strong>{location}</p>
    <p>请尽快联系确认情况！</p>
    <hr>
    <p style="color:gray;">此邮件由老年人智能助手自动发送</p>
    </body>
    </html>
    """
    
    # 模拟发送结果
    if not email_service._is_configured():
        return f"【模拟发送】已向 {len(email_list)} 位联系人发送紧急求助邮件。请配置SMTP服务以启用真实发送。"
    
    result = await email_service.send_batch_emails(email_list, subject, content, html=True)
    
    if result["success"]:
        return f"已成功向 {result['success_count']}/{result['total']} 位联系人发送紧急求助邮件"
    else:
        return "邮件发送失败，请检查邮件服务配置"
