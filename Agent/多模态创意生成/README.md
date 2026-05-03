# 多模态创意生成

这是一个基于多 Agent 的创意生成小项目，包含：

- 文案 Agent：生成广告短句
- 评审 Agent：优化文案表达
- 设计 Agent：根据文案生成海报

## 安装

```bash
pip install -r requirements.txt
```

## 环境变量

在项目根目录创建 `.env`：

```env
DASHSCOPE_API_KEY=your-dashscope-api-key
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
CHAT_MODEL=qwen-plus
IMAGE_MODEL=wanx-v1
```

## 运行

```bash
python main.py --product "夏日柠檬饮料" --audience "年轻人"
```

运行后输出：

- 文案：`outputs/campaign.txt`
- 海报：`outputs/poster.png`
