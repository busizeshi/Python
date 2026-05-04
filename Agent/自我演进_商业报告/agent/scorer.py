import math
from collections import Counter
from typing import Dict, List


def _tokens(text: str) -> List[str]:
    """将文本切分为 token，兼容中文字符和英文单词。"""
    import re

    chinese_chars = re.findall(r"[\u4e00-\u9fff]", text)
    english_words = re.findall(r"[a-zA-Z]+", text.lower())
    return chinese_chars + english_words


def _ngram_counts(tokens: List[str], n: int = 2) -> Counter:
    return Counter(tuple(tokens[i : i + n]) for i in range(len(tokens) - n + 1))


def redundancy_score(text: str) -> float:
    toks = _tokens(text)
    if len(toks) < 10:
        return 1.0

    bigrams = _ngram_counts(toks, 2)
    total = max(1, sum(bigrams.values()))
    repeats = sum(c for c in bigrams.values() if c > 1)
    return max(0.0, 1.0 - repeats / total)


def relevance_score(prompt: str, report: str) -> float:
    prompt_tokens = set(_tokens(prompt))
    report_tokens = set(_tokens(report))
    if not prompt_tokens:
        return 1.0

    overlap = len(prompt_tokens & report_tokens) / len(prompt_tokens)
    return min(1.0, 0.3 + 0.7 * overlap)


def completeness_score(report: str) -> float:
    lines = report.splitlines()
    sections = sum(1 for line in lines if line.strip().startswith("##"))

    if sections >= 4:
        return 1.0
    if sections >= 2:
        return 0.7
    if sections >= 1:
        return 0.4
    return 0.2


def length_fit_score(report: str, target_words: int) -> float:
    tokens = _tokens(report)
    actual_count = len(tokens)
    if actual_count == 0:
        return 0.0

    ratio = actual_count / max(1, target_words)
    if 0.5 <= ratio <= 1.5:
        return 1.0 - abs(ratio - 1.0) * 0.5
    if ratio < 0.5:
        return ratio * 2.0 * 0.75
    return max(0.1, 1.0 / (ratio * 0.8))


def structure_score(report: str, prefer_bullets: bool) -> float:
    lines = report.splitlines()
    has_bullets = any(line.strip().startswith(("-", "*")) for line in lines)
    has_paragraphs = any(
        len(line.strip()) > 0 and not line.strip().startswith(("-", "*", "#"))
        for line in lines
    )
    has_headers = any(line.strip().startswith("#") for line in lines)

    base_score = 0.8 if has_headers else 0.3
    if prefer_bullets:
        return base_score + (0.2 if has_bullets else 0.0)
    return base_score + (0.2 if has_paragraphs else 0.0)


def overall_score(
    source: str, summary: str, target_words: int, prefer_bullets: bool
) -> Dict[str, float]:
    r = redundancy_score(summary)
    rel = relevance_score(source, summary)
    comp = completeness_score(summary)
    l = length_fit_score(summary, target_words)
    s = structure_score(summary, prefer_bullets)

    total = 0.2 * r + 0.3 * rel + 0.25 * comp + 0.15 * l + 0.1 * s

    return {
        "redundancy": r,
        "relevance": rel,
        "completeness": comp,
        "length_fit": l,
        "structure": s,
        "total": total,
    }
