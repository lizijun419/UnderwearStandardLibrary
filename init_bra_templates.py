# init_bra_templates.py
# 一键清空并重新初始化 bra_templates 表（13条模板记录）

from db_config import get_db_connection

def init_bra_templates():
    conn = get_db_connection()
    cursor = conn.cursor()

    print("🧹 正在清空 bra_templates 表...")
    cursor.execute("TRUNCATE TABLE bra_templates;")
    conn.commit()
    print("✅ 清空完成！")

    # 13条完整模板记录
    templates = [
        # 1/2罩杯（4种）
        ('1/2罩杯', '常规侧比', '无', 'B01'),
        ('1/2罩杯', '常规侧比', '有', 'B01'),
        ('1/2罩杯', '低侧比', '无', 'B01'),
        ('1/2罩杯', '低侧比', '有', 'B01'),
        # 3/4罩杯（4种）
        ('3/4罩杯', '常规侧比', '无', 'A01'),
        ('3/4罩杯', '常规侧比', '有', 'A01'),
        ('3/4罩杯', '低侧比', '无', 'A01'),
        ('3/4罩杯', '低侧比', '有', 'A01'),
        # 全罩杯（2种）
        ('全罩杯', '常规侧比', '无', 'C01'),
        ('全罩杯', '高侧比', '无', 'C01'),
        # 特殊款式（3种）
        ('背心', None, None, 'D01'),
        ('抹胸', None, None, 'E01'),
        ('三角杯', None, None, 'F01'),
    ]

    print("📝 正在插入 13 条模板记录...")
    for idx, (cup, side, center, shape) in enumerate(templates, 1):
        cursor.execute("""
            INSERT INTO bra_templates (cup_type, side_ratio_type, center_width, cup_shape_code)
            VALUES (%s, %s, %s, %s)
        """, (cup, side, center, shape))
        conn.commit()
        print(f"  ✅ 已插入第 {idx} 条: {cup} | {side} | {center} | {shape}")

    cursor.close()
    conn.close()
    print("\n🎉 初始化完成！bra_templates 表现在包含 13 条记录。")
    print("现在可以重启 Flask，然后测试文胸设计功能了！")

if __name__ == '__main__':
    init_bra_templates()