# fix_838hq.py
# 强制更新 838HQ 的图片数据

from db_config import get_db_connection
import os

# 请修改为你的 838HQ.jpg 实际路径
IMAGE_PATH = r"C:\Users\李子珺\Desktop\学习\220613303_内裤款式图数据库系统设计与实现\论文归档\数据资料\企业款式图\内裤 838HQ.jpg"

def fix_838hq():
    if not os.path.exists(IMAGE_PATH):
        print(f"❌ 文件不存在: {IMAGE_PATH}")
        return

    with open(IMAGE_PATH, 'rb') as f:
        image_data = f.read()

    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 先检查这条记录是否存在
    cursor.execute("SELECT image_id FROM underwear_garments WHERE image_name LIKE '%838HQ%'")
    row = cursor.fetchone()
    
    if row:
        # 更新已有记录
        cursor.execute("""
            UPDATE underwear_garments 
            SET image_data = %s, image_size = %s 
            WHERE image_id = %s
        """, (image_data, len(image_data), row['image_id']))
        print(f"✅ 已更新 838HQ (image_id={row['image_id']})")
    else:
        # 如果不存在，插入新记录
        cursor.execute("""
            INSERT INTO underwear_garments (image_code, image_name, image_data, image_type, image_size, description)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, ('U_838HQ', '内裤 838HQ', image_data, 'image/jpeg', len(image_data), '手动导入'))
        print("✅ 已插入 838HQ")
    
    conn.commit()
    cursor.close()
    conn.close()

if __name__ == '__main__':
    fix_838hq()