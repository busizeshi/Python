#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
将 Markdown 文件转换为 PDF

依赖安装：
pip install markdown weasyprint

使用方式：
python md_to_pdf.py input.md output.pdf
"""

import sys
from pathlib import Path
import markdown
from weasyprint import HTML, CSS


def markdown_to_pdf(md_file, pdf_file):
    # 读取 markdown 内容
    text = Path(md_file).read_text(encoding="utf-8")

    # Markdown 转 HTML
    html_body = markdown.markdown(
        text,
        extensions=[
            "extra",
            "tables",
            "toc",
            "fenced_code",
            "codehilite"
        ]
    )

    # 拼接完整 HTML
    html = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{
                font-family: "Microsoft YaHei", "SimSun", sans-serif;
                margin: 40px;
                line-height: 1.8;
                font-size: 14px;
            }}
            h1, h2, h3 {{
                color: #222;
            }}
            code {{
                background: #f4f4f4;
                padding: 2px 4px;
                border-radius: 4px;
            }}
            pre {{
                background: #f4f4f4;
                padding: 12px;
                overflow-x: auto;
                border-radius: 6px;
            }}
            table {{
                border-collapse: collapse;
                width: 100%;
                margin: 12px 0;
            }}
            th, td {{
                border: 1px solid #ccc;
                padding: 8px;
                text-align: left;
            }}
            blockquote {{
                color: #666;
                border-left: 4px solid #ccc;
                padding-left: 12px;
                margin-left: 0;
            }}
        </style>
    </head>
    <body>
        {html_body}
    </body>
    </html>
    """

    # 输出 PDF
    HTML(string=html).write_pdf(pdf_file)
    print(f"已生成 PDF: {pdf_file}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("用法: python md_to_pdf.py input.md output.pdf")
        sys.exit(1)

    md_input = "D:\\dev\\Java\\Work\\slcp-demo\\src\\main\\docs\\print_api.md"
    pdf_output = "D:\\dev\\Java\\Work\\slcp-demo\\src\\main\\docs\\print_api.pdf"

    markdown_to_pdf(md_input, pdf_output)