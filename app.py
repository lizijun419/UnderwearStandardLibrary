# app.py - 完整版（兼容本地 + Render 云端）

from flask import Flask, jsonify, render_template, send_file, request, make_response
from flask_cors import CORS
from db_config import get_db_connection
import io
import os
import re
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

# ==================== 路径配置（兼容本地 + Render） ====================

# 本地路径（你的原始路径）
# ==================== 路径配置（兼容本地 + Render） ====================
import os

# 本地路径（你的原始路径）
LOCAL_BRA_AI_ROOT = r"C:\Users\李子珺\Desktop\学习\220613207刘凝\220613207刘凝\答辩文件\数据库源文件\bradata\bradata\bin\Debug\模板-款式图"
LOCAL_BRA_ANNOTATION_ROOT = r"C:\Users\李子珺\Desktop\学习\220613207刘凝\220613207刘凝\答辩文件\数据库源文件\bradata\bradata\bin\Debug\模板-尺寸规格"
LOCAL_BRA_CUP_ROOT = r"C:\Users\李子珺\Desktop\学习\220613207刘凝\220613207刘凝\答辩文件\数据库源文件\bradata\bradata\bin\Debug\罩杯形状"
LOCAL_AI_ROOT = r"C:\Users\李子珺\Desktop\学习\220613303_内裤款式图数据库系统设计与实现\论文归档\数据资料\企业款式图"

# 云端路径（Render 挂载磁盘后使用）—— 改为相对路径，不依赖 /app
CLOUD_BRA_AI_ROOT = './uploads/templates'      # 相对于当前工作目录
CLOUD_BRA_ANNOTATION_ROOT = './uploads/annotations'
CLOUD_BRA_CUP_ROOT = './uploads/cup_shapes'
CLOUD_AI_ROOT = './uploads/underwear_ai'

# 根据环境自动选择路径
def get_path(local_path, cloud_path):
    """如果设置了 DATABASE_URL（云端），使用云端路径；否则使用本地路径"""
    if os.environ.get('DATABASE_URL'):
        return cloud_path
    return local_path

BRA_AI_ROOT = get_path(LOCAL_BRA_AI_ROOT, CLOUD_BRA_AI_ROOT)
BRA_ANNOTATION_ROOT = get_path(LOCAL_BRA_ANNOTATION_ROOT, CLOUD_BRA_ANNOTATION_ROOT)
BRA_CUP_ROOT = get_path(LOCAL_BRA_CUP_ROOT, CLOUD_BRA_CUP_ROOT)
AI_ROOT = get_path(LOCAL_AI_ROOT, CLOUD_AI_ROOT)

# 上传文件夹（始终使用相对路径）
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')

# 确保上传目录存在（不会创建 /app）
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename, allowed_set):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_set


# ==================== 分类映射 ====================
UNDERWEAR_CATEGORY_MAP = {
    '内裤 838HQ': '丁字裤',
    '内裤 TFGETGLC03': '丁字裤',
    '内裤 TFDTGLC18': '丁字裤',
    '内裤 TFDBXMF07': '平角裤',
    '内裤 TFEBXMS04': '平角裤',
    '内裤 TFDBXMF12': '平角裤',
    '内裤 TFGEBXLC07': '平角裤',
    '内裤 TFDBZLC05': '三角裤',
    '内裤 TFDTNMF20': '细带三角裤',
    '内裤 TFGETNLC05': '细带三角裤',
    '内裤 TFGTNST03': '细带三角裤',
    '内裤 TFNWTNCT06': '细带三角裤',
}

OTHER_CATEGORY_MAP = {
    '吊带裙': '吊裙',
    '吊衣': '吊衣',
    '睡衣': '睡衣',
    '泳衣': '泳衣',
    '背心': '背心',
    '睡裤': '睡裤',
    '半身裙': '半身裙',
    '吊带袜': '吊带袜',
    '连体衣': '连体衣',
    '塑身衣': '塑身衣',
}

