"""
工具模块 - LangChain 1.0+
工具使用 @tool 装饰器定义，自动转换为 StructuredTool
"""
from tools.baidu_map import (
    baidu_map_navigation,
    baidu_map_search_place,
    baidu_map_get_address
)
from tools.weather import query_weather, query_weather_forecast
from tools.sms import send_sms, send_sos_sms
from tools.email import send_email, send_sos_email
from tools.contact import (
    query_contact_phone,
    query_contact_address,
    list_all_contacts,
    query_home_address,
    make_call
)
from tools.emergency import (
    query_emergency_shelter,
    query_nearby_hospital,
    query_nearby_pharmacy,
    query_emergency_numbers,
    query_health_tips,
    query_medical_help
)
from tools.memo import add_memo, list_memos, query_time


def get_all_tools() -> list:
    """
    获取所有工具
    
    LangChain 1.0+ 中，使用 @tool 装饰器的函数
    会自动转换为 BaseTool 实例
    """
    tools = [
        # 百度地图
        baidu_map_navigation,
        baidu_map_search_place,
        baidu_map_get_address,
        
        # 天气
        query_weather,
        query_weather_forecast,
        
        # 通讯（短信功能需要企业认证，已保留代码但暂不使用）
        # send_sms,
        # send_sos_sms,
        send_email,
        send_sos_email,
        
        # 联系人
        query_contact_phone,
        query_contact_address,
        list_all_contacts,
        query_home_address,
        make_call,
        
        # 紧急信息
        query_emergency_shelter,
        query_nearby_hospital,
        query_nearby_pharmacy,
        query_emergency_numbers,
        query_health_tips,
        query_medical_help,
        
        # 记事
        add_memo,
        list_memos,
        query_time,
    ]
    
    return tools


__all__ = [
    # 百度地图
    "baidu_map_navigation",
    "baidu_map_search_place", 
    "baidu_map_get_address",
    
    # 天气
    "query_weather",
    "query_weather_forecast",
    
    # 短信（已注释，需要企业认证）
    "send_sms",
    "send_sos_sms",
    
    # 邮件
    "send_email",
    "send_sos_email",
    
    # 联系人
    "query_contact_phone",
    "query_contact_address",
    "list_all_contacts",
    "query_home_address",
    "make_call",
    
    # 紧急信息
    "query_emergency_shelter",
    "query_nearby_hospital",
    "query_nearby_pharmacy",
    "query_emergency_numbers",
    "query_health_tips",
    "query_medical_help",
    
    # 记事
    "add_memo",
    "list_memos",
    "query_time",
    
    # 工具获取
    "get_all_tools"
]
