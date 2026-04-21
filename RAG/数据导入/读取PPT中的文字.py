import sys
import io
import os
from langchain_core.documents import Document
from unstructured.partition.ppt import partition_ppt

# 修复 Windows 下 unstructured 的编码问题
if sys.platform == 'win32':
    # 设置环境变量，让子进程使用 UTF-8
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    # 设置标准输出编码
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 使用绝对路径
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ppt_path = os.path.join(base_dir, "data", "黑悟空", "黑神话悟空.pptx")

ppt_elements=partition_ppt(filename=ppt_path)

for element in ppt_elements:
    print(element.text)

documents=[Document(page_content=element.text,metadata={"source":ppt_path}) for element in ppt_elements]

print(documents[0:3])
