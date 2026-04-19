# -*- coding: utf-8 -*-
"""
Python连接达梦数据库（DM8），全量查询 delivery_point 表数据
"""

import dmPython

# =============================
# 数据库连接配置
# =============================
conn = dmPython.connect(
    user="SYSDBA",
    password="SYSDBa001.",
    server="192.168.8.36",
    port=5236
)

cursor = conn.cursor()

# 切换schema
cursor.execute("SET SCHEMA SPD_TEST_SLCP")

# =============================
# 全量查询
# =============================
cursor.execute("SELECT * FROM delivery_point")

rows = cursor.fetchall()

# 获取列名
columns = [desc[0] for desc in cursor.description]
print("\n列名:", columns)
print("\n查询结果（共{}条记录）:".format(len(rows)))
for r in rows:
    print(dict(zip(columns, r)))

cursor.close()
conn.close()

print("\n执行完成")