"""
天气查询工具
使用和风天气API (支持免费版和企业版)
"""
import httpx
from typing import Optional
from langchain.tools import tool
from config import config


class WeatherService:
    """天气服务"""
    
    def __init__(self):
        self.api_key = config.QWEATHER_API_KEY
        # 判断是否为企业版（有自定义API Host）
        self.api_host = getattr(config, 'QWEATHER_API_HOST', '')
        self.is_enterprise = bool(self.api_host)
        
        if self.is_enterprise:
            # 企业版使用自定义域名
            self.geo_url = f"https://{self.api_host}/geo/v2/city/lookup"
            self.weather_url = f"https://{self.api_host}/v7/weather/now"
            self.forecast_url = f"https://{self.api_host}/v7/weather/3d"
        else:
            # 免费版使用官方域名
            self.geo_url = "https://geoapi.qweather.com/v2/city/lookup"
            self.weather_url = "https://devapi.qweather.com/v7/weather/now"
            self.forecast_url = "https://devapi.qweather.com/v7/weather/3d"
    
    def _get_headers(self) -> dict:
        """获取请求头"""
        # 企业版可以使用 Bearer Token，但某些配置下可能不需要
        # 暂时不使用 headers 认证，改用 URL 参数
        return {}
    
    def _get_params(self, extra_params: dict) -> dict:
        """获取请求参数"""
        params = extra_params.copy()
        # 所有版本都在 URL 参数中传递 key
        params["key"] = self.api_key
        return params
    
    async def _request(self, url: str, params: dict) -> dict:
        """发送请求"""
        headers = self._get_headers()
        params = self._get_params(params)
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, params=params, headers=headers, timeout=10)
                # 检查响应状态
                if response.status_code != 200:
                    print(f"[天气API错误] HTTP {response.status_code}: {response.text[:200]}")
                    return {"code": str(response.status_code), "error": f"HTTP {response.status_code}"}
                # 检查内容是否为空
                if not response.text:
                    print("[天气API错误] 返回空内容")
                    return {"code": "-1", "error": "空响应"}
                try:
                    data = response.json()
                    # 检查和风天气的错误码
                    if data.get("code") == "401" or (data.get("error") and data["error"].get("status") == 401):
                        print("[天气API错误] API Key无效或未授权")
                        return {"code": "401", "error": "API Key无效或未授权"}
                    if data.get("code") == "402":
                        print("[天气API错误] 额度已用完")
                        return {"code": "402", "error": "额度已用完"}
                    return data
                except Exception as e:
                    print(f"[天气API错误] JSON解析失败: {e}, 响应内容: {response.text[:200]}")
                    return {"code": "-2", "error": f"解析失败: {e}"}
            except Exception as e:
                print(f"[天气API错误] 请求异常: {e}")
                return {"code": "-3", "error": f"请求失败: {e}"}
    
    async def get_weather(self, location: str) -> Optional[dict]:
        """
        获取天气信息
        
        参数:
            location: 城市名称或经纬度(格式: 经度,纬度)
        """
        if not self.api_key:
            print("[天气] 未配置API Key，使用模拟数据")
            return None
        
        # 先获取城市ID
        geo_result = await self._request(self.geo_url, {"location": location})
        
        if geo_result.get("code") != "200":
            print(f"[天气] 城市查询失败: {geo_result.get('error', '未知错误')}")
            return None
        
        # 企业版和免费版返回格式略有不同
        locations = geo_result.get("location", []) or geo_result.get("geo", [])
        if not locations:
            print("[天气] 未找到该城市")
            return None
        
        location_id = locations[0].get("id") or locations[0].get("locationId")
        location_name = locations[0].get("name")
        
        if not location_id:
            print("[天气] 无法获取城市ID")
            return None
        
        # 获取实时天气
        weather_result = await self._request(self.weather_url, {"location": location_id})
        
        if weather_result.get("code") != "200":
            print(f"[天气] 天气查询失败: {weather_result.get('error', '未知错误')}")
            return None
        
        now = weather_result.get("now", {})
        
        return {
            "location": location_name,
            "temp": now.get("temp"),
            "feelsLike": now.get("feelsLike"),
            "text": now.get("text"),
            "windDir": now.get("windDir"),
            "windScale": now.get("windScale"),
            "humidity": now.get("humidity"),
            "vis": now.get("vis")
        }
    
    async def get_3d_weather(self, location: str) -> Optional[dict]:
        """获取3天天气预报"""
        if not self.api_key:
            return None
        
        # 先获取城市ID
        geo_result = await self._request(self.geo_url, {"location": location})
        
        if geo_result.get("code") != "200":
            return None
        
        locations = geo_result.get("location", []) or geo_result.get("geo", [])
        if not locations:
            return None
        
        location_id = locations[0].get("id") or locations[0].get("locationId")
        location_name = locations[0].get("name")
        
        if not location_id:
            return None
        
        # 获取3天预报
        weather_result = await self._request(self.forecast_url, {"location": location_id})
        
        if weather_result.get("code") != "200":
            return None
        
        return {
            "location": location_name,
            "daily": weather_result.get("daily", [])
        }


