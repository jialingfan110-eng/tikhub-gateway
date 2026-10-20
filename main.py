"""
TikHub 轻量级 API 网关
专门用于管理 TikHub API 的员工使用情况
"""
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
import httpx
import config
import database
from typing import Optional
from pydantic import BaseModel
import uvicorn

# 初始化数据库
database.init_db()

app = FastAPI(title="TikHub Gateway", version="1.0.0")


# ========== 数据模型 ==========

class CreateUserRequest(BaseModel):
    name: str
    email: str = ""
    department: str = "default"
    quota: Optional[float] = None


# ========== 依赖验证 ==========

async def verify_user(request: Request):
    """验证用户 API Key"""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    
    api_key = auth_header.replace("Bearer ", "")
    user = database.get_user_by_api_key(api_key)
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    
    if user["used_quota"] >= user["quota"]:
        raise HTTPException(status_code=429, detail="Quota exceeded")
    
    return user


async def verify_admin(request: Request):
    """验证管理员 API Key"""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    
    api_key = auth_header.replace("Bearer ", "")
    if api_key != config.ADMIN_API_KEY:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    return True


# ========== 管理接口 ==========

@app.post("/admin/users")
async def admin_create_user(req: CreateUserRequest, admin: bool = Depends(verify_admin)):
    """创建新用户（管理员接口）"""
    user = database.create_user(
        name=req.name,
        email=req.email,
        department=req.department,
        quota=req.quota,
    )
    return user


@app.get("/admin/users")
async def admin_list_users(admin: bool = Depends(verify_admin)):
    """列出所有用户（管理员接口）"""
    return database.list_users()


@app.get("/admin/stats/daily")
async def admin_daily_stats(date: Optional[str] = None, admin: bool = Depends(verify_admin)):
    """获取每日用量统计（管理员接口）"""
    return {
        "date": date,
        "user_stats": database.get_daily_usage(date),
        "api_stats": database.get_api_usage_stats(date),
    }


# ========== 健康检查 ==========

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "tikhub-gateway"}


# ========== TikHub 代理转发核心 ==========

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_to_tikhub(path: str, request: Request, user: dict = Depends(verify_user)):
    """
    核心代理接口：把请求转发到 TikHub
    自动记录每个用户的调用次数和费用
    """
    # 构建完整的 TikHub URL
    tikhub_url = f"{config.TIKHUB_BASE_URL}/{path}"
    
    # 获取请求体
    body = await request.body()
    
    # 复制请求头
    headers = dict(request.headers)
    # 替换成 TikHub 的主 Key
    headers["Authorization"] = f"Bearer {config.TIKHUB_MASTER_KEY}"
    # 移除一些不需要的头
    headers.pop("host", None)
    headers.pop("content-length", None)
    
    # 计算本次调用的费用
    api_path = f"/{path}"
    cost = config.API_PRICING.get(api_path, config.API_PRICING["_default"])
    
    # 转发请求到 TikHub
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.request(
                method=request.method,
                url=tikhub_url,
                content=body,
                headers=headers,
                params=request.query_params,
            )
            
            # 记录用量
            database.log_usage(
                user_id=user["id"],
                api_path=api_path,
                cost=cost,
                status_code=response.status_code,
            )
            
            # 返回 TikHub 的响应
            return JSONResponse(
                content=response.json() if response.headers.get("content-type", "").includes("application/json") else response.text,
                status_code=response.status_code,
                headers=dict(response.headers),
            )
            
        except httpx.RequestError as e:
            # 记录失败的调用（不扣费）
            database.log_usage(
                user_id=user["id"],
                api_path=api_path,
                cost=0,
                status_code=500,
            )
            raise HTTPException(status_code=502, detail=f"Failed to reach TikHub: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
