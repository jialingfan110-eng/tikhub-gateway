"""
配置文件
"""
import os

# TikHub 上游地址
TIKHUB_BASE_URL = os.getenv("TIKHUB_BASE_URL", "https://api.tikhub.dev")

# TikHub 主 API Key（公司购买的那个）
TIKHUB_MASTER_KEY = os.getenv("TIKHUB_MASTER_KEY", "your-tikhub-master-key-here")

# 管理员 API Key（用来管理用户、查看统计）
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "admin-secret-key-change-me")

# 数据库路径
DATABASE_PATH = os.getenv("DATABASE_PATH", "tikhub_gateway.db")

# 默认每个新用户的额度（美元）
DEFAULT_USER_QUOTA = float(os.getenv("DEFAULT_USER_QUOTA", "10.0"))

# 计费规则：每个接口的单价（美元/次）
# 可以根据 TikHub 的实际价格调整
API_PRICING = {
    # 抖音相关
    "/api/v1/douyin/user/info": 0.001,
    "/api/v1/douyin/user/posts": 0.002,
    "/api/v1/douyin/post/detail": 0.001,
    
    # 视频号相关
    "/api/v1/wechat_channels/v2/user/info": 0.001,
    "/api/v1/wechat_channels/v2/live/list": 0.002,
    "/api/v1/wechat_channels/v2/live/detail": 0.001,
    
    # 小红书相关
    "/api/v1/xiaohongshu/user/info": 0.001,
    "/api/v1/xiaohongshu/notes": 0.002,
    
    # 通用默认价格
    "_default": 0.001,
}
