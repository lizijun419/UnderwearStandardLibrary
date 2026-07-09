# check_bra_templates.py
# 查看 bra_templates 表中的现有数据

from db_config import get_db_connection

conn = get_db_connection()
cursor = conn.cursor()

cursor.execute("SELECT * FROM bra_templates;")
data = cursor.fetchall()

print(f"📊 bra_templates 表中共有 {len(data)} 条记录\n")
for item in data:
    print(f"ID: {item['template_id']}")
    print(f"  罩杯类型: {item['cup_type']}")
    print(f"  侧比类型: {item['side_ratio_type']}")
    print(f"  前中宽度: {item['center_width']}")
    print(f"  模板AI路径: {item['template_ai_path']}")
    print(f"  规格AI路径: {item['annotation_ai_path']}")
    print("-" * 40)

cursor.close()
conn.close()