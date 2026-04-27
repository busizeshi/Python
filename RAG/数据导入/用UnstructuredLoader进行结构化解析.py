import os
import sys

# 设置 NLTK 数据路径为虚拟环境中的本地路径
venv_nltk_data = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.venv', 'nltk_data')
os.environ['NLTK_DATA'] = venv_nltk_data

from langchain_unstructured import UnstructuredLoader
import nltk

# 确保 NLTK 使用本地数据
if not os.path.exists(venv_nltk_data):
    os.makedirs(venv_nltk_data, exist_ok=True)
nltk.data.path.insert(0, venv_nltk_data)

# 手动下载 NLTK 数据包（使用新版命名规范）
required_packages = ['punkt', 'punkt_tab', 'averaged_perceptron_tagger', 'averaged_perceptron_tagger_eng']
for package in required_packages:
    try:
        # 适配不同包的查找路径
        if 'punkt' in package:
            nltk.data.find(f'tokenizers/{package}')
        elif 'tagger' in package:
            nltk.data.find(f'taggers/{package}')
        print(f"✓ 已存在: {package}")
    except LookupError:
        print(f"↓ 正在下载: {package}")
        try:
            nltk.download(package, download_dir=venv_nltk_data, quiet=True)
        except Exception as e:
            print(f"⚠ 自动下载失败: {e}")
            print(f"请手动下载 NLTK 数据包到: {venv_nltk_data}")
            sys.exit(1)

# 禁用 unstructured 的自动下载（防止重复下载导致 403 错误）
import unstructured.nlp.tokenize as unstructured_tokenize
unstructured_tokenize._download_nltk_packages_if_not_present = lambda: None

# 使用绝对路径
current_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(current_dir, "..", "data", "山西文旅", "云冈石窟-ch.pdf")

loader = UnstructuredLoader(
    file_path=file_path,
    strategy="hi_res",
    # partition_via_api=True,  # 如果调用的是本地Unstructured工具， 注释掉本行和下一行代码
    # coordinates=True,  # 通过API调用Unstructured工具， 并返回元素坐标
)
docs = []
for doc in loader.lazy_load():
    docs.append(doc)
    print(doc)