VALID_UNDERWEAR_CATEGORIES = ['丁字裤', '平角裤', '三角裤', '细带三角裤']
VALID_OTHER_CATEGORIES = ['吊裙', '吊衣', '睡衣', '泳衣', '背心', '睡裤', '半身裙', '吊带袜', '连体衣', '塑身衣', '其他']


def parse_category_from_description(description):
    """从 description 字段解析分类"""
    if not description:
        return None
    match = re.search(r'分类:\s*([^\s|]+)', description)
    if match:
        return match.group(1)
    return None


# ==================== 文胸映射 ====================
CUP_FILE_MAP = {
    '3/4罩杯': '34罩杯',
    '1/2罩杯': '12罩杯',
    '全罩杯': '全罩杯',
    '三角杯': '三角杯',
    '背心': '背心',
    '抹胸': '抹胸'
}

CENTER_FILE_MAP = {
    '有前中宽': '前中宽',
    '无前中宽': '无前中宽',
    '有': '前中宽',
    '无': '无前中宽'
}

CENTER_DISPLAY_MAP = {
    '有前中宽': '有前中宽',
    '无前中宽': '无前中宽',
    '有': '有',
    '无': '无'
}


# ==================== 首页 ====================
@app.route('/')
def home():
    return render_template('index.html')


# ==================== 测试数据库 ====================
@app.route('/test_db')
def test_db_html():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES;" if os.environ.get('DATABASE_URL') is None else "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")
        tables = cursor.fetchall()
        conn.close()
        table_list = "".join([f"<li>{list(t.values())[0]}</li>" for t in tables])
        return f"""
        <h2 style="color:green;">✅ 数据库连接成功！</h2>
        <p>共找到 <strong>{len(tables)}</strong> 张表：</p>
        <ul style="font-size:18px; line-height:1.8;">
            {table_list}
        </ul>
        <p><a href="/">← 返回首页</a></p>
        """
    except Exception as e:
        return f"""
        <h2 style="color:red;">❌ 数据库连接失败</h2>
        <p>错误信息：{str(e)}</p>
        <p><a href="/">← 返回首页</a></p>
        """


@app.route('/api/test_db')
def test_db_json():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES;" if os.environ.get('DATABASE_URL') is None else "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")
        tables = cursor.fetchall()
        conn.close()
        return jsonify({
            'status': '✅ 数据库连接成功！',
            'table_count': len(tables),
            'tables': [list(t.values())[0] for t in tables]
        })
    except Exception as e:
        return jsonify({'status': '❌ 数据库连接失败', 'error': str(e)})


# ==================== 文胸API ====================

@app.route('/api/bra_cup_types')
def get_bra_cup_types():
    return jsonify({
        'status': 'success',
        'data': list(CUP_FILE_MAP.keys())
    })


@app.route('/api/bra_cup_shapes', methods=['GET'])
def get_bra_cup_shapes():
    cup_type = request.args.get('cup_type')
    if not cup_type:
        return jsonify({'status': 'error', 'error': '缺少 cup_type 参数'}), 400
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT cup_shape_code, cup_shape_img_path, remark
            FROM bra_cup_shapes 
            WHERE cup_type = %s
            ORDER BY cup_shape_code
        """, (cup_type,))
        data = cursor.fetchall()
        conn.close()

        for item in data:
            exists = os.path.exists(item['cup_shape_img_path'])
            item['exists'] = exists

        return jsonify({
            'status': 'success',
            'data': data
        })
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)})


@app.route('/api/bra_template_query', methods=['POST'])
def bra_template_query():
    try:
        data = request.json
        cup_type = data.get('cup_type')
        side_ratio_type = data.get('side_ratio_type')
        center_width = data.get('center_width')

        if not cup_type:
            return jsonify({'status': 'error', 'error': '请选择罩杯类型'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
            SELECT template_id, cup_type, side_ratio_type, center_width, 
                   cup_shape_code, template_ai_path, annotation_ai_path, remark
            FROM bra_templates 
            WHERE cup_type = %s
        """
        params = [cup_type]

        if side_ratio_type and side_ratio_type != '全部':
            sql += " AND side_ratio_type = %s"
            params.append(side_ratio_type)

        if center_width and center_width != '全部':
            db_center = '有' if center_width == '有前中宽' else '无' if center_width == '无前中宽' else center_width
            sql += " AND center_width = %s"
            params.append(db_center)

        cursor.execute(sql, params)
        result = cursor.fetchall()
        conn.close()

        for item in result:
            if item['template_ai_path']:
                item['ai_exists'] = os.path.exists(item['template_ai_path'])
            else:
                item['ai_exists'] = False
            if item['annotation_ai_path']:
                item['annotation_exists'] = os.path.exists(item['annotation_ai_path'])
            else:
                item['annotation_exists'] = False

            side = item['side_ratio_type'] or '默认侧比'
            center = item['center_width'] or '无前中宽'
            if center == '有':
                center = '有前中宽'
            elif center == '无':
                center = '无前中宽'
            item['display_name'] = f"{side} · {center}"

        return jsonify({
            'status': 'success',
            'data': result
        })

    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500


