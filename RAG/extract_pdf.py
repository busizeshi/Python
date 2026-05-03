from PyPDF2 import PdfReader, PdfWriter

def extract_pages(input_pdf, output_pdf, start_page, end_page):
    reader = PdfReader(input_pdf)
    writer = PdfWriter()

    # 注意：索引从 0 开始
    for page_num in range(start_page - 1, end_page):
        writer.add_page(reader.pages[page_num])

    with open(output_pdf, "wb") as f:
        writer.write(f)

# 使用示例：提取第 1 到 第 2 页
extract_pages("C:\\Users\\13127\\Desktop\\share\\RAG实战课 9787115671851_000020296367_fz.pdf", "extracted.pdf", 328, 349)