# 微光年轮 MindRing

用于记录对某个概念、定义在不同时间点的理解，让认知像年轮一样沉淀、生长。

## 技术选型

- 后端：Python + FastAPI
- ORM：SQLAlchemy 2.x
- 数据库：MySQL（默认连接串使用 `mysql+pymysql`，本地测试可切换 SQLite）
- 小程序生态：预留微信登录、订阅消息、内容安全检测与分享海报接口边界

## MVP 功能

### 概念管理（Concept）

- 创建概念：记录“第一性原理”“长期主义”等概念。
- 搜索/聚合：按关键词、创建者搜索概念。
- 置顶：支持把高频概念固定到列表顶部。

### 年轮记录（Insight / The Ring）

- 添加理解：支持 Markdown/富文本字符串、标签、当前心境/状态。
- 时间戳：系统默认写入当前时间，也支持用户传入 `occurred_at` 补录历史理解。
- 版本关联：创建新理解时，若未指定 `previous_insight_id`，系统会自动关联同一用户在该概念下的上一条理解。

### 时间轴与对比

- 时间轴：`/api/concepts/{concept_id}/timeline` 支持正序或倒序展示某个概念的全部理解。
- 对比模式：`/api/insights/diff` 可选择两个时间点的理解，返回新增/删除行。
- 日历视图：`/api/calendar` 返回某个用户每天留下的认知记录数量。

### 微信生态预留

- 微信登录：`/api/wechat/login` 预留 `auth.code2Session` 服务边界。
- 回顾提醒：`/api/wechat/review-reminders` 预留订阅消息触达入口。
- 分享海报：`/api/share-posters` 返回海报文案，方便小程序端使用 Canvas 生成卡片。
- 内容安全：`ContentSafetyService` 预留微信 `security.msgSecCheck` 与 `security.mediaCheckAsync` 接入点；生产审核前必须打开并接入官方检测。

## 快速开始

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
export DATABASE_URL='mysql+pymysql://mindring:mindring@127.0.0.1:3306/mindring?charset=utf8mb4'
uvicorn app.main:app --reload
```

开发或测试时可以临时使用 SQLite：

```bash
export DATABASE_URL='sqlite+pysqlite:///./mindring.db'
```

## API 示例

创建概念：

```bash
curl -X POST http://127.0.0.1:8000/api/concepts \
  -H 'Content-Type: application/json' \
  -d '{"name":"第一性原理","creator_id":"user_1","description":"拆解到基本事实"}'
```

添加理解：

```bash
curl -X POST http://127.0.0.1:8000/api/insights \
  -H 'Content-Type: application/json' \
  -d '{"concept_id":1,"author_id":"user_1","content":"从基本事实重新推导，而不是类比。","mood":"清醒","tags":["思维模型"]}'
```

## 合规提醒

微信小程序上线前必须完善：

1. 用户隐私保护指引与隐私协议弹窗。
2. 文本内容调用 `security.msgSecCheck`。
3. 图片/海报等媒体内容调用 `security.mediaCheckAsync`。
4. 订阅消息只在用户授权后发送，并遵循模板消息使用规范。