@app.route('/api/bra_cup_image/<cup_shape_code>')
def get_bra_cup_image(cup_shape_code):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT cup_shape_img_path FROM bra_cup_shapes WHERE cup_shape_code = %s", (cup_shape_code,))
        row = cursor.fetchone()
        conn.close()

        if row and os.path.exists(row['cup_shape_img_path']):
            return send_file(row['cup_shape_img_path'], mimetype='image/png')

        png_path = os.path.join(BRA_CUP_ROOT, f"{cup_shape_code}.png")
        if os.path.exists(png_path):
            return send_file(png_path, mimetype='image/png')

        return "预览图不存在", 404
    except Exception as e:
        return str(e), 500


@app.route('/api/download_bra_cup/<cup_shape_code>')
def download_bra_cup(cup_shape_code):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT cup_shape_img_path FROM bra_cup_shapes WHERE cup_shape_code = %s", (cup_shape_code,))
        row = cursor.fetchone()
        conn.close()

        if row and os.path.exists(row['cup_shape_img_path']):
            return send_file(row['cup_shape_img_path'], as_attachment=True, download_name=f"{cup_shape_code}.png")

        png_path = os.path.join(BRA_CUP_ROOT, f"{cup_shape_code}.png")
        if os.path.exists(png_path):
            return send_file(png_path, as_attachment=True, download_name=f"{cup_shape_code}.png")

        return "文件不存在", 404
    except Exception as e:
        return str(e), 500


@app.route('/api/download_bra_ai', methods=['POST'])
def download_bra_ai():
    try:
        data = request.json
        cup_type = data.get('cup_type')
        side_ratio_type = data.get('side_ratio_type')
        center_width = data.get('center_width')

        if not cup_type:
            return "请选择罩杯类型", 400

        cup_prefix = CUP_FILE_MAP.get(cup_type, cup_type)
        if cup_type in ['三角杯', '背心', '抹胸']:
            filename = f"{cup_prefix}.ai"
        else:
            parts = [cup_prefix]
            if side_ratio_type and side_ratio_type != '全部':
                parts.append(side_ratio_type)
            if center_width and center_width != '全部':
                parts.append(CENTER_FILE_MAP.get(center_width, center_width))
            filename = "-".join(parts) + ".ai"

        file_path = os.path.join(BRA_AI_ROOT, filename)

        if not os.path.exists(file_path):
            return f"文件不存在: {filename}", 404

        return send_file(file_path, as_attachment=True, download_name=filename)

    except Exception as e:
        return str(e), 500


