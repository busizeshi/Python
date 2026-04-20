from llama_index.readers.database import DatabaseReader

reader = DatabaseReader(
    scheme="mysql",
    host="115.190.125.94",
    port=3306,
    user="root",
    password="root",
    dbname="jwd_ai"
)

query="select * from users"

documents=reader.load_data(query)

print(f"从数据库加载的文档数： {len(documents)}")
print(documents)