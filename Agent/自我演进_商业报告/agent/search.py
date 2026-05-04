import os
from typing import Dict, List

import requests


def baidu_search_func(query: str, num: int = 5) -> List[Dict[str, str]]:
    """Search Chinese web with SerpAPI Baidu engine."""
    api_key = os.getenv("SERPAPI_API_KEY","97db7da7af0aa8b813d9ecca8595b1b9c4ed253b2d9bcaa15ec53a0f3568a6ea")
    if not api_key:
        raise ValueError("Missing SERPAPI_API_KEY")

    url = "https://serpapi.com/search.json"
    params = {
        "engine": "baidu",
        "q": query,
        "api_key": api_key,
        "rn": max(1, min(num, 10)),
    }

    r = requests.get(url, params=params, timeout=60)
    r.raise_for_status()
    data = r.json()

    items = data.get("organic_results", []) or []
    results: List[Dict[str, str]] = []
    for it in items[:num]:
        results.append(
            {
                "title": it.get("title", ""),
                "snippet": it.get("snippet", ""),
                "link": it.get("link", ""),
            }
        )
    return results


baidu_search_tool = {
    "type": "function",
    "function": {
        "name": "baidu_search_func",
        "description": (
            "Search Chinese web using SerpAPI Baidu engine and return top "
            "results (title, snippet, link)."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query string.",
                },
                "num": {
                    "type": "integer",
                    "description": "Number of results to return (1-10).",
                    "minimum": 1,
                    "maximum": 10,
                },
            },
            "required": ["query"],
        },
    },
}
