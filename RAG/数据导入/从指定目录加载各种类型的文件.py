# pip install python-magic-bin

from langchain_community.document_loaders import DirectoryLoader

# loader=DirectoryLoader("../data/黑悟空")

# 通过指定文件路径和文件匹配模式加载特定文件
loader=DirectoryLoader("../data/黑悟空", glob="**/*.txt")

# 查看加载进度
# loader=DirectoryLoader("../data/黑悟空", show_progress=True)

# 使用多线程加载文档
# loader=DirectoryLoader("../data/黑悟空", use_multithreading=True)


docs = loader.load()

print(f'文档数目:{len(docs)}')