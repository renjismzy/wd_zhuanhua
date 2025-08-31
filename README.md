# 文档转换 MCP 服务器

一个支持多种文档格式转换和Server-Sent Events (SSE)的MCP服务器。

## 功能特性

- 🔄 **多格式转换**: 支持 Markdown、HTML、文本、PDF、DOCX 等格式之间的转换
- 🌐 **REST API**: 提供完整的HTTP API接口
- 📡 **SSE支持**: 实时事件推送，支持转换进度监控
- 🔌 **MCP协议**: 完全兼容Model Context Protocol
- ⚡ **异步处理**: 高性能异步文档转换
- 🛡️ **错误处理**: 完善的错误处理和状态管理

## 支持的格式

- **文本格式**: txt, md (Markdown), html
- **文档格式**: pdf, docx, doc

## 安装依赖

```bash
# 安装Python依赖
pip install -r requirements.txt

# 或使用poetry
poetry install
```

## 使用方法

### 1. REST API 模式

启动HTTP服务器：

```bash
python main.py --api
```

服务器将在 `http://localhost:8000` 启动。

#### API 端点

- `GET /formats` - 获取支持的格式列表
- `POST /convert` - 文档转换
- `GET /events` - SSE事件流
- `GET /status/{job_id}` - 获取转换状态

#### 转换示例

```bash
# 使用curl转换文档
curl -X POST http://localhost:8000/convert \
  -F "source_format=md" \
  -F "target_format=html" \
  -F "content=# Hello World\n\nThis is **markdown** text."

# 使用PowerShell
$params = @{
    source_format='md'
    target_format='html'
    content='# Hello World`n`nThis is **markdown** text.'
}
Invoke-RestMethod -Uri 'http://localhost:8000/convert' -Method Post -Body $params
```

### 2. MCP 协议模式

启动MCP服务器：

```bash
python main.py
```

这将启动stdio模式的MCP服务器，可以与支持MCP协议的客户端集成。

#### MCP 工具

- `convert_document` - 转换文档格式
- `list_supported_formats` - 列出支持的格式
- `get_conversion_status` - 获取转换状态

### 3. 测试功能

运行测试脚本验证所有功能：

```bash
python test_api.py
```

## 配置选项

服务器支持通过环境变量进行配置：

```bash
# 服务器配置
export SERVER_HOST=0.0.0.0
export SERVER_PORT=8000

# 文件处理
export MAX_FILE_SIZE=10485760  # 10MB
export TEMP_DIR=./temp

# SSE配置
export SSE_HEARTBEAT_INTERVAL=30
export SSE_CONNECTION_TIMEOUT=300
```

## 项目结构

```
wd_mcp/
├── main.py                 # 主服务器文件
├── document_converter.py   # 文档转换器
├── sse_manager.py         # SSE事件管理器
├── config.py              # 配置管理
├── client_example.py      # 客户端示例
├── test_api.py           # API测试脚本
├── pyproject.toml        # 项目配置
└── README.md             # 项目说明
```

## 开发说明

### 添加新的转换格式

1. 在 `document_converter.py` 中添加转换逻辑
2. 更新 `SUPPORTED_FORMATS` 列表
3. 实现相应的转换方法

### 自定义SSE事件

1. 在 `sse_manager.py` 中定义新的事件类型
2. 使用 `broadcast_event` 方法发送事件

## 示例客户端

查看 `client_example.py` 了解如何：

- 使用MCP协议与服务器交互
- 监听SSE事件流
- 调用REST API

## 错误处理

服务器提供详细的错误信息：

- 格式不支持
- 文件大小超限
- 转换失败
- 网络连接问题

## 性能优化

- 异步文档处理
- 连接池管理
- 临时文件自动清理
- 内存使用优化

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！

---

**注意**: 确保安装了所需的依赖包，特别是用于PDF和DOCX处理的库。