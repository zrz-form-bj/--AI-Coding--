"""
紧急信息工具
硬编码的紧急避难所、医院等信息
"""
from typing import List
from langchain.tools import tool


# ========== 硬编码的紧急信息 ==========

EMERGENCY_SHELTERS = [
    {
        "name": "社区应急避难所",
        "address": "幸福路88号社区服务中心",
        "phone": "010-12345678",
        "capacity": "可容纳500人"
    },
    {
        "name": "区级应急避难中心",
        "address": "光明大道128号",
        "phone": "010-87654321",
        "capacity": "可容纳2000人"
    }
]

NEARBY_HOSPITALS = [
    {
        "name": "市第一人民医院",
        "address": "健康路1号",
        "phone": "120",
        "distance": "约2公里",
        "emergency": True,
        "departments": ["急诊科", "心内科", "神经内科", "骨科"]
    },
    {
        "name": "社区医院",
        "address": "幸福路56号",
        "phone": "010-11111111",
        "distance": "约500米",
        "emergency": False,
        "departments": ["全科", "中医科", "理疗科"]
    }
]

PHARMACIES = [
    {
        "name": "老百姓大药房",
        "address": "幸福路32号",
        "phone": "010-22222222",
        "distance": "约300米",
        "24h": True
    },
    {
        "name": "同仁堂药店",
        "address": "光明大道45号",
        "phone": "010-33333333",
        "distance": "约800米",
        "24h": False
    }
]

EMERGENCY_NUMBERS = {
    "报警": "110",
    "急救": "120",
    "火警": "119",
    "交通事故": "122"
}

HEALTH_TIPS = {
    "高血压": "1.按时服药，定期测量血压；2.低盐低脂饮食；3.适量运动；4.保持心情舒畅",
    "糖尿病": "1.控制饮食，少食多餐；2.定期监测血糖；3.适量运动；4.按时服药或注射胰岛素",
    "心脏病": "1.避免剧烈运动；2.保持情绪稳定；3.随身携带急救药物；4.定期复查",
    "关节炎": "1.注意关节保暖；2.适度活动，避免过度劳累；3.可进行热敷理疗"
}


# ========== LangChain Tools ==========

@tool
async def query_emergency_shelter() -> str:
    """
    查询紧急避难所工具。
    查询附近的紧急避难所信息。
    
    返回:
        紧急避难所列表
    """
    result = "以下是附近的紧急避难所：\n\n"
    for i, shelter in enumerate(EMERGENCY_SHELTERS, 1):
        result += f"{i}. {shelter['name']}\n"
        result += f"   地址：{shelter['address']}\n"
        result += f"   电话：{shelter['phone']}\n"
        result += f"   容量：{shelter['capacity']}\n\n"
    return result


@tool
async def query_nearby_hospital() -> str:
    """
    查询附近医院工具。
    查询附近的医院信息。
    
    返回:
        附近医院列表
    """
    result = "以下是附近的医院：\n\n"
    for i, hospital in enumerate(NEARBY_HOSPITALS, 1):
        result += f"{i}. {hospital['name']}"
        if hospital['emergency']:
            result += "（有急诊）"
        result += "\n"
        result += f"   地址：{hospital['address']}\n"
        result += f"   电话：{hospital['phone']}\n"
        result += f"   距离：{hospital['distance']}\n"
        result += f"   科室：{', '.join(hospital['departments'])}\n\n"
    return result


@tool
async def query_nearby_pharmacy() -> str:
    """
    查询附近药店工具。
    查询附近的药店信息。
    
    返回:
        附近药店列表
    """
    result = "以下是附近的药店：\n\n"
    for i, pharmacy in enumerate(PHARMACIES, 1):
        result += f"{i}. {pharmacy['name']}"
        if pharmacy['24h']:
            result += "（24小时营业）"
        result += "\n"
        result += f"   地址：{pharmacy['address']}\n"
        result += f"   电话：{pharmacy['phone']}\n"
        result += f"   距离：{pharmacy['distance']}\n\n"
    return result


@tool
async def query_emergency_numbers() -> str:
    """
    查询紧急电话工具。
    查询常用紧急电话号码。
    
    返回:
        紧急电话列表
    """
    result = "以下是常用紧急电话：\n\n"
    for name, number in EMERGENCY_NUMBERS.items():
        result += f"• {name}：{number}\n"
    return result


@tool
async def query_health_tips(disease: str = "") -> str:
    """
    健康提醒工具。
    查询常见疾病的健康提醒。
    
    参数:
        disease: 疾病名称，如"高血压"、"糖尿病"（可选）
    
    返回:
        健康提醒信息
    """
    if disease:
        if disease in HEALTH_TIPS:
            return f"【{disease}健康提醒】\n{HEALTH_TIPS[disease]}"
        else:
            return f"暂时没有「{disease}」的具体健康提醒，请咨询医生获取专业建议。"
    
    result = "以下是常见疾病的健康提醒：\n\n"
    for name, tips in HEALTH_TIPS.items():
        result += f"【{name}】\n{tips}\n\n"
    return result


@tool
async def query_medical_help() -> str:
    """
    医护救援工具。
    获取医护救援相关信息。
    
    返回:
        医护救援指南
    """
    result = "【医护救援指南】\n\n"
    result += "紧急情况处理：\n"
    result += "1. 立即拨打急救电话：120\n"
    result += "2. 保持冷静，说明具体情况和位置\n"
    result += "3. 如有慢性病，告知医生正在服用的药物\n\n"
    result += "就近医院：\n"
    result += f"• {NEARBY_HOSPITALS[0]['name']}\n"
    result += f"  地址：{NEARBY_HOSPITALS[0]['address']}\n"
    result += f"  电话：{NEARBY_HOSPITALS[0]['phone']}\n"
    return result
