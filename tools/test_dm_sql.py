# -*- coding: utf-8 -*-
"""
Python连接达梦数据库（DM8），执行：
1. 建表 delivery_point
2. 添加注释
3. 插入1条办公室记录
4. 插入3条卡位记录

使用前先安装驱动：
pip install dmPython
"""

import dmPython
import uuid

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

# 切换schema（重要）
cursor.execute("SET SCHEMA SPD_TEST_SLCP")

try:
    # =============================
    # 建表SQL
    # =============================
    create_sql = """
    CREATE TABLE delivery_point (
        id                  VARCHAR2(64)    NOT NULL,
        point_code          VARCHAR2(64)    NOT NULL,
        point_name          VARCHAR2(128),
        floor_name          VARCHAR2(32),
        point_type          VARCHAR2(64),
        area_name           VARCHAR2(64),
        x                   DECIMAL(16,6)   DEFAULT 0,
        y                   DECIMAL(16,6)   DEFAULT 0,
        z                   DECIMAL(16,6)   DEFAULT 0,
        user_id             VARCHAR2(64),
        robot_mapping_position VARCHAR2(128),
        enabled             INT             DEFAULT 1,
        create_by           VARCHAR2(64),
        create_date         TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,
        update_by           VARCHAR2(64),
        update_date         TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (id)
    )
    """
    cursor.execute(create_sql)
    print("表 delivery_point 创建成功")

except Exception as e:
    print("建表可能已存在：", e)

# =============================
# 注释SQL
# =============================
comment_sqls = [
    "COMMENT ON TABLE delivery_point IS '配送点位信息表'",
    "COMMENT ON COLUMN delivery_point.id IS '主键ID'",
    "COMMENT ON COLUMN delivery_point.point_code IS '点位编码'",
    "COMMENT ON COLUMN delivery_point.point_name IS '点位显示名称'",
    "COMMENT ON COLUMN delivery_point.floor_name IS '楼层名称(如26F)'",
    "COMMENT ON COLUMN delivery_point.point_type IS '点位类别编码(如PERSON-人员)'",
    "COMMENT ON COLUMN delivery_point.area_name IS '所属区域编码(如OFFICE-办公室,CUBICLE-卡位)'",
    "COMMENT ON COLUMN delivery_point.x IS 'CAD坐标X'",
    "COMMENT ON COLUMN delivery_point.y IS 'CAD坐标Y'",
    "COMMENT ON COLUMN delivery_point.z IS 'CAD坐标Z(默认0)'",
    "COMMENT ON COLUMN delivery_point.user_id IS '点位归属用户ID'",
    "COMMENT ON COLUMN delivery_point.robot_mapping_position IS '机器人映射位置'",
    "COMMENT ON COLUMN delivery_point.enabled IS '启用状态(1启用/0停用)'",
    "COMMENT ON COLUMN delivery_point.create_by IS '创建人'",
    "COMMENT ON COLUMN delivery_point.create_date IS '创建日期'",
    "COMMENT ON COLUMN delivery_point.update_by IS '更新人'",
    "COMMENT ON COLUMN delivery_point.update_date IS '更新日期'"
]

for sql in comment_sqls:
    try:
        cursor.execute(sql)
    except:
        pass

print("注释执行完成")

# =============================
# 插入数据
# =============================
insert_sql = """
INSERT INTO delivery_point (
    id, point_code, point_name, area_name,
    enabled, create_by, update_by
) VALUES (?, ?, ?, ?, 1, 'python', 'python')
"""

data_list = [
    # 办公室
    (str(uuid.uuid4()), "2214", "2214", "OFFICE"),

    # 卡位
    (str(uuid.uuid4()), "gaopeng", "gaopeng", "CUBICLE"),
    (str(uuid.uuid4()), "test_01", "test_01", "CUBICLE"),
    (str(uuid.uuid4()), "litao", "litao", "CUBICLE"),
]

for row in data_list:
    cursor.execute(insert_sql, row)

conn.commit()

print("数据插入成功，共4条记录")

# =============================
# 查询验证
# =============================
cursor.execute("""
SELECT point_code, point_name, area_name
FROM delivery_point
""")

rows = cursor.fetchall()

for r in rows:
    print(r)

cursor.close()
conn.close()

print("执行完成")