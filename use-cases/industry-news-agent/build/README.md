# Industry News Agent Docker 部署指南

## 📋 概述

本项目使用Docker容器化部署，包含两个主要服务：
- **Frontend**: 基于Nginx的静态文件服务
- **Backend**: 基于Python FastAPI的后端服务

## 🏗️ 目录结构

```
build/
├── frontend/
│   ├── Dockerfile          # 前端Docker镜像构建文件
│   └── nginx.conf          # Nginx配置文件
├── backend/
│   └── Dockerfile          # 后端Docker镜像构建文件
├── docker-compose.yml      # 服务编排文件
├── requirements.txt         # 基础Python依赖
├── .dockerignore           # Docker构建忽略文件
├── build.sh                # 镜像构建脚本
├── deploy.sh               # 部署管理脚本
└── README.md               # 本文件
```

## 🚀 快速开始

### 1. 构建镜像

```bash
# 进入build目录
cd build

# 构建所有镜像
./build.sh
```

### 2. 启动应用

```bash
# 使用docker-compose启动
docker-compose up -d

# 或者使用部署脚本
./deploy.sh start
```

### 3. 访问应用

- **前端界面**: http://localhost
- **后端API**: http://localhost:8000
- **健康检查**: http://localhost/health

## 🛠️ 部署脚本使用

`deploy.sh` 脚本提供了完整的应用管理功能：

```bash
# 查看帮助
./deploy.sh help

# 启动应用
./deploy.sh start

# 停止应用
./deploy.sh stop

# 重启应用
./deploy.sh restart

# 查看状态
./deploy.sh status

# 查看日志
./deploy.sh logs

# 构建并启动
./deploy.sh build

# 清理所有资源
./deploy.sh clean
```

## 🔧 配置说明

### 前端配置 (nginx.conf)

- 端口: 80
- 静态文件服务
- API代理到后端
- Gzip压缩
- 静态资源缓存
- 健康检查端点

### 后端配置

- 端口: 8000
- Python 3.12环境
- 健康检查
- 日志和报告目录挂载

### 环境变量

可以通过 `docker-compose.yml` 或环境文件设置：

```bash
ENVIRONMENT=production
LOG_LEVEL=INFO
```

## 📊 监控和日志

### 健康检查

- 前端: `GET /health`
- 后端: `GET /health`

### 日志查看

```bash
# 查看所有服务日志
./deploy.sh logs

# 查看特定服务日志
docker-compose logs frontend
docker-compose logs backend
```

### 状态监控

```bash
# 查看服务状态
./deploy.sh status

# 查看资源使用
docker stats
```

## 🔄 更新部署

### 1. 停止服务

```bash
./deploy.sh stop
```

### 2. 重新构建

```bash
./build.sh
```

### 3. 启动服务

```bash
./deploy.sh start
```

## 🧹 清理和维护

### 清理所有资源

```bash
./deploy.sh clean
```

这将删除：
- 所有容器
- 网络
- 卷（包括报告和日志）

### 查看磁盘使用

```bash
docker system df
```

### 清理未使用的镜像

```bash
docker image prune -a
```

## 🚨 故障排除

### 常见问题

1. **端口冲突**
   - 检查80和8000端口是否被占用
   - 修改 `docker-compose.yml` 中的端口映射

2. **权限问题**
   - 确保脚本有执行权限: `chmod +x *.sh`

3. **构建失败**
   - 检查Docker是否运行
   - 检查网络连接
   - 查看构建日志

### 调试模式

```bash
# 前台运行查看详细输出
docker-compose up

# 查看特定服务日志
docker-compose logs -f backend
```

## 📝 注意事项

1. **数据持久化**: 报告和日志存储在Docker卷中
2. **网络配置**: 前端通过Nginx代理API请求到后端
3. **健康检查**: 确保服务正常运行
4. **资源限制**: 可以根据需要调整Docker资源限制

## 🔗 相关链接

- [Docker官方文档](https://docs.docker.com/)
- [Docker Compose文档](https://docs.docker.com/compose/)
- [Nginx配置参考](https://nginx.org/en/docs/)
- [FastAPI部署指南](https://fastapi.tiangolo.com/deployment/)
