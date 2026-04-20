# -*- coding: utf-8 -*-
"""
功能：
1. 连接 MySQL 数据库
2. 执行指定 SQL
3. 查询结果导出 Excel

依赖安装：
pip install pandas pymysql openpyxl
"""

import pandas as pd
import pymysql
from datetime import datetime

# =============================
# 数据库配置（改成你的实际信息）
# =============================
DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "123456",
    "database": "your_database",
    "charset": "utf8mb4"
}

# =============================
# SQL 查询
# =============================
sql = """
select c.count_date          as '统计日期',
       building.pos_name     as '楼',
       floor.pos_name        as '层',
       zone.pos_name         as '区域',
       n.alias_name          as '网络名称',
       ng.group_name         as '组名称',
       u.dev_id              as '设备Mac地址',
       u.dev_name            as '设备名称',
       i.prod_type_code      as '设备类型编码',
       c.switch_counts       as '开关次数',
       c.switch_open_counts  as '开次数',
       c.switch_close_counts as '关次数',
       c.auto_counts         as '自动次数',
       c.auto_open_counts    as '自动开次数',
       c.auto_close_counts   as '自动关次数',
       c.run_seconds / 3600  as '运行时长(小时)'
from dev_run_time_count c
         inner join dev_useable_ppe u on c.dev_id = u.dev_id
         inner join dev_inherent_ppe i on u.dev_id = i.dev_id
         inner join dev_group g on u.dev_id = g.dev_id
         inner join net_ble_mesh_group ng on u.net_id = ng.net_id and g.group_id = ng.group_id
         inner join net_ble_mesh n on u.net_id = n.net_id
         left join org_pos zone on n.pos_id = zone.id
         left join org_pos floor on zone.father = floor.id
         left join org_pos building on floor.father = building.id
where c.org_id = '9881e523-5a80-409f-8cd7-7da899516ade'
  and c.count_date >= '2026-03-19'
  and c.count_date <= '2026-04-19'
  and c.prod_type_code in (
      'airConditionerPanel',
      'airConditioner',
      'airConditionerPanelFine',
      'switch'
  );
"""

# =============================
# 导出 Excel
# =============================
def export_excel():
    conn = None
    try:
        # 连接数据库
        conn = pymysql.connect(**DB_CONFIG)

        # 查询数据
        df = pd.read_sql(sql, conn)

        # 文件名
        file_name = f"设备运行统计_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

        # 导出 Excel
        with pd.ExcelWriter(file_name, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="统计数据")

            # 自动列宽
            worksheet = writer.sheets["统计数据"]
            for col in worksheet.columns:
                max_length = 0
                col_letter = col[0].column_letter

                for cell in col:
                    try:
                        if cell.value:
                            max_length = max(max_length, len(str(cell.value)))
                    except:
                        pass

                worksheet.column_dimensions[col_letter].width = max_length + 2

        print(f"导出成功：{file_name}")

    except Exception as e:
        print("执行失败：", e)

    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    export_excel()