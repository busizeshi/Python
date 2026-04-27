import re

markdown_path = "../data/黑悟空/黑悟空版本介绍.md"

# 读取 Markdown 文件
with open(markdown_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 解析标题结构
title_pattern = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
matches = title_pattern.finditer(content)

print(f'📄 文件: {markdown_path}\n')
print(f'📑 文档结构:\n')
print('=' * 80)

for match in matches:
    level = len(match.group(1))  # # 的数量
    title = match.group(2).strip()
    indent = '  ' * (level - 1)  # 根据层级缩进
    print(f'{indent}{"#" * level} {title}')

print('=' * 80)

# 也可以获取完整的文本内容（不含 Markdown 标记）
print('\n📝 完整内容（前500字符）:\n')
# 移除 Markdown 标题标记
clean_text = re.sub(r'^#{1,6}\s+', '', content, flags=re.MULTILINE)
print(clean_text[:500])
if len(clean_text) > 500:
    print(f'\n... (总长度: {len(clean_text)} 字符)')
