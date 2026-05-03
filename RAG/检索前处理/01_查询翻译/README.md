# 01 查询翻译学习手册

## 1. 查询重写（Query Rewrite）

作用：把口语、歧义、缺关键词的用户查询改写为“更可检索”的表达。

实现要点：

1. 保持原意，不凭空添加事实。
2. 补齐核心检索关键词（实体、时间、范围、约束）。
3. 输出结构可控（建议 JSON）。

风险：过度重写导致偏题。

## 2. 查询分解（Query Decomposition）

作用：把复杂多意图查询拆成多个子查询并行检索。

实现要点：

1. 每个子查询应独立可检索。
2. 子查询数量不宜过多（通常 2~5）。
3. 合并阶段要去重并做优先级排序。

风险：拆分过细导致噪声增加与成本上升。

## 3. 查询澄清（Query Clarification）

作用：当查询信息不足时，先提问再检索。

实现要点：

1. 判断是否“必须澄清”。
2. 澄清问题应短、单一、可选项明确。
3. 未澄清时可用保守默认策略。

风险：过度澄清影响交互效率。

## 4. 查询扩展（Query Expansion）

作用：给查询增加同义词、上下位词、术语变体，提高召回覆盖。

实现要点：

1. 扩展词要有主题约束。
2. 可对扩展词设置权重。
3. 适合和稀疏检索/混合检索结合。

风险：扩展过宽导致误召回。

## 5. HyDE

作用：先让模型生成“假设答案文档”，再对该文档做 embedding 检索。

实现要点：

1. HyDE 文档应聚焦 query 主题。
2. 可同时保留原 query 向量与 HyDE 向量做融合。
3. 对事实敏感任务要防止幻觉放大。

风险：生成内容偏题会把检索方向带偏。

## 6. 评估建议

1. 对比基线：原 query 直接检索。
2. 逐项开启策略：rewrite -> decomposition -> expansion -> hyde。
3. 记录收益与代价：Recall 提升、延迟提升、token 成本提升。

## Demo 路径（全部在本模块目录下）

1. `demos/demo_query_rewrite.py`
2. `demos/demo_query_decompose.py`
3. `demos/demo_query_clarify.py`
4. `demos/demo_query_expand.py`
5. `demos/demo_hyde.py`
6. `demos/demo_query_translation_all.py`
