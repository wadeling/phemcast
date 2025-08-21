# Industry News Agent 部署说明

## 功能特性

- 用户名密码登录
- 邀请码登录和用户注册
- 行业新闻分析和报告生成
- 邮件发送功能
- MySQL数据库支持

## 部署步骤

### 1. 环境准备

确保已安装 Docker 和 Docker Compose。

### 2. 配置环境变量

复制环境变量模板并配置：

```bash
cp .env.template .env
# 编辑 .env 文件，填入实际的配置值
```

### 3. 构建镜像

```bash
# 构建前端镜像
docker build -t industry-news-agent-frontend:latest -f ../Dockerfile.frontend ..

# 构建后端镜像
docker build -t industry-news-agent-backend:latest -f ../Dockerfile.backend ..
```

### 4. 启动服务

```bash
docker-compose up -d
```

### 5. 初始化邀请码

```bash
# 等待MySQL服务启动完成
docker-compose exec backend python init_invite_codes.py
```

## 服务说明

- **Frontend**: Nginx前端服务，端口80
- **Backend**: FastAPI后端服务，端口8000
- **MySQL**: 数据库服务，端口3306

## 访问地址

- 前端界面: http://localhost
- 后端API: http://localhost:8000
- 登录页面: http://localhost/login
- API文档: http://localhost:8000/docs

## 邀请码

系统预置的邀请码：
- WELCOME2024
- INDUSTRY2024
- NEWS2024
- AGENT2024
- TEST123

## 数据库

数据库会自动创建以下表：
- `invite_codes`: 邀请码表
- `users`: 用户表

## 故障排除

1. 如果MySQL连接失败，检查容器状态：
   ```bash
   docker-compose ps
   docker-compose logs mysql
   ```

2. 如果后端启动失败，检查日志：
   ```bash
   docker-compose logs backend
   ```

3. 重置数据库：
   ```bash
   docker-compose down -v
   docker-compose up -d
   ```
