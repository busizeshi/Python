# Game NPC LangGraph

一个基于 LangGraph 的多角色 NPC 对话示例项目，玩家可以和村长、铁匠、药师进行智能对话。

## 特性
- AI 路由：根据输入自动选择最合适的 NPC
- 多轮对话：保留上下文历史
- 角色扮演：每个 NPC 有独立人设和领域
- 即插即用：安装依赖后可直接运行

## NPC 角色
- 村长：村庄管理、历史故事、一般建议
- 铁匠：武器装备、打造修理、战斗相关
- 药师：治疗、草药、健康相关

## 安装
```bash
pip install -r requirements.txt
```

## 使用（阿里千问 qwen-turbo）
```powershell
$env:DASHSCOPE_API_KEY="你的千问API Key"
$env:LLM_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"
$env:LLM_MODEL="qwen-turbo"
python -m game_npc_langgraph.main
```

## 项目结构
- `game_npc_langgraph/main.py`：主程序与状态图
- `game_npc_langgraph/router.py`：路由器
- `game_npc_langgraph/npc_agents.py`：NPC 节点和人设

## 备注
当前默认模型是 `qwen-turbo`，也可通过环境变量覆盖。
