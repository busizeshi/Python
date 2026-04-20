from langchain_core.documents import Document

documents = [
    Document(page_content="This is the first document.", metadata={"source": "场景一"}),
    Document(page_content="This is the second document.", metadata={"source": "场景二"}),
]

for document in documents:
    print(document)