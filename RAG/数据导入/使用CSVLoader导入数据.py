from langchain_community.document_loaders import CSVLoader
import os

# 使用绝对路径
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
csv_path = os.path.join(base_dir, "data", "黑悟空", "黑神话悟空.csv")

# 方式1：基础用法
loader = CSVLoader(csv_path, encoding="utf-8")

data=loader.load()

for record in data[:2]:
    print(record)


# ====== 使用 csv_args 自定义 CSV 解析配置 ======
import os

# 使用绝对路径
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
file_path = os.path.join(base_dir, "data", "黑悟空", "黑神话悟空.csv")

# 使用 csv_args 参数自定义 CSV 解析
loader_custom = CSVLoader(
    file_path=file_path,
    encoding="utf-8",
    csv_args={
        "delimiter": ",",
        "quotechar": '"',
        "fieldnames": ["种类", "名称", "说明", "等级"],
    },
)

data_custom = loader_custom.load()

print("\n" + "="*60)
print("使用 csv_args 自定义配置加载的 CSV 数据:")
print("="*60)
for record in data_custom[:2]:
    print(record)
