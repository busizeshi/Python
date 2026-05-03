import argparse
import json
from pathlib import Path


def slide_count_by_duration(duration: int) -> int:
    if duration <= 10:
        return 7
    if duration <= 20:
        return 9
    return 14


def audience_focus(audience: str) -> str:
    mapping = {
        "管理层": "业务价值、风险控制、投入产出",
        "客户": "痛点匹配、方案差异化、落地收益",
        "技术团队": "架构设计、技术约束、实施细节",
        "通用": "背景、方案、行动平衡",
    }
    return mapping.get(audience, mapping["通用"])


def make_slide(no: int, title: str, objective: str, focus: str) -> dict:
    return {
        "slide_no": no,
        "slide_title": title,
        "objective": objective,
        "bullet_points": [
            f"核心信息 {no}.1",
            f"核心信息 {no}.2",
            f"核心信息 {no}.3",
        ],
        "speaker_notes": f"围绕{objective}展开，重点强调：{focus}。",
        "visual_suggestion": "优先使用对比图、流程图或时间线增强理解。",
    }


def generate_outline(topic: str, audience: str, duration: int, tone: str, language: str) -> dict:
    total = slide_count_by_duration(duration)
    focus = audience_focus(audience)

    base_titles = [
        "封面",
        "背景与问题",
        "目标与成功标准",
        "核心方案一",
        "核心方案二",
        "实施路径",
        "风险与应对",
        "结论",
        "行动项",
    ]
    if total > len(base_titles):
        for i in range(len(base_titles) + 1, total + 1):
            base_titles.append(f"补充页{i}")
    else:
        base_titles = base_titles[:total]

    slides = []
    for idx, title in enumerate(base_titles, start=1):
        objective = f"说明{title}并支撑主题“{topic}”"
        slides.append(make_slide(idx, title, objective, focus))

    return {
        "deck_title": topic,
        "subtitle": f"面向{audience}的{tone}型演示",
        "audience": audience,
        "duration_minutes": duration,
        "tone": tone,
        "language": language,
        "slides": slides,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input",default="D:\\dev\\Python\\Agent\\skills\\ppt-generator\\examples\\request_sample.json", help="JSON 输入路径")
    parser.add_argument("--output",default="D:\\dev\\Python\\Agent\\skills\\ppt-generator\\examples\\outline_output.json", help="JSON 输出路径")
    args = parser.parse_args()

    req = json.loads(Path(args.input).read_text(encoding="utf-8-sig"))
    topic = req["topic"]
    audience = req.get("audience", "通用")
    duration = int(req.get("duration_minutes", 15))
    tone = req.get("tone", "专业")
    language = req.get("language", "zh")

    out = generate_outline(topic, audience, duration, tone, language)
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Generated {len(out['slides'])} slides -> {out_path}")


if __name__ == "__main__":
    main()

