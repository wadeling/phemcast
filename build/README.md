# Industry News Agent - Docker 构建说明

## 概述

本项目使用Docker容器化部署，包含前端和后端两个服务。

## 架构变更说明

### 新架构特点
- **统一入口**: 使用`main.py`作为程序入口点
- **后台任务**: 自动启动TaskProcessor进程管理定时任务
- **进程管理**: 主进程运行FastAPI，子进程运行任务调度器

### 启动方式变更
- **之前**: 分别启动Web服务和调度器
- **现在**: 使用`python main.py`统一启动所有服务

## 构建和部署

### 1. 构建镜像

```bash
# 构建后端镜像
docker build -f build/backend/Dockerfile -t industry-news-agent-backend .

# 构建前端镜像
docker build -f build/frontend/Dockerfile -t industry-news-agent-frontend .
```

### 2. 运行容器

```bash
# 运行后端容器
docker run -d \
  --name industry-news-agent-backend \
  -p 8000:8000 \
  -e DATABASE_URL="mysql://user:password@host:3306/dbname" \
  -e OPENAI_API_KEY="your_api_key" \
  industry-news-agent-backend

# 运行前端容器
docker run -d \
  --name industry-news-agent-frontend \
  -p 80:80 \
  industry-news-agent-frontend
```

### 3. 使用Docker Compose（推荐）

```bash
# 在deploy目录下运行
cd deploy
docker-compose up -d
```

## 服务配置

### 后端服务 (Backend)

- **端口**: 8000
- **入口点**: `python main.py`
- **健康检查**: http://localhost:8000/health
- **功能**: 
  - FastAPI Web服务
  - 后台任务处理器
  - 数据库操作
  - AI分析服务

### 前端服务 (Frontend)

- **端口**: 80
- **入口点**: Nginx
- **健康检查**: http://localhost/health
- **功能**: 
  - 静态文件服务
  - 反向代理到后端
  - 负载均衡

## 环境变量

### 必需环境变量

```bash
# 数据库连接
DATABASE_URL=mysql://username:password@host:3306/database_name

# OpenAI API
OPENAI_API_KEY=your_openai_api_key

# 腾讯云配置（如果使用邮件服务）
TENCENT_CLOUD_SECRET_ID=your_secret_id
TENCENT_CLOUD_SECRET_KEY=your_secret_key
TENCENT_FROM_EMAIL=your_verified_email@example.com
```

### 可选环境变量

```bash
# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
SHOW_FILE_LINE=true
SHOW_FUNCTION=true

# 邮件服务配置
EMAIL_USERNAME=your_email@example.com
EMAIL_PASSWORD=your_email_password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

## 健康检查

### 后端健康检查

```bash
curl http://localhost:8000/health
```

响应示例：
```json
{
  "status": "healthy",
  "timestamp": "2025-08-27T15:48:31.123456"
}
```

### 前端健康检查

```bash
curl http://localhost/health
```

## 日志查看

### 容器日志

```bash
# 查看后端日志
docker logs industry-news-agent-backend

# 查看前端日志
docker logs industry-news-agent-frontend

# 实时查看日志
docker logs -f industry-news-agent-backend
```

### 应用日志

```bash
# 进入容器查看应用日志
docker exec -it industry-news-agent-backend tail -f logs/app.log
```

## 故障排除

### 常见问题

1. **容器启动失败**
   - 检查环境变量配置
   - 查看容器日志
   - 确认端口未被占用

2. **健康检查失败**
   - 检查服务是否正常启动
   - 确认网络连接
   - 查看应用日志

3. **任务调度不工作**
   - 检查TaskProcessor进程状态
   - 查看调度器日志
   - 确认数据库连接

### 调试命令

```bash
# 检查容器状态
docker ps -a

# 检查容器资源使用
docker stats

# 进入容器调试
docker exec -it industry-news-agent-backend bash

# 检查网络连接
docker network ls
docker network inspect bridge
```

## 性能优化

### 资源限制

```bash
# 限制容器资源使用
docker run -d \
  --name industry-news-agent-backend \
  --memory=2g \
  --cpus=2 \
  -p 8000:8000 \
  industry-news-agent-backend
```

### 日志管理

```bash
# 配置日志轮转
docker run -d \
  --name industry-news-agent-backend \
  --log-driver json-file \
  --log-opt max-size=10m \
  --log-opt max-file=3 \
  -p 8000:8000 \
  industry-news-agent-backend
```

## 生产环境部署

### 使用进程管理器

```bash
# 使用supervisor管理进程
sudo apt-get install supervisor
sudo nano /etc/supervisor/conf.d/industry-news-agent.conf
```

### 监控和告警

- 配置Prometheus监控
- 设置Grafana仪表板
- 配置告警规则

## 更新和升级

### 滚动更新

```bash
# 构建新镜像
docker build -t industry-news-agent-backend:v2 .

# 更新服务
docker-compose up -d --no-deps backend
```

### 回滚

```bash
# 回滚到之前的版本
docker-compose up -d --no-deps backend
```

## 安全注意事项

1. **环境变量**: 不要在代码中硬编码敏感信息
2. **网络隔离**: 使用Docker网络隔离服务
3. **权限控制**: 限制容器权限
4. **镜像安全**: 定期更新基础镜像
5. **日志安全**: 避免记录敏感信息

## 联系支持

如果遇到问题，请：
1. 查看容器日志
2. 检查环境变量配置
3. 运行健康检查
4. 查看应用日志