# 创建服务实例
weather_service = WeatherService()


# ========== 模拟天气数据（当API不可用时使用） ==========
MOCK_WEATHER = {
    "北京": {
        "temp": "22",
        "text": "晴",
        "humidity": "45",
        "windDir": "北风",
        "windScale": "3级"
    },
    "上海": {
        "temp": "26",
        "text": "多云",
        "humidity": "65",
        "windDir": "东风",
        "windScale": "2级"
    },
    "广州": {
        "temp": "30",
        "text": "阴",
        "humidity": "75",
        "windDir": "南风",
        "windScale": "2级"
    }
}


@tool
async def query_weather(location: str = "北京") -> str:
    """
    天气查询工具。
    查询指定城市的天气情况。
    
    参数:
        location: 城市名称，如"北京"、"上海"、"广州"
    
    返回:
        天气信息
    """
    # 尝试使用API
    weather = await weather_service.get_weather(location)
    
    if weather:
        result = f"「{weather['location']}」当前天气：\n"
        result += f"天气：{weather['text']}\n"
        result += f"气温：{weather['temp']}℃\n"
        result += f"体感温度：{weather['feelsLike']}℃\n"
        result += f"风向：{weather['windDir']} {weather['windScale']}级\n"
        result += f"湿度：{weather['humidity']}%"
        return result
    
    # 如果API不可用，使用模拟数据
    if location in MOCK_WEATHER:
        mock = MOCK_WEATHER[location]
        result = f"「{location}」当前天气（模拟数据）：\n"
        result += f"天气：{mock['text']}\n"
        result += f"气温：{mock['temp']}℃\n"
        result += f"风向：{mock['windDir']} {mock['windScale']}\n"
        result += f"湿度：{mock['humidity']}%"
        return result
    
    return f"抱歉，暂时无法获取「{location}」的天气信息。请稍后再试。"


@tool
async def query_weather_forecast(location: str = "北京") -> str:
    """
    天气预报工具。
    查询未来3天的天气预报。
    
    参数:
        location: 城市名称
    
    返回:
        3天天气预报信息
    """
    forecast = await weather_service.get_3d_weather(location)
    
    if forecast:
        result = f"「{forecast['location']}」未来3天天气预报：\n"
        for day in forecast.get("daily", []):
            date = day.get("fxDate", "")
            text_day = day.get("textDay", "")
            text_night = day.get("textNight", "")
            temp_max = day.get("tempMax", "")
            temp_min = day.get("tempMin", "")
            result += f"{date}：{text_day}转{text_night}，{temp_min}℃~{temp_max}℃\n"
        return result
    
    return f"抱歉，暂时无法获取「{location}」的天气预报。"
