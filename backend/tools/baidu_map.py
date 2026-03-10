"""
百度地图工具
功能：路线规划、地点搜索、地理编码
"""
import httpx
from typing import Optional, Dict, Any
from langchain.tools import tool
from config import config


class BaiduMapService:
    """百度地图服务"""
    
    def __init__(self):
        self.ak = config.BAIDU_MAP_AK
        self.base_url = "https://api.map.baidu.com"
    
    async def _request(self, url: str, params: dict) -> dict:
        """发送请求"""
        params["ak"] = self.ak
        params["output"] = "json"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=10)
            return response.json()
    
    async def geocode(self, address: str, city: str = "") -> Optional[Dict]:
        """地址转经纬度（地理编码）"""
        url = f"{self.base_url}/geocoding/v3/"
        params = {"address": address}
        if city:
            params["city"] = city
        
        result = await self._request(url, params)
        if result.get("status") == 0:
            location = result.get("result", {}).get("location", {})
            return {
                "lat": location.get("lat"),
                "lng": location.get("lng"),
                "precise": result.get("result", {}).get("precise", 0),
                "confidence": result.get("result", {}).get("confidence", 0)
            }
        return None
    
    async def reverse_geocode(self, lat: float, lng: float) -> Optional[str]:
        """经纬度转地址（逆地理编码）"""
        url = f"{self.base_url}/reverse_geocoding/v3/"
        params = {
            "location": f"{lat},{lng}",
            "extensions_poi": 1
        }
        
        result = await self._request(url, params)
        if result.get("status") == 0:
            return result.get("result", {}).get("formatted_address", "")
        return None
    
    async def direction(
        self,
        origin_lat: float,
        origin_lng: float,
        dest_lat: float,
        dest_lng: float,
        mode: str = "transit"  # driving, walking, transit, riding
    ) -> Optional[Dict]:
        """路线规划"""
        url_map = {
            "driving": f"{self.base_url}/direction/v2/driving",
            "walking": f"{self.base_url}/direction/v2/walking",
            "transit": f"{self.base_url}/direction/v2/transit",
            "riding": f"{self.base_url}/direction/v2/riding"
        }
        
        url = url_map.get(mode, url_map["transit"])
        params = {
            "origin": f"{origin_lat},{origin_lng}",
            "destination": f"{dest_lat},{dest_lng}"
        }
        
        result = await self._request(url, params)
        if result.get("status") == 0:
            return result.get("result", {})
        return None
    
    async def search_place(self, query: str, location: str = "", city: str = "") -> Optional[list]:
        """地点搜索（POI）"""
        url = f"{self.base_url}/place/v2/search"
        params = {"query": query}
        if location:
            params["location"] = location
        if city:
            params["city"] = city
        
        result = await self._request(url, params)
        if result.get("status") == 0:
            return result.get("results", [])
        return []


# 创建服务实例
baidu_map_service = BaiduMapService()


# ========== LangChain Tools ==========

@tool
async def baidu_map_navigation(
    destination: str,
    origin_lat: float = None,
    origin_lng: float = None,
    mode: str = "transit"
) -> str:
    """
    百度地图路线规划工具。
    用于查询从一个地点到另一个地点的路线。
    
    参数:
        destination: 目的地名称或地址
        origin_lat: 起点纬度（可选，不提供则使用当前位置）
        origin_lng: 起点经度（可选，不提供则使用当前位置）
        mode: 出行方式，可选：driving(驾车)、walking(步行)、transit(公交地铁)、riding(骑行)
    
    返回:
        路线规划的详细信息
    """
    # 先获取目的地的经纬度
    dest_location = await baidu_map_service.geocode(destination)
    if not dest_location:
        return f"抱歉，没有找到目的地「{destination}」的位置信息。"
    
    dest_lat = dest_location["lat"]
    dest_lng = dest_location["lng"]
    
    # 如果没有提供起点，返回目的地信息和提示
    if origin_lat is None or origin_lng is None:
        return f"找到目的地「{destination}」，位置：纬度{dest_lat}，经度{dest_lng}。如需导航，请允许获取您的当前位置。"
    
    # 规划路线
    route_result = await baidu_map_service.direction(
        origin_lat, origin_lng, dest_lat, dest_lng, mode
    )
    
    if not route_result:
        return f"抱歉，无法规划到「{destination}」的路线。"
    
    # 解析路线结果
    routes = route_result.get("routes", [])
    if not routes:
        return f"抱歉，没有找到到「{destination}」的路线。"
    
    route = routes[0]
    
    # 构建返回信息
    mode_names = {
        "driving": "驾车",
        "walking": "步行",
        "transit": "公交地铁",
        "riding": "骑行"
    }
    
    result = f"从当前位置{mode_names.get(mode, '公交地铁')}前往「{destination}」的路线：\n"
    
    if mode == "transit":
        # 公交路线
        steps = route.get("steps", [])
        for i, step in enumerate(steps[:5]):  # 最多显示5步
            instructions = step.get("instructions", "")
            result += f"{i+1}. {instructions}\n"
    else:
        # 其他出行方式
        distance = route.get("distance", 0)
        duration = route.get("duration", 0)
        result += f"距离：{distance/1000:.1f}公里\n"
        result += f"预计时间：{duration//60}分钟\n"
    
    return result


@tool
async def baidu_map_search_place(query: str, city: str = "") -> str:
    """
    百度地图地点搜索工具。
    用于搜索附近的医院、药店、超市等设施。
    
    参数:
        query: 搜索关键词，如"医院"、"药店"、"超市"
        city: 城市名称（可选）
    
    返回:
        搜索结果列表
    """
    places = await baidu_map_service.search_place(query, city=city)
    
    if not places:
        return f"抱歉，没有找到附近的「{query}」。"
    
    result = f"为您找到以下{query}：\n"
    for i, place in enumerate(places[:5]):  # 最多显示5个
        name = place.get("name", "")
        address = place.get("address", "")
        distance = place.get("distance", "")
        result += f"{i+1}. {name}"
        if address:
            result += f"，地址：{address}"
        if distance:
            result += f"，距离：{distance}米"
        result += "\n"
    
    return result


@tool
async def baidu_map_get_address(lat: float, lng: float) -> str:
    """
    根据经纬度获取详细地址。
    
    参数:
        lat: 纬度
        lng: 经度
    
    返回:
        详细地址信息
    """
    address = await baidu_map_service.reverse_geocode(lat, lng)
    if address:
        return f"当前位置的地址是：{address}"
    return "抱歉，无法获取当前位置的地址信息。"
