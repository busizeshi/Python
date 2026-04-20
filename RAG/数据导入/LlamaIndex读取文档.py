from llama_index.core import SimpleDirectoryReader

dir_reader = SimpleDirectoryReader("../data/黑悟空")

documents = dir_reader.load_data()

print(f'文档数量：{len(documents)}')

print(documents[1])

print('---'*20)

# 读取目录中的特定文件
specific_file_reader = SimpleDirectoryReader(input_files=["../data/黑悟空/设定.txt"])
specific_file_documents = specific_file_reader.load_data()

print(specific_file_documents[0])

