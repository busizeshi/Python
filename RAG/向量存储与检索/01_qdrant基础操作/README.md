# 01 Qdrant 基础操作学习手册

## 1. 你要先建立的核心认知

1. Qdrant 是“向量 + 条件过滤”的检索系统，不只是相似度搜索。
2. 一条数据在 Qdrant 的最小单元是 Point：`id + vector + payload`。
3. 向量负责语义召回，payload 负责业务约束，两者必须一起设计。

## 2. 数据模型知识点

1. `Collection`
- 类似逻辑表，定义向量字段的维度、距离度量、索引配置。
- 关键约束：写入向量维度必须和 Collection 定义完全一致。

2. `Vector`
- Dense 向量通常由 embedding 模型生成。
- 当前学习固定使用千问 embedding（`text-embedding-v3`）。

3. `Payload`
- 存放结构化元数据，例如 `source`、`category`、`created_at`。
- 没有 payload 设计，后续几乎无法做稳定过滤检索。

## 3. 检索过程知识点

1. 纯向量检索
- 输入 query 向量，返回最相似 TopK。
- 适合语义相近表达，但可能引入“主题相关但业务不相关”的结果。

2. 过滤检索
- 在向量召回基础上叠加 payload 过滤。
- 业务系统中通常是默认模式，不是高级功能。

3. 返回控制
- `with_payload=True` 便于解释命中原因。
- `with_vectors=False` 通常可减轻响应体积。

## 4. 如何实现（步骤法）

1. 连接 Qdrant：`http://115.190.125.94/`。
2. 调用千问 embedding 先拿到样本向量维度。
3. 创建 collection（尺寸=embedding 维度，距离一般先用 Cosine）。
4. 把原文本 + metadata 封装成 points 后 upsert。
5. 用 query 先做纯向量检索，再加 filter 对比结果。

## 5. 参数与设计决策

1. 距离度量默认建议 `Cosine`
- 对文本语义检索通常最稳。

2. TopK 初始建议 `3~10`
- 太小易漏召回，太大噪声变多。

3. payload 字段最小集合
- `doc_id`：唯一文档标识
- `chunk_id`：分块标识
- `source`：来源
- `category`：业务标签
- `created_at`：时间

## 6. 常见错误与排查

1. 维度不一致
- 现象：upsert 报错。
- 原因：collection size 和 embedding 维度不同。

2. 有结果但不相关
- 原因常见为 chunk 质量差、topk 过大、无过滤。

3. 查询延迟高
- 先看是否返回了不必要的大 payload 或 vectors。

## 7. 本模块实践入口

1. `demo_01_health_check.py`
2. `demo_02_create_upsert.py`
3. `demo_03_search_and_filter.py`

## 8. 通过标准

1. 你能从零创建 collection 并写入数据。
2. 你能写出“向量 + payload 过滤”查询。
3. 你能解释每个命中结果为何被召回。
