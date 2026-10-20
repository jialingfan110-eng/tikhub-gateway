# TikHub Gateway - 轻量级 API 管理网关

专门用于管理 TikHub API 的员工使用情况，自动统计每个员工的调用次数和费用。

## 功能特点

- ✅ **用户管理**：给每个员工分发独立的 API Key
- ✅ **用量统计**：自动记录每个员工的调用次数和费用
- ✅ **额度控制**：可以给每个员工设置额度上限
- ✅ **透明计费**：按次计费，完全匹配 TikHub 的计费方式
- ✅ **数据导出**：提供 API 接口，方便对接到烛光看板
- ✅ **轻量级**：单个 Python 服务，SQLite 数据库，无需额外依赖

## 快速部署（Railway）

### 1. 准备环境变量

在 Railway 部署时设置以下环境变量：

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `TIKHUB_BASE_URL` | TikHub 上游地址 | `https://api.tikhub.dev` |
| `TIKHUB_MASTER_KEY` | 你的 TikHub API Key | `sk-xxxxxxxxxxxx` |
| `ADMIN_API_KEY` | 管理员 Key（用来管理用户） | `my-admin-secret-123` |
| `DEFAULT_USER_QUOTA` | 新用户默认额度（美元） | `10.0` |

### 2. 部署步骤

1. Fork 这个项目到你的 GitHub
2. 在 Railway 中选择 "Deploy from GitHub repo"
3. 选择你 Fork 的仓库
4. 配置上面的环境变量
5. 点击部署，等待启动完成

## 使用方法

### 1. 创建员工账号（管理员）

```bash
curl -X POST https://your-app.railway.app/admin/users \
  -H "Authorization: Bearer my-admin-secret-123" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "张三",
    "email": "zhangsan@company.com",
    "department": "技术部",
    "quota": 20.0
  }'
```

返回：
```json
{
  "id": 1,
  "api_key": "tk-xxxxxxxxxxxx",
  "name": "张三",
  "department": "技术部",
  "quota": 20.0,
  "used_quota": 0.0
}
```

### 2. 员工调用 API

员工使用分配到的 `api_key` 来调用，和直接用 TikHub 一样：

```bash
curl https://your-app.railway.app/api/v1/douyin/user/info \
  -H "Authorization: Bearer tk-xxxxxxxxxxxx"
```

网关会自动：
- 验证员工的身份和额度
- 记录调用次数和费用
- 转发请求到 TikHub
- 返回结果

### 3. 查看用量统计（管理员）

```bash
# 查看今天的统计
curl https://your-app.railway.app/admin/stats/daily \
  -H "Authorization: Bearer my-admin-secret-123"
```

返回数据包含：
- 每个员工的调用次数和消耗费用
- 每个 API 路径的调用统计
- 按部门汇总的用量

## 数据对接烛光看板

这个网关提供了完整的统计 API，你可以：

1. **每天定时拉取数据**：写一个简单的脚本，每天凌晨调用 `/admin/stats/daily` 接口
2. **写入飞书多维表格**：把拉到的数据写入你们已有的多维表格
3. **烛光看板读取**：看板直接读多维表格的数据即可

## 目录结构

```
tikhub-gateway/
├── main.py          # 主服务
├── config.py        # 配置文件
├── database.py      # 数据库操作
├── requirements.txt # Python 依赖
├── Dockerfile       # Docker 部署文件
└── README.md        # 说明文档
```
