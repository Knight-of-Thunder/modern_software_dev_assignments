# Week 3 - Financial MCP Server (Python)

这是一个基于 `mcp.server.fastmcp.FastMCP` 的金融数据 MCP Server，集成 [Financial Modeling Prep API](https://site.financialmodelingprep.com/developer/docs)。

## 功能

- `get_stock_quote(ticker)`  
  返回实时价格、日内高点、日内低点、涨跌幅。
- `get_financial_metrics(ticker)`  
  返回关键财务指标（市值、PE Ratio、EPS 等）。

## 技术实现

- 核心框架：`FastMCP`
- 传输模式：默认 `stdio`
- 代码结构：通过 `create_mcp_app()` 抽离，可复用到 FastAPI 挂载
- 请求模型：异步（`httpx.AsyncClient`）
- 日志输出：全部走 `logging`，并输出到 `sys.stderr`
- 错误处理：
  - ticker 格式非法
  - ticker 无数据
  - 上游网络超时
  - HTTP 错误（含 429 限流）

## 目录结构

`week3/server` 下主要文件：

- `main.py`：stdio 启动入口
- `app.py`：MCP 工具注册 + FastAPI 挂载工厂
- `fmp_service.py`：FMP API 异步访问与字段映射
- `errors.py`：统一错误类型
- `config.py`：环境变量和默认配置
- `fastapi_app.py`：可选 FastAPI 入口示例

## 安装与运行

1) 安装依赖：

```bash
pip install -r week3/server/requirements.txt
```

2) 设置环境变量：

```bash
export FMP_API_KEY="你的FMP_API_KEY"
```

3) 启动 stdio MCP Server：

```bash
python -m week3.server.main
```

## FastAPI 挂载（可选，预留）

如需未来扩展到 HTTP，可运行：

```bash
uvicorn week3.server.fastapi_app:app --host 0.0.0.0 --port 8000
```

说明：当前以 stdio 为主，`fastapi_app.py` 仅用于展示挂载方式与代码复用结构。

## 工具示例

### get_stock_quote

输入：

```json
{ "ticker": "AAPL" }
```

输出（示例）：

```json
{
  "success": true,
  "data": {
    "ticker": "AAPL",
    "price": 192.53,
    "day_high": 193.2,
    "day_low": 190.7,
    "change_percent": 0.86,
    "timestamp": 1710000000
  }
}
```

### get_financial_metrics

输入：

```json
{ "ticker": "AAPL" }
```

输出（示例）：

```json
{
  "success": true,
  "data": {
    "ticker": "AAPL",
    "company_name": "Apple Inc.",
    "market_cap": 2900000000000,
    "pe_ratio": 30.52,
    "eps": 6.42,
    "industry": "Consumer Electronics",
    "sector": "Technology",
    "exchange": "NASDAQ"
  }
}
```

## 常见错误

- `FMP_API_KEY is not set`：未配置环境变量
- `Invalid ticker format`：股票代码格式不合法
- `No quote/financial metrics found`：代码不存在或无可用数据
- `Upstream request timed out`：上游超时
- `API rate limit exceeded`：触发限流，请稍后重试

