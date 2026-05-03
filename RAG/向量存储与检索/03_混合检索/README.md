# 03 Qdrant 混合检索学习手册（Dense + Sparse）

## 1. 这一模块你要掌握的核心能力

1. 能解释 Dense 检索和 Sparse 检索各自擅长什么。
2. 能实现 Dense-only、Sparse-only、Hybrid 三种模式并对比结果。
3. 能根据查询类型调整融合权重，而不是固定一个参数。

## 2. 混合检索的本质

1. Dense（语义向量）
- 优势：同义改写、口语表达、语义泛化能力强。
- 短板：对精确词（产品编号、版本号、专有名词）不稳定。

2. Sparse（关键词）
- 优势：关键词精确命中强，可解释性高。
- 短板：对同义表达和语义改写不鲁棒。

3. Hybrid（融合）
- 思路：并行召回，再融合排序。
- 目标：同时保留语义能力和精确命中能力。

## 3. 你需要知道的实现路径

1. 数据准备
- 同一批文档，既用于 Dense 向量召回，也用于 Sparse 关键词打分。

2. 双路召回
- Dense 路：query -> embedding -> Qdrant 向量检索 TopK。
- Sparse 路：query 关键词 -> 文档关键词重叠打分 TopK。

3. 融合重排
- 常用方法：加权融合。
- 示例：`hybrid_score = w_dense * dense_score + w_sparse * sparse_score`

4. 输出可解释结果
- 至少输出：文档文本、Dense 分、Sparse 分、Hybrid 分。

## 4. 权重调参方法（实战）

1. 按查询类型分组
- 语义问答型：Dense 权重更高。
- 术语精确型：Sparse 权重更高。

2. 固定候选池再调权重
- 先固定 Dense TopK 和 Sparse TopK。
- 再调 `w_dense / w_sparse`，观察 Recall@K 和误召回变化。

3. 先看失败样本再调参
- 看哪些 query 被错召回，反推是“语义不足”还是“关键词不足”。

## 5. 常见坑

1. 候选池太小，融合没有发挥空间。
2. 只输出最终分，不保留分项分数，无法解释结果。
3. 不做分词清洗，Sparse 得分噪声大。

## 6. 本模块 Demo 能学到什么

`demo_hybrid_retrieval.py` 会演示：

1. 构建中文文档样本并写入 Qdrant。
2. 用千问生成 query 向量并做 Dense 检索。
3. 本地做简化 Sparse 打分（关键词重叠率）。
4. 做融合排序并输出 Dense-only / Sparse-only / Hybrid 三组结果对比。

## 7. 验收标准

1. 你能解释某条结果为何在 Hybrid 中上升或下降。
2. 你能根据查询类型给出一组合理权重。
3. 你能指出至少 2 条混合检索失败样本及原因。
