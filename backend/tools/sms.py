"""
短信发送工具
使用阿里云短信服务
"""
import json
from typing import List, Optional
from langchain.tools import tool
from config import config


class SMSService:
    """短信服务"""
    
    def __init__(self):
        self.access_key_id = config.ALIYUN_ACCESS_KEY_ID
        self.access_key_secret = config.ALIYUN_ACCESS_KEY_SECRET
        self.sign_name = config.ALIYUN_SMS_SIGN_NAME
        self.template_code = config.ALIYUN_SMS_TEMPLATE_CODE
    
    def _is_configured(self) -> bool:
        """检查是否已配置"""
        return all([
            self.access_key_id,
            self.access_key_secret,
            self.sign_name,
            self.template_code
        ])
    
    async def send_sms(
        self,
        phone: str,
        template_param: dict
    ) -> dict:
        """
        发送短信
        
        参数:
            phone: 手机号
            template_param: 模板参数
        
        返回:
            发送结果
        """
        if not self._is_configured():
            return {
                "success": False,
                "message": "短信服务未配置，请先在.env文件中配置阿里云短信相关信息"
            }
        
        try:
            from alibabacloud_dysmsapi20170525.client import Client
            from alibabacloud_dysmsapi20170525 import models as sms_models
            from alibabacloud_tea_openapi import models as open_api_models
            
            # 创建客户端
            config_open = open_api_models.Config(
                access_key_id=self.access_key_id,
                access_key_secret=self.access_key_secret
            )
            config_open.endpoint = "dysmsapi.aliyuncs.com"
            client = Client(config_open)
            
            # 构建请求
            request = sms_models.SendSmsRequest(
                phone_numbers=phone,
                sign_name=self.sign_name,
                template_code=self.template_code,
                template_param=json.dumps(template_param)
            )
            
            # 发送短信
            response = client.send_sms(request)
            
            if response.body.code == "OK":
                return {
                    "success": True,
                    "message": "短信发送成功",
                    "biz_id": response.body.biz_id
                }
            else:
                return {
                    "success": False,
                    "message": f"短信发送失败：{response.body.message}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "message": f"短信发送异常：{str(e)}"
            }
    
    async def send_batch_sms(
        self,
        phones: List[str],
        template_param: dict
    ) -> dict:
        """
        批量发送短信
        
        参数:
            phones: 手机号列表
            template_param: 模板参数
        
        返回:
            发送结果
        """
        results = []
        for phone in phones:
            result = await self.send_sms(phone, template_param)
            results.append({
                "phone": phone,
                **result
            })
        
        success_count = sum(1 for r in results if r.get("success"))
        
        return {
            "success": success_count > 0,
            "total": len(phones),
            "success_count": success_count,
            "results": results
        }


# 创建服务实例
sms_service = SMSService()


# ========== LangChain Tools ==========

@tool
async def send_sms(
    phone: str,
    message: str
) -> str:
    """
    发送短信工具。
    向指定手机号发送短信。
    
    参数:
        phone: 手机号
        message: 短信内容
    
    返回:
        发送结果
    """
    result = await sms_service.send_sms(phone, {"message": message})
    
    if result["success"]:
        return f"短信已成功发送到 {phone}"
    else:
        return f"短信发送失败：{result['message']}"


@tool
async def send_sos_sms(
    phones: str,
    elderly_name: str,
    location: str
) -> str:
    """
    SOS紧急短信发送工具。
    向多个紧急联系人发送包含老人位置信息的短信。
    
    参数:
        phones: 手机号列表，用逗号分隔
        elderly_name: 老人姓名
        location: 位置信息
    
    返回:
        发送结果
    """
    phone_list = [p.strip() for p in phones.split(",") if p.strip()]
    
    if not phone_list:
        return "没有提供有效的手机号"
    
    # 模拟发送结果（实际配置阿里云后才会真实发送）
    if not sms_service._is_configured():
        # 模拟模式
        return f"【模拟发送】已向 {len(phone_list)} 位联系人发送紧急求助短信：{elderly_name}在{location}需要帮助。请配置阿里云短信服务以启用真实发送。"
    
    result = await sms_service.send_batch_sms(
        phone_list,
        {
            "name": elderly_name,
            "location": location
        }
    )
    
    if result["success"]:
        return f"已成功向 {result['success_count']}/{result['total']} 位联系人发送紧急求助短信"
    else:
        return "短信发送失败，请检查短信服务配置"
