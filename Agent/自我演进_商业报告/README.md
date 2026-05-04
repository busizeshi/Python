# 自我演进商业报告（SerpAPI Baidu + 千问）

一个可迭代优化的商业报告生成器，支持：

- 报告初稿生成
- 反思决策（修订 or 搜索）
- SerpAPI + Baidu 搜索补全中文信息
- 多维度评分与参数自适应

## 安装

```bash
pip install -r requirements.txt
```

## 环境变量

```env
# 千问（DashScope OpenAI 兼容接口）
DASHSCOPE_API_KEY=your-dashscope-api-key
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
CHAT_MODEL=qwen-plus

# SerpAPI（Baidu）
SERPAPI_API_KEY=your-serpapi-key
```

## 运行

```bash
python main.py --prompt "分析苹果公司最新商业战略" --steps 5 --target-words 1000 --target-score 0.86 --out out.json
```

## 输出

会生成一个 JSON 文件，包含：

- `summary`：最佳报告正文
- `best_score`：最佳评分
- `history`：每轮动作与评分
- `search_summary`：搜索摘要
- `learned_params`：最终学习到的参数