@app.route('/api/download_bra_annotation', methods=['POST'])
def download_bra_annotation():
    try:
        data = request.json
        cup_type = data.get('cup_type')
        side_ratio_type = data.get('side_ratio_type')
        center_width = data.get('center_width')

        if not cup_type:
            return "请选择罩杯类型", 400

        cup_prefix = CUP_FILE_MAP.get(cup_type, cup_type)
        if cup_type in ['三角杯', '背心', '抹胸']:
            base_filename = f"{cup_prefix}.ai"
        else:
            parts = [cup_prefix]
            if side_ratio_type and side_ratio_type != '全部':
                parts.append(side_ratio_type)
            if center_width and center_width != '全部':
                parts.append(CENTER_FILE_MAP.get(center_width, center_width))
            base_filename = "-".join(parts) + ".ai"

        ann_filename = base_filename.replace('.ai', '-规格.ai')
        file_path = os.path.join(BRA_ANNOTATION_ROOT, ann_filename)

        if not os.path.exists(file_path):
            return f"尺寸规格文件不存在: {ann_filename}", 404

        return send_file(file_path, as_attachment=True, download_name=ann_filename)

    except Exception as e:
        return str(e), 500


# ==================== 内裤API ====================

@app.route('/api/underwear_garments')
def get_underwear_garments():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT image_id, image_code, image_name, image_type, image_size,
                   description, upload_time, view_count
            FROM underwear_garments
            ORDER BY upload_time DESC
        """)
        data = cursor.fetchall()
        conn.close()

        for item in data:
            # 从 description 解析分类（上传时写入的）
            category = parse_category_from_description(item['description'])
            if not category:
                # 兜底：用 image_name 匹配
                for key, cat in UNDERWEAR_CATEGORY_MAP.items():
                    if key in item['image_name']:
                        category = cat
                        break
                if not category:
                    for key, cat in OTHER_CATEGORY_MAP.items():
                        if key in item['image_name']:
                            category = cat
                            break
            if not category:
                category = '未分类'
            item['category'] = category

        return jsonify({'status': 'success', 'count': len(data), 'data': data})
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)})


@app.route('/api/underwear_image/<int:image_id>')
def get_underwear_image(image_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT image_data, image_type FROM underwear_garments WHERE image_id = %s", (image_id,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return "图片不存在", 404

        # 图片压缩（仅JPG）
        if 'jpeg' in row['image_type'] or 'jpg' in row['image_type']:
            try:
                from PIL import Image
                img = Image.open(io.BytesIO(row['image_data']))
                img.thumbnail((800, 800), Image.LANCZOS)
                output = io.BytesIO()
                img.save(output, format='JPEG', quality=75, optimize=True)
                output.seek(0)
                response = make_response(send_file(output, mimetype='image/jpeg'))
                response.headers['Cache-Control'] = 'public, max-age=86400'
                return response
            except ImportError:
                pass
            except Exception as e:
                print(f"图片压缩失败: {e}")

        response = make_response(send_file(
            io.BytesIO(row['image_data']),
            mimetype=row['image_type']
        ))
        response.headers['Cache-Control'] = 'public, max-age=86400'
        return response

    except Exception as e:
        return str(e), 500


@app.route('/api/download_ai/<int:image_id>')
def download_ai_file(image_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT image_code, image_name FROM underwear_garments WHERE image_id = %s", (image_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return "款式不存在", 404

        image_code = row['image_code']

        ai_path = os.path.join(UPLOAD_FOLDER, f"{image_code}.ai")
        if os.path.exists(ai_path):
            return send_file(ai_path, as_attachment=True, download_name=f"{image_code}.ai")

        image_name = row['image_name']
        safe_name = re.sub(r'[\\/*?:"<>|]', '', image_name)
        ai_path = os.path.join(AI_ROOT, f"{safe_name}.ai")
        if os.path.exists(ai_path):
            return send_file(ai_path, as_attachment=True, download_name=f"{safe_name}.ai")

        return f"AI文件不存在", 404

    except Exception as e:
        return str(e), 500


# ==================== 上传功能：内裤/其他款式 ====================

@app.route('/api/upload', methods=['POST'])
def upload_file():
    try:
        category_type = request.form.get('category_type', 'underwear')
        underwear_category = request.form.get('underwear_category', '')
        other_category = request.form.get('other_category', '')
        image_name = request.form.get('image_name', '').strip()
        image_code = request.form.get('image_code', '').strip()
        remark = request.form.get('remark', '').strip()

        if category_type == 'underwear':
            category = underwear_category
        else:
            category = other_category

        if not image_name:
            return jsonify({'status': 'error', 'error': '请填写款式名称'}), 400

        if not image_code:
            return jsonify({'status': 'error', 'error': '请填写款号'}), 400

        if 'image_file' not in request.files:
            return jsonify({'status': 'error', 'error': '请选择图片文件'}), 400

        image_file = request.files['image_file']
        if image_file.filename == '':
            return jsonify({'status': 'error', 'error': '请选择图片文件'}), 400

        if not allowed_file(image_file.filename, ALLOWED_EXTENSIONS):
            return jsonify({'status': 'error', 'error': '图片格式不支持，请上传 JPG/PNG 格式'}), 400

        image_data = image_file.read()
        image_type = image_file.mimetype
        image_size = len(image_data)

        ai_filename = None
        if 'ai_file' in request.files:
            ai_file = request.files['ai_file']
            if ai_file.filename != '' and allowed_file(ai_file.filename, ALLOWED_AI_EXTENSIONS):
                ai_filename = f"{image_code}.ai"
                ai_file_path = os.path.join(UPLOAD_FOLDER, ai_filename)
                ai_file.save(ai_file_path)

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) as cnt FROM underwear_garments WHERE image_code = %s", (image_code,))
        if cursor.fetchone()['cnt'] > 0:
            conn.close()
            return jsonify({'status': 'error', 'error': f'款号 {image_code} 已存在'}), 400

        description = f"分类: {category}"
        if remark:
            description += f" | 备注: {remark}"

        cursor.execute("""
            INSERT INTO underwear_garments 
            (image_code, image_name, image_data, image_type, image_size, description, upload_user_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (image_code, image_name, image_data, image_type, image_size, description, 1))
        conn.commit()
        image_id = cursor.lastrowid
        conn.close()

        return jsonify({
            'status': 'success',
            'image_id': image_id,
            'image_code': image_code,
            'ai_file': ai_filename
        })

    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500


