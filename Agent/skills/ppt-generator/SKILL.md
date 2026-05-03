---
name: ppt-generator
description: 根据用户主题、受众和时长，生成结构化的演示文稿方案（页级大纲、每页要点、讲述备注、视觉建议），并输出机器可读 JSON。用于汇报准备、培训课件、路演材料、项目复盘、方案提案等 PPT 生产场景。
---

# PPT 生成技能

将一个主题快速转换为可执行的 PPT 页级方案。

## 工作流

1. 阅读 `references/ppt_playbook.md` 的编排规则。
2. 明确输入参数：主题、受众、时长、风格。
3. 生成页级结构：封面、目录、主体、结论、行动项。
4. 用 `scripts/generate_ppt_outline.py` 产出稳定 JSON。
5. 输出摘要和结果文件路径。

## 输入参数

- `topic`：演示主题（必填）
- `audience`：受众类型（管理层/客户/技术团队/通用）
- `duration_minutes`：演讲时长（默认 15）
- `tone`：表达风格（专业/说服/教学/复盘）
- `language`：`zh` 或 `en`（默认 `zh`）

## 输出 Schema

- `deck_title`
- `subtitle`
- `audience`
- `duration_minutes`
- `slides`: 数组，每页包含：
  - `slide_no`
  - `slide_title`
  - `objective`
  - `bullet_points`
  - `speaker_notes`
  - `visual_suggestion`

## 资源

- 规则：`references/ppt_playbook.md`
- 脚本：`scripts/generate_ppt_outline.py`
- 模板：`assets/ppt_outline_template.json`
