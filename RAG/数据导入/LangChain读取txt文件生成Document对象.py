from langchain_community.document_loaders import TextLoader

loader = TextLoader("../data/黑悟空/设定.txt",encoding="utf-8")

documents = loader.load()

print(documents)