# ==================== 编辑与删除 ====================

@app.route('/api/update_garment/<int:image_id>', methods=['PUT'])
def update_garment(image_id):
    try:
        data = request.json
        image_name = data.get('image_name', '').strip()
        image_code = data.get('image_code', '').strip()
        category = data.get('category', '').strip()
        remark = data.get('remark', '').strip()

        if not image_name:
            return jsonify({'status': 'error', 'error': '款式名称不能为空'}), 400

        if not image_code:
            return jsonify({'status': 'error', 'error': '款号不能为空'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        if image_code:
            cursor.execute(
                "SELECT COUNT(*) as cnt FROM underwear_garments WHERE image_code = %s AND image_id != %s",
                (image_code, image_id)
            )
            if cursor.fetchone()['cnt'] > 0:
                conn.close()
                return jsonify({'status': 'error', 'error': f'款号 {image_code} 已被其他款式使用'}), 400

        description_parts = []
        if category:
            description_parts.append(f"分类: {category}")
        if remark:
            description_parts.append(f"备注: {remark}")
        description = " | ".join(description_parts) if description_parts else ""

        cursor.execute("""
            UPDATE underwear_garments 
            SET image_name = %s, image_code = %s, description = %s
            WHERE image_id = %s
        """, (image_name, image_code, description, image_id))
        conn.commit()
        conn.close()

        return jsonify({'status': 'success', 'message': '更新成功'})

    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500


@app.route('/api/delete_garment/<int:image_id>', methods=['DELETE'])
def delete_garment(image_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT image_code FROM underwear_garments WHERE image_id = %s", (image_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return jsonify({'status': 'error', 'error': '款式不存在'}), 404

        image_code = row['image_code']

        ai_path = os.path.join(UPLOAD_FOLDER, f"{image_code}.ai")
        if os.path.exists(ai_path):
            os.remove(ai_path)

        cursor.execute("DELETE FROM underwear_garments WHERE image_id = %s", (image_id,))
        conn.commit()
        conn.close()

        return jsonify({'status': 'success', 'message': f'已删除款式 {image_code}'})

    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500


# ==================== 文胸上传功能 ====================

@app.route('/api/upload_bra_shape', methods=['POST'])
def upload_bra_shape():
    try:
        cup_type = request.form.get('cup_type')
        cup_shape_code = request.form.get('cup_shape_code', '').strip()
        remark = request.form.get('remark', '').strip()

        if not cup_type:
            return jsonify({'status': 'error', 'error': '请选择罩杯类型'}), 400

        if not cup_shape_code:
            return jsonify({'status': 'error', 'error': '请填写罩杯形状编号'}), 400

        if 'cup_png' not in request.files:
            return jsonify({'status': 'error', 'error': '请上传PNG文件'}), 400

        cup_png = request.files['cup_png']
        if cup_png.filename == '':
            return jsonify({'status': 'error', 'error': '请选择PNG文件'}), 400

        png_filename = f"{cup_shape_code}.png"
        png_path = os.path.join(BRA_CUP_ROOT, png_filename)
        cup_png.save(png_path)

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO bra_cup_shapes (cup_type, cup_shape_code, cup_shape_img_path, remark)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
                cup_shape_img_path = %s,
                remark = %s
        """, (cup_type, cup_shape_code, png_path, remark, png_path, remark))
        conn.commit()
        conn.close()

        return jsonify({
            'status': 'success',
            'message': f'罩杯形状 {cup_shape_code} 上传成功',
            'cup_type': cup_type,
            'cup_shape_code': cup_shape_code
        })

    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500


@app.route('/api/upload_bra_template', methods=['POST'])
def upload_bra_template():
    try:
        cup_type = request.form.get('cup_type')
        side_ratio_type = request.form.get('side_ratio_type')
        center_width = request.form.get('center_width')
        remark = request.form.get('remark', '').strip()

        if not cup_type:
            return jsonify({'status': 'error', 'error': '请选择罩杯类型'}), 400

        has_template = 'template_ai' in request.files and request.files['template_ai'].filename != ''
        has_annotation = 'annotation_ai' in request.files and request.files['annotation_ai'].filename != ''

        if not has_template and not has_annotation:
            return jsonify({'status': 'error', 'error': '请至少上传款式图AI或尺寸规格AI中的一个'}), 400

        cup_prefix = CUP_FILE_MAP.get(cup_type, cup_type)
        if cup_type in ['三角杯', '背心', '抹胸']:
            base_name = cup_prefix
        else:
            parts = [cup_prefix]
            if side_ratio_type:
                parts.append(side_ratio_type)
            if center_width:
                parts.append(CENTER_FILE_MAP.get(center_width, center_width))
            base_name = "-".join(parts)

        template_path = None
        if has_template:
            template_ai = request.files['template_ai']
            template_filename = f"{base_name}.ai"
            template_path = os.path.join(BRA_AI_ROOT, template_filename)
            template_ai.save(template_path)

        annotation_path = None
        if has_annotation:
            annotation_ai = request.files['annotation_ai']
            annotation_filename = f"{base_name}-规格.ai"
            annotation_path = os.path.join(BRA_ANNOTATION_ROOT, annotation_filename)
            annotation_ai.save(annotation_path)

        conn = get_db_connection()
        cursor = conn.cursor()

        db_center = '有' if center_width == '有前中宽' else '无' if center_width == '无前中宽' else center_width

        cursor.execute("""
            SELECT template_id FROM bra_templates 
            WHERE cup_type = %s AND (side_ratio_type = %s OR (side_ratio_type IS NULL AND %s IS NULL))
            AND (center_width = %s OR (center_width IS NULL AND %s IS NULL))
        """, (cup_type, side_ratio_type, side_ratio_type, db_center, db_center))
        existing = cursor.fetchone()

        if existing:
            cursor.execute("""
                UPDATE bra_templates 
                SET template_ai_path = %s, annotation_ai_path = %s, remark = %s
                WHERE template_id = %s
            """, (template_path, annotation_path, remark, existing['template_id']))
            template_id = existing['template_id']
        else:
            cursor.execute("""
                INSERT INTO bra_templates 
                (cup_type, side_ratio_type, center_width, template_ai_path, annotation_ai_path, remark, category_id)
                VALUES (%s, %s, %s, %s, %s, %s, 2)
            """, (cup_type, side_ratio_type, db_center, template_path, annotation_path, remark))
            template_id = cursor.lastrowid

        conn.commit()
        conn.close()

        return jsonify({
            'status': 'success',
            'template_id': template_id,
            'message': f'模板 {base_name} 上传成功'
        })

    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500


# ==================== 文胸编辑与删除功能 ====================

@app.route('/api/update_bra_shape', methods=['POST'])
def update_bra_shape():
    try:
        data = request.json
        cup_shape_code = data.get('cup_shape_code')
        remark = data.get('remark', '').strip()

        if not cup_shape_code:
            return jsonify({'status': 'error', 'error': '缺少形状编号'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE bra_cup_shapes 
            SET remark = %s 
            WHERE cup_shape_code = %s
        """, (remark, cup_shape_code))
        conn.commit()
        conn.close()

        return jsonify({'status': 'success', 'message': '备注更新成功'})
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500


@app.route('/api/delete_bra_shape', methods=['POST'])
def delete_bra_shape():
    try:
        data = request.json
        cup_shape_code = data.get('cup_shape_code')

        if not cup_shape_code:
            return jsonify({'status': 'error', 'error': '缺少形状编号'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT cup_shape_img_path FROM bra_cup_shapes WHERE cup_shape_code = %s", (cup_shape_code,))
        row = cursor.fetchone()

        cursor.execute("DELETE FROM bra_cup_shapes WHERE cup_shape_code = %s", (cup_shape_code,))
        conn.commit()
        conn.close()

        if row and os.path.exists(row['cup_shape_img_path']):
            os.remove(row['cup_shape_img_path'])

        return jsonify({'status': 'success', 'message': f'已删除 {cup_shape_code}'})
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500


@app.route('/api/update_bra_template', methods=['POST'])
def update_bra_template():
    try:
        data = request.json
        template_id = data.get('template_id')
        remark = data.get('remark', '').strip()

        if not template_id:
            return jsonify({'status': 'error', 'error': '缺少模板ID'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE bra_templates 
            SET remark = %s 
            WHERE template_id = %s
        """, (remark, template_id))
        conn.commit()
        conn.close()

        return jsonify({'status': 'success', 'message': '备注更新成功'})
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500


@app.route('/api/delete_bra_template', methods=['POST'])
def delete_bra_template():
    try:
        data = request.json
        template_id = data.get('template_id')

        if not template_id:
            return jsonify({'status': 'error', 'error': '缺少模板ID'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT template_ai_path, annotation_ai_path 
            FROM bra_templates 
            WHERE template_id = %s
        """, (template_id,))
        row = cursor.fetchone()

        cursor.execute("DELETE FROM bra_templates WHERE template_id = %s", (template_id,))
        conn.commit()
        conn.close()

        if row:
            if row['template_ai_path'] and os.path.exists(row['template_ai_path']):
                os.remove(row['template_ai_path'])
            if row['annotation_ai_path'] and os.path.exists(row['annotation_ai_path']):
                os.remove(row['annotation_ai_path'])

        return jsonify({'status': 'success', 'message': f'已删除模板 {template_id}'})
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500


# ==================== 页面路由 ====================

@app.route('/bra_design')
def bra_design_page():
    return render_template('bra_design.html')


@app.route('/upload')
def upload_page():
    return render_template('upload.html')


@app.route('/upload_bra')
def upload_bra_page():
    return render_template('upload_bra.html')


@app.route('/underwear_detail/<int:image_id>')
def underwear_detail(image_id):
    return render_template('underwear_detail.html')


@app.route('/detail_measurements/<int:image_id>')
def detail_measurements(image_id):
    return render_template('measurements.html')


@app.route('/detail/<int:image_id>')
def detail_page(image_id):
    return render_template('underwear_detail.html')


if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)