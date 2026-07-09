import os
from db_config import get_db_connection

IMAGE_FOLDER = r"C:\Users\李子珺\Desktop\学习\220613303_内裤款式图数据库系统设计与实现\论文归档\数据资料\企业款式图"

def import_images():
    if not os.path.exists(IMAGE_FOLDER):
        print(f"❌ 文件夹不存在 -> {IMAGE_FOLDER}")
        return

    image_files = [f for f in os.listdir(IMAGE_FOLDER) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    if not image_files:
        print("❌ 没有找到任何图片")
        return

    print(f"📁 找到 {len(image_files)} 张图片")

    conn = get_db_connection()
    cursor = conn.cursor()

    # 清空旧数据（DELETE + COMMIT）
    cursor.execute("DELETE FROM underwear_garments;")
    conn.commit()
    print("🧹 已清空旧数据")

    success_count = 0
    for idx, filename in enumerate(image_files):
        try:
            file_path = os.path.join(IMAGE_FOLDER, filename)
            with open(file_path, 'rb') as f:
                image_data = f.read()

            if len(image_data) == 0:
                print(f"  ⚠️ 跳过空文件: {filename}")
                continue

            name_without_ext = os.path.splitext(filename)[0]
            image_code = f"U_{idx+1:03d}"
            image_type = 'image/jpeg' if filename.lower().endswith(('.jpg','.jpeg')) else 'image/png'

            cursor.execute("""
                INSERT INTO underwear_garments 
                (image_code, image_name, image_data, image_type, image_size, description, upload_user_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (image_code, name_without_ext, image_data, image_type, len(image_data), f"批量导入: {filename}", 1))
            conn.commit()
            success_count += 1
            print(f"  ✅ 已导入: {filename}")

        except Exception as e:
            print(f"  ❌ 导入失败: {filename} -> {e}")
            conn.rollback()

    cursor.close()
    conn.close()
    print(f"\n🎉 导入完成！成功导入 {success_count} 张图片。")

if __name__ == '__main__':
    import_images()