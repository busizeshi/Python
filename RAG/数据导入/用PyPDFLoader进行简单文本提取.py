from langchain_community.document_loaders import PyPDFLoader

file_path="../data/黑悟空/黑神话悟空.pdf"

loader=PyPDFLoader(file_path)

pages=loader.load()

print(f"加载了{len(pages)}页PDF文档")

for page in pages:
    print(page.page_content)