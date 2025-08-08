# Industry News Agent - Project Structure

## 📁 新的项目结构

```
industry-news-agent/
├── html/                          # 前端代码目录
│   ├── index.html                 # 主页面HTML
│   ├── css/                       # 样式文件
│   │   └── style.css              # 主样式表
│   ├── js/                        # JavaScript文件
│   │   └── app.js                 # 前端逻辑
│   └── images/                    # 图片资源目录
├── src/                          # 后端代码目录
│   ├── web_interface.py          # FastAPI应用（已简化）
│   ├── agent.py                  # LangGraph代理
│   ├── tools.py                  # 工具函数
│   ├── models.py                 # 数据模型
│   ├── web_scraper.py           # 网页爬虫
│   ├── report_generator.py       # 报告生成器
│   ├── email_service.py          # 邮件服务
│   └── settings.py               # 配置管理
├── data/                         # 数据文件
│   └── wize-io-blog.html         # 示例HTML文件
├── tests/                        # 测试文件
├── reports/                      # 生成的报告目录
├── requirements.txt              # Python依赖
├── .env                         # 环境变量
├── test_structure.py           # 结构测试脚本
└── test_scraping.py            # 爬虫测试脚本
```

## 🔄 主要变更

### 1. **前端代码分离**
- ✅ 将HTML、CSS、JavaScript代码从 `web_interface.py` 中分离
- ✅ 创建了专门的 `html/` 目录存放前端资源
- ✅ 实现了前后端代码的完全分离

### 2. **简化的Web接口**
- ✅ `web_interface.py` 现在只包含FastAPI路由和业务逻辑
- ✅ 移除了所有内联的HTML和JavaScript代码
- ✅ 使用 `FileResponse` 提供静态文件服务

### 3. **改进的静态文件服务**
- ✅ 自动挂载 `html/` 目录到 `/static` 路径
- ✅ 分别挂载 `css/` 和 `js/` 子目录
- ✅ 支持静态资源的热重载

## 📋 文件说明

### 前端文件

#### `html/index.html`
- 主页面HTML结构
- 引用外部CSS和JavaScript文件
- 包含完整的用户界面表单

#### `html/css/style.css`
- 所有样式定义
- 响应式设计
- 加载动画和进度条样式

#### `html/js/app.js`
- 前端交互逻辑
- 表单提交处理
- 任务状态检查功能
- 异步API调用

### 后端文件

#### `src/web_interface.py` (已简化)
- FastAPI应用定义
- REST API端点
- 静态文件服务配置
- 业务逻辑处理

## 🚀 运行应用

### 开发模式
```bash
cd /Users/lingximo/go/src/github.com/wadeling/phemcast/use-cases/industry-news-agent
python -m uvicorn src.web_interface:app --host 0.0.0.0 --port 8000 --reload
```

### 生产模式
```bash
python -m uvicorn src.web_interface:app --host 0.0.0.0 --port 8000
```

### 访问应用
- 主页面: http://localhost:8000
- API文档: http://localhost:8000/docs
- 系统状态: http://localhost:8000/api/status

## 🔧 开发工作流

### 修改前端
1. 编辑 `html/` 目录下的相应文件
2. 刷新浏览器查看更改
3. 无需重启后端服务

### 修改后端
1. 编辑 `src/` 目录下的Python文件
2. 保存更改（启用自动重载）
3. 服务会自动重启

### 添加新静态资源
1. 将文件放入 `html/` 相应子目录
2. 通过 `/static/` 路径访问

## 📝 API端点

### 表单提交
- `POST /api/generate-report-form` - 生成报告（表单数据）

### JSON API
- `POST /api/generate-report` - 生成报告（JSON数据）
- `GET /api/task/{task_id}` - 检查任务状态
- `GET /api/status` - 获取系统状态
- `GET /api/docs` - API文档信息

### 文件下载
- `GET /download/{task_id}/{format_type}` - 下载生成的报告

## ✅ 验证项目结构

运行测试脚本验证所有文件是否正确配置：

```bash
python test_structure.py
```

测试脚本会检查：
- ✅ 所有必要目录是否存在
- ✅ 所有必要文件是否存在
- ✅ HTML内容是否正确
- ✅ CSS样式是否完整
- ✅ JavaScript功能是否正常
- ✅ Python模块是否能正确导入

## 🎯 优势

### 1. **更好的代码组织**
- 前后端代码完全分离
- 静态资源集中管理
- 清晰的目录结构

### 2. **更易于维护**
- 前端修改不影响后端
- 样式和逻辑分离
- 模块化设计

### 3. **更好的开发体验**
- 支持热重载
- 静态资源自动服务
- 清晰的文件分工

### 4. **更好的扩展性**
- 易于添加新页面
- 支持多种静态资源
- 便于团队协作

这个重构后的项目结构更加专业、清晰，便于长期维护和扩展。