import os
from dotenv import load_dotenv

load_dotenv()

DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")
DASHSCOPE_BASE_URL = os.getenv(
    "DASHSCOPE_BASE_URL",
    "https://dashscope.aliyuncs.com/compatible-mode/v1",
)
DASHSCOPE_IMAGE_BASE_URL = os.getenv(
    "DASHSCOPE_IMAGE_BASE_URL",
    "https://dashscope.aliyuncs.com",
)

CHAT_MODEL = os.getenv("CHAT_MODEL", "qwen-plus")
IMAGE_MODEL = os.getenv("IMAGE_MODEL", "wanx-v1")
