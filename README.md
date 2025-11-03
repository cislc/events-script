# Gitee Events Crawler

自动爬取 Gitee 组织动态的 Python 脚本项目。

## 功能特性

- 自动爬取指定 Gitee 组织的公开动态
- 增量更新,避免重复爬取
- 每天凌晨 1 点自动执行
- 数据以 JSONL 格式保存(每行一个 JSON 对象)
- 完整的日志记录
- access_token 可配置

## 项目结构

```
events-script/
├── crawler.py              # 爬虫主程序
├── scheduler.py            # 定时任务调度器
├── config.json             # 配置文件
├── requirements.txt        # Python 依赖
├── start_scheduler.bat     # Windows 启动脚本
├── run_once.bat           # 手动运行一次
├── data/                  # 数据目录
│   ├── events.jsonl       # 事件数据文件
│   └── state.json         # 状态文件(记录最新事件ID)
└── logs/                  # 日志目录
    └── crawler_YYYYMMDD.log
```

## 安装步骤

### 1. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 access_token

编辑 `config.json` 文件,填入你的 Gitee access_token:

```json
{
  "access_token": "your_access_token_here",
  "organization": "dongshan-community",
  "api_base_url": "https://gitee.com/api/v5",
  "limit": 100,
  "data_dir": "./data",
  "log_dir": "./logs"
}
```

**如何获取 access_token:**
1. 登录 Gitee
2. 访问 https://gitee.com/profile/personal_access_tokens
3. 创建新令牌,选择权限(至少需要 `projects` 读权限)
4. 复制生成的 token 到配置文件

## 使用方法

### 方式一: 启动定时调度器(推荐)

**Windows:**
```bash
# 双击运行
start_scheduler.bat

# 或命令行运行
python scheduler.py
```

**Linux/Mac:**
```bash
python scheduler.py
```

调度器会在每天凌晨 1 点自动运行爬虫。

### 方式二: 手动运行一次

**Windows:**
```bash
# 双击运行
run_once.bat

# 或命令行运行
python crawler.py
```

**Linux/Mac:**
```bash
python crawler.py
```

### 方式三: 使用系统定时任务

#### Windows 任务计划程序

1. 打开"任务计划程序"
2. 创建基本任务
3. 触发器: 每天凌晨 1:00
4. 操作: 启动程序
   - 程序: `python.exe` 的完整路径
   - 参数: `crawler.py`
   - 起始于: 项目目录路径

#### Linux Cron

```bash
# 编辑 crontab
crontab -e

# 添加定时任务(每天凌晨1点执行)
0 1 * * * cd /path/to/events-script && /usr/bin/python3 crawler.py
```

## 数据格式

### events.jsonl

采用 JSONL 格式(JSON Lines),每行一个完整的 JSON 对象,方便流式读取和追加:

```jsonl
{"id": "1431223426296414208", "type": "PushEvent", "actor": {...}, "_crawled_at": "2025-10-27T10:00:00"}
{"id": "1430981676218736640", "type": "PushEvent", "actor": {...}, "_crawled_at": "2025-10-27T10:00:00"}
```

**优点:**
- 易于追加写入
- 支持流式处理大文件
- 每行独立,不会因格式错误影响整个文件
- 便于使用 `grep`、`awk` 等工具处理

### state.json

记录最新爬取的事件 ID,用于增量更新:

```json
{
  "last_event_id": "1431223426296414208",
  "last_update": "2025-10-27T10:00:00"
}
```

## 增量更新机制

1. 首次运行时获取所有可用事件
2. 后续运行时,从最新事件往前爬取,直到遇到上次记录的 `last_event_id`
3. 只保存新增的事件,避免重复

## 日志

日志文件按日期命名,保存在 `logs/` 目录:

```
logs/crawler_20251027.log
```

日志包含:
- 爬取开始/结束时间
- 获取的事件数量
- 错误信息
- API 请求详情

## API 说明

使用 Gitee OpenAPI v5:

```
GET https://gitee.com/api/v5/orgs/{org}/events
```

参数:
- `access_token`: 必需,用户授权码
- `org`: 必需,组织路径
- `prev_id`: 可选,用于翻页
- `limit`: 可选,每页数量(最大100)

## 常见问题

**Q: 如何更换要爬取的组织?**

A: 修改 `config.json` 中的 `organization` 字段。

**Q: 如何修改定时时间?**

A: 编辑 `scheduler.py` 第 17 行:
```python
schedule.every().day.at("01:00").do(job)  # 改为其他时间,如 "02:30"
```

**Q: 数据文件太大怎么办?**

A: JSONL 格式支持按行处理,可以定期归档:
```bash
# 按月份归档
mv data/events.jsonl data/events_202510.jsonl
```

**Q: 遇到 API 限流怎么办?**

A: Gitee API 有频率限制,可以:
1. 减少 `limit` 参数
2. 增加请求间隔
3. 使用企业版 access_token