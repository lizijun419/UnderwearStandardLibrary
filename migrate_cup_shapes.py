# migrate_cup_shapes.py
# 将所有罩杯形状PNG导入到 bra_cup_shapes 表

import os
import re
from db_config import get_db_connection

CUP_IMG_ROOT = r"C:\Users\李子珺\Desktop\学习\220613207刘凝\220613207刘凝\答辩文件\数据库源文件\bradata\bradata\bin\Debug\罩杯形状"

PREFIX_TO_CUP_TYPE = {
    'A': '3/4罩杯',
    'B': '1/2罩杯',
    'C': '全罩杯',
    'D': '背心',
    'E': '抹胸',
    'F': '三角杯',
}

def migrate():
    if not os.path.exists(CUP_IMG_ROOT):
        print(f"❌ 路径不存在: {CUP_IMG_ROOT}")
        return

    png_files = [f for f in os.listdir(CUP_IMG_ROOT) if f.lower().endswith('.png')]
    print(f"📁 找到 {len(png_files)} 个PNG文件")

    conn = get_db_connection()
    cursor = conn.cursor()

    success_count = 0
    for filename in png_files:
        name_without_ext = os.path.splitext(filename)[0]
        match = re.match(r'^([A-Z])(\d{2})$', name_without_ext)
        if not match:
            print(f"⚠️ 跳过非标准命名: {filename}")
            continue

        prefix = match.group(1)
        code = match.group(0)
        cup_type = PREFIX_TO_CUP_TYPE.get(prefix)

        if not cup_type:
            print(f"⚠️ 未知前缀: {prefix} (文件: {filename})")
            continue

        file_path = os.path.join(CUP_IMG_ROOT, filename)

        try:
            cursor.execute("""
                INSERT INTO bra_cup_shapes (cup_type, cup_shape_code, cup_shape_img_path, remark)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                    cup_shape_img_path = %s,
                    remark = CONCAT(IFNULL(remark, ''), '')
            """, (cup_type, code, file_path, f"自动导入: {filename}", file_path))
            success_count += 1
            print(f"✅ {code} → {cup_type}")
        except Exception as e:
            print(f"❌ 插入失败 {filename}: {e}")

    conn.commit()
    cursor.close()
    conn.close()
    print(f"\n🎉 导入完成！成功导入 {success_count} 条记录。")

if __name__ == '__main__':
    migrate()