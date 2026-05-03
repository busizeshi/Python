# 用千问 + python-pptx 生成真实 PPT

## 1. 安装依赖

```powershell
cd D:\dev\Python\Agent\skills\ppt-generator
D:\dev\Python\Agent\.venv\Scripts\pip.exe install -r .\requirements.txt
```

## 2. 配置环境变量

复制 `.env.example` 为 `.env`，并填入你的密钥：

```env
DASHSCOPE_API_KEY=你的DashScope密钥
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
QWEN_MODEL=qwen-plus
```

## 3. 准备输入

编辑 `examples/request_sample.json`：

```json
{
  "topic": "Q3 产品增长复盘",
  "audience": "管理层",
  "duration_minutes": 15,
  "tone": "说服",
  "language": "zh"
}
```

## 4. 生成大纲 + PPT

```powershell
D:\dev\Python\Agent\.venv\Scripts\python.exe .\scripts\generate_ppt_with_qwen.py
```

默认输出：
- `examples/outline_llm_output.json`
- `examples/slides_from_qwen.pptx`
