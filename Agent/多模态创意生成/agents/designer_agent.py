import os
import time

import requests
from openai import NotFoundError, OpenAI

from config import (
    DASHSCOPE_API_KEY,
    DASHSCOPE_BASE_URL,
    DASHSCOPE_IMAGE_BASE_URL,
    IMAGE_MODEL,
)


class DesignerAgent:
    def __init__(self):
        self.client = OpenAI(api_key=DASHSCOPE_API_KEY, base_url=DASHSCOPE_BASE_URL)

    def run(self, text_prompt: str, save_path: str = "outputs/poster.png") -> str:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        try:
            return self._generate_by_compatible_api(text_prompt, save_path)
        except NotFoundError:
            return self._generate_by_dashscope_native(text_prompt, save_path)

    def _generate_by_compatible_api(self, text_prompt: str, save_path: str) -> str:
        response = self.client.images.generate(
            model=IMAGE_MODEL,
            prompt=text_prompt,
            size="1024x1024",
            n=1,
        )
        if response.data and len(response.data) > 0:
            image_url = getattr(response.data[0], "url", None)
            if image_url:
                self._download(image_url, save_path)
                return save_path
        raise RuntimeError("图片生成失败：兼容接口未返回图片 URL")

    def _generate_by_dashscope_native(self, text_prompt: str, save_path: str) -> str:
        submit_url = f"{DASHSCOPE_IMAGE_BASE_URL}/api/v1/services/aigc/text2image/image-synthesis"
        headers = {
            "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
            "Content-Type": "application/json",
            "X-DashScope-Async": "enable",
        }
        payload = {
            "model": IMAGE_MODEL,
            "input": {"prompt": text_prompt},
            "parameters": {"size": "1024*1024", "n": 1},
        }

        resp = requests.post(submit_url, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        task_id = resp.json().get("output", {}).get("task_id")
        if not task_id:
            raise RuntimeError(f"图片生成失败：未获取 task_id，响应={resp.text}")

        task_url = f"{DASHSCOPE_IMAGE_BASE_URL}/api/v1/tasks/{task_id}"
        for _ in range(30):
            poll = requests.get(task_url, headers=headers, timeout=60)
            poll.raise_for_status()
            body = poll.json()
            status = body.get("output", {}).get("task_status")
            if status == "SUCCEEDED":
                results = body.get("output", {}).get("results", [])
                if results and results[0].get("url"):
                    self._download(results[0]["url"], save_path)
                    return save_path
                raise RuntimeError(f"图片生成失败：任务成功但无图片 URL，响应={body}")
            if status in {"FAILED", "CANCELED"}:
                raise RuntimeError(f"图片生成失败：任务状态={status}，响应={body}")
            time.sleep(2)

        raise RuntimeError("图片生成超时：轮询 60 秒后仍未完成")

    @staticmethod
    def _download(image_url: str, save_path: str) -> None:
        image_response = requests.get(image_url, timeout=120)
        image_response.raise_for_status()
        with open(save_path, "wb") as f:
            f.write(image_response.content)
