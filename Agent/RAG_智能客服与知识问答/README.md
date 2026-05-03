# Helpdesk AI

基于 LangChain + Qdrant + FastAPI 的企业客服问答系统，支持 FAQ 问答、工单创建、投诉升级和多轮会话记忆。

## 使用方式

1. 安装依赖
```bash
pip install -r requirements.txt
```

2. 准备 `.env`
```env
# 阿里云 DashScope 兼容 OpenAI 接口
DASHSCOPE_API_KEY=your-dashscope-api-key
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
CHAT_MODEL=qwen-plus
EMBEDDING_MODEL=text-embedding-v4

# Qdrant
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=
QDRANT_COLLECTION=helpdesk-knowledge
```

3. 启动 Qdrant（若你本地未启动）
```bash
docker run -p 6333:6333 qdrant/qdrant
```

4. 构建向量索引
```bash
python ingest/index_qdrant.py
```

5. 启动服务
```bash
uvicorn app.main:app --reload --port 8000
```

## 调用示例

```bash
curl -X POST http://127.0.0.1:8000/chat ^
  -H "Content-Type: application/json" ^
  -d "{\"session_id\":\"s1\",\"user_id\":\"u1\",\"query\":\"你们的服务时间是什么时候？\"}"
```
