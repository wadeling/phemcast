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

创建环境变量文件并配置：

```bash
# 创建 .env 文件
cat > .env << EOF
# Registry and Repository Configuration
REGISTRY=ccr.ccs.tencentyun.com
REPO=phemcast

# Platform Configuration
# Supported platforms: linux/amd64, linux/arm64, linux/arm/v7
# Default: linux/amd64
PLATFORM=linux/amd64

# Database Configuration
MYSQL_ROOT_PASSWORD=password
MYSQL_DATABASE=phemcast
MYSQL_USER=phemcast
MYSQL_PASSWORD=phemcast
EOF
```

### 3. 构建镜像

使用Makefile构建镜像（推荐）：

```bash
# 构建x86_64版本（默认）
make build-all

# 构建ARM64版本
make build-all platform=linux/arm64

# 构建多平台版本
make build-multi-platform
```

或使用Docker命令直接构建：

```bash
# 构建前端镜像
docker build --platform linux/amd64 -t industry-news-agent-frontend:latest -f ../Dockerfile.frontend ..

# 构建后端镜像
docker build --platform linux/amd64 -t industry-news-agent-backend:latest -f ../Dockerfile.backend ..
```

### 4. 启动服务

使用部署脚本启动（推荐）：

```bash
# 启动x86_64版本
./deploy.sh start

# 启动ARM64版本
PLATFORM=linux/arm64 ./deploy.sh start

# 或直接使用docker-compose
docker-compose up -d
```

### 5. 初始化邀请码

```bash
# 等待MySQL服务启动完成
docker-compose exec backend python init_invite_codes.py
```

## 平台支持

系统支持多种CPU架构：

- **linux/amd64**: x86_64架构（Intel/AMD处理器）
- **linux/arm64**: ARM64架构（Apple Silicon、ARM服务器）
- **linux/arm/v7**: ARM v7架构（较老的ARM设备）

### 平台选择建议

- **开发环境**: 使用 `linux/amd64`（默认）
- **Apple Silicon Mac**: 使用 `linux/arm64`
- **ARM服务器**: 使用 `linux/arm64`
- **树莓派等设备**: 使用 `linux/arm/v7`

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
