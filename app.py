# app.py - 完整版（所有组合完全自由，无任何限制）

from flask import Flask, jsonify, render_template, send_file, request
from flask_cors import CORS
from db_config import get_db_connection
import io
import os
import re
import requests
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

# ==================== Supabase 配置 ====================
SUPABASE_URL = os.environ.get('SUPABASE_URL', 'https://udebgifoxquvxqhpgkry.supabase.co')
SUPABASE_SERVICE_KEY = os.environ.get('SUPABASE_SERVICE_KEY', '')

STORAGE_API_BASE = f"{SUPABASE_URL}/storage/v1/object"

def supabase_download(bucket_name, filename):
    if not SUPABASE_SERVICE_KEY:
        return None
    url = f"{STORAGE_API_BASE}/{bucket_name}/{filename}"
    headers = {
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "apikey": SUPABASE_SERVICE_KEY
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.content
    else:
        return None

def supabase_upload(bucket_name, filename, file_data, content_type="application/octet-stream"):
    if not SUPABASE_SERVICE_KEY:
        return False
    url = f"{STORAGE_API_BASE}/{bucket_name}/{filename}"
    headers = {
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "apikey": SUPABASE_SERVICE_KEY,
    }
    files = {'file': (filename, file_data, content_type)}
    response = requests.post(url, headers=headers, files=files)
    if response.status_code in [200, 201]:
        return True
    elif response.status_code == 409:
        response = requests.put(url, headers=headers, files=files)
        return response.status_code == 200
    else:
        return False

def supabase_delete(bucket_name, filename):
    if not SUPABASE_SERVICE_KEY:
        return False
    url = f"{STORAGE_API_BASE}/{bucket_name}/{filename}"
    headers = {
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "apikey": SUPABASE_SERVICE_KEY
    }
    response = requests.delete(url, headers=headers)
    return response.status_code == 200


# ==================== 路径配置（兼容本地 + Render） ====================
LOCAL_BRA_AI_ROOT = r"C:\Users\李子珺\Desktop\学习\220613207刘凝\220613207刘凝\答辩文件\数据库源文件\bradata\bradata\bin\Debug\模板-款式图"
LOCAL_BRA_ANNOTATION_ROOT = r"C:\Users\李子珺\Desktop\学习\220613207刘凝\220613207刘凝\答辩文件\数据库源文件\bradata\bradata\bin\Debug\模板-尺寸规格"
LOCAL_BRA_CUP_ROOT = r"C:\Users\李子珺\Desktop\学习\220613207刘凝\220613207刘凝\答辩文件\数据库源文件\bradata\bradata\bin\Debug\罩杯形状"
LOCAL_AI_ROOT = r"C:\Users\李子珺\Desktop\学习\220613303_内裤款式图数据库系统设计与实现\论文归档\数据资料\企业款式图"

CLOUD_BRA_AI_ROOT = './uploads/templates'
CLOUD_BRA_ANNOTATION_ROOT = './uploads/annotations'
CLOUD_BRA_CUP_ROOT = './uploads/cup_shapes'
CLOUD_AI_ROOT = './uploads/underwear_ai'

def get_path(local_path, cloud_path):
    if os.environ.get('DATABASE_URL'):
        return cloud_path
    return local_path

BRA_AI_ROOT = get_path(LOCAL_BRA_AI_ROOT, CLOUD_BRA_AI_ROOT)
BRA_ANNOTATION_ROOT = get_path(LOCAL_BRA_ANNOTATION_ROOT, CLOUD_BRA_ANNOTATION_ROOT)
BRA_CUP_ROOT = get_path(LOCAL_BRA_CUP_ROOT, CLOUD_BRA_CUP_ROOT)
AI_ROOT = get_path(LOCAL_AI_ROOT, CLOUD_AI_ROOT)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
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
    if not description:
        return None
    match = re.search(r'分类:\s*([^\s|]+)', description)
    if match:
        return match.group(1)
    return None


# ==================== 文胸映射（仅用于文件名构建，无组合限制） ====================
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
        cursor.execute("SHOW TABLES;")
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
        cursor.execute("SHOW TABLES;")
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
    return jsonify({'status': 'success', 'data': list(CUP_FILE_MAP.keys())})


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
            item['exists'] = True
        return jsonify({'status': 'success', 'data': data})
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
            item['ai_exists'] = item['template_ai_path'] is not None
            item['annotation_exists'] = item['annotation_ai_path'] is not None

            side = item['side_ratio_type'] or '默认侧比'
            center = item['center_width'] or '无前中宽'
            if center == '有':
                center = '有前中宽'
            elif center == '无':
                center = '无前中宽'
            item['display_name'] = f"{side} · {center}"

        return jsonify({'status': 'success', 'data': result})
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500


@app.route('/api/bra_cup_image/<cup_shape_code>')
def get_bra_cup_image(cup_shape_code):
    try:
        if not SUPABASE_SERVICE_KEY:
            return "Supabase 未配置", 500
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT cup_shape_img_path FROM bra_cup_shapes WHERE cup_shape_code = %s", (cup_shape_code,))
        row = cursor.fetchone()
        conn.close()
        if not row or not row['cup_shape_img_path']:
            return "预览图不存在", 404
        uuid_file = row['cup_shape_img_path'].split('/')[-1]
        file_data = supabase_download('cup-shapes', uuid_file)
        if file_data is None:
            return "预览图不存在", 404
        return send_file(io.BytesIO(file_data), mimetype='image/png')
    except Exception as e:
        if '404' in str(e) or 'not found' in str(e).lower():
            return "预览图不存在", 404
        return str(e), 500


@app.route('/api/download_bra_cup/<cup_shape_code>')
def download_bra_cup(cup_shape_code):
    try:
        if not SUPABASE_SERVICE_KEY:
            return "Supabase 未配置", 500
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT cup_shape_img_path FROM bra_cup_shapes WHERE cup_shape_code = %s", (cup_shape_code,))
        row = cursor.fetchone()
        conn.close()
        if not row or not row['cup_shape_img_path']:
            return "文件不存在", 404
        uuid_file = row['cup_shape_img_path'].split('/')[-1]
        file_data = supabase_download('cup-shapes', uuid_file)
        if file_data is None:
            return "文件不存在", 404
        return send_file(io.BytesIO(file_data), as_attachment=True, download_name=f"{cup_shape_code}.png")
    except Exception as e:
        if '404' in str(e) or 'not found' in str(e).lower():
            return "文件不存在", 404
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

        conn = get_db_connection()
        cursor = conn.cursor()
        sql = "SELECT template_ai_path FROM bra_templates WHERE cup_type = %s"
        params = [cup_type]
        if side_ratio_type and side_ratio_type != '全部':
            sql += " AND side_ratio_type = %s"
            params.append(side_ratio_type)
        else:
            sql += " AND (side_ratio_type IS NULL OR side_ratio_type = '')"
        if center_width and center_width != '全部':
            db_center = '有' if center_width == '有前中宽' else '无' if center_width == '无前中宽' else center_width
            sql += " AND center_width = %s"
            params.append(db_center)
        else:
            sql += " AND (center_width IS NULL OR center_width = '')"
        cursor.execute(sql, params)
        row = cursor.fetchone()
        conn.close()

        if not row or not row['template_ai_path']:
            return "未找到对应的款式图", 404

        uuid_file = row['template_ai_path'].split('/')[-1]
        bucket = 'bra-templates'
        if 'supabase://' in row['template_ai_path']:
            parts = row['template_ai_path'].split('/')
            if len(parts) >= 2:
                bucket = parts[-2]

        file_data = supabase_download(bucket, uuid_file)
        if file_data is None:
            return f"文件不存在: {uuid_file}", 404
        download_name = f"{cup_type}_{side_ratio_type}_{center_width}.ai"
        return send_file(io.BytesIO(file_data), as_attachment=True, download_name=download_name)
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

        conn = get_db_connection()
        cursor = conn.cursor()
        sql = "SELECT annotation_ai_path FROM bra_templates WHERE cup_type = %s"
        params = [cup_type]
        if side_ratio_type and side_ratio_type != '全部':
            sql += " AND side_ratio_type = %s"
            params.append(side_ratio_type)
        else:
            sql += " AND (side_ratio_type IS NULL OR side_ratio_type = '')"
        if center_width and center_width != '全部':
            db_center = '有' if center_width == '有前中宽' else '无' if center_width == '无前中宽' else center_width
            sql += " AND center_width = %s"
            params.append(db_center)
        else:
            sql += " AND (center_width IS NULL OR center_width = '')"
        cursor.execute(sql, params)
        row = cursor.fetchone()
        conn.close()

        if not row or not row['annotation_ai_path']:
            return "未找到对应的尺寸规格文件", 404

        uuid_file = row['annotation_ai_path'].split('/')[-1]
        bucket = 'bra-annotations'
        if 'supabase://' in row['annotation_ai_path']:
            parts = row['annotation_ai_path'].split('/')
            if len(parts) >= 2:
                bucket = parts[-2]

        file_data = supabase_download(bucket, uuid_file)
        if file_data is None:
            return f"文件不存在: {uuid_file}", 404
        download_name = f"{cup_type}_{side_ratio_type}_{center_width}_规格.ai"
        return send_file(io.BytesIO(file_data), as_attachment=True, download_name=download_name)
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
            category = parse_category_from_description(item['description'])
            if not category:
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
        if not row['image_data']:
            return "图片数据为空", 404
        from flask import make_response
        response = make_response(send_file(
            io.BytesIO(row['image_data']),
            mimetype=row['image_type'] or 'image/jpeg'
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
        return "AI文件不存在", 404
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


# ==================== 文胸上传功能（完全自由组合，无任何限制） ====================

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

        ext = '.png'
        uuid_filename = f"{uuid.uuid4().hex}{ext}"
        file_data = cup_png.read()
        if not supabase_upload('cup-shapes', uuid_filename, file_data, content_type="image/png"):
            return jsonify({'status': 'error', 'error': '上传到 Supabase 失败'}), 500

        png_path = f"supabase://cup-shapes/{uuid_filename}"

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT cup_shape_code FROM bra_cup_shapes WHERE cup_type = %s AND cup_shape_code = %s",
            (cup_type, cup_shape_code)
        )
        existing = cursor.fetchone()

        if existing:
            cursor.execute(
                "UPDATE bra_cup_shapes SET cup_shape_img_path = %s, remark = %s WHERE cup_type = %s AND cup_shape_code = %s",
                (png_path, remark, cup_type, cup_shape_code)
            )
        else:
            cursor.execute(
                "INSERT INTO bra_cup_shapes (cup_type, cup_shape_code, cup_shape_img_path, remark) VALUES (%s, %s, %s, %s)",
                (cup_type, cup_shape_code, png_path, remark)
            )
        conn.commit()
        conn.close()
        return jsonify({'status': 'success', 'message': f'罩杯形状 {cup_shape_code} 上传成功'})
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
            return jsonify({'status': 'error', 'error': '请至少上传款式图AI或尺寸规格AI中的一个'}), 500

        if not SUPABASE_SERVICE_KEY:
            return jsonify({'status': 'error', 'error': 'Supabase 未配置'}), 500

        ext = '.ai'
        template_uuid = None
        annotation_uuid = None

        if has_template:
            template_ai = request.files['template_ai']
            template_data = template_ai.read()
            template_uuid = f"{uuid.uuid4().hex}{ext}"
            if not supabase_upload('bra-templates', template_uuid, template_data, content_type="application/octet-stream"):
                return jsonify({'status': 'error', 'error': '上传款式图失败'}), 500

        if has_annotation:
            annotation_ai = request.files['annotation_ai']
            annotation_data = annotation_ai.read()
            annotation_uuid = f"{uuid.uuid4().hex}{ext}"
            if not supabase_upload('bra-annotations', annotation_uuid, annotation_data, content_type="application/octet-stream"):
                return jsonify({'status': 'error', 'error': '上传尺寸规格失败'}), 500

        template_path = f"supabase://bra-templates/{template_uuid}" if template_uuid else None
        annotation_path = f"supabase://bra-annotations/{annotation_uuid}" if annotation_uuid else None

        conn = get_db_connection()
        cursor = conn.cursor()
        db_center = '有' if center_width == '有前中宽' else '无' if center_width == '无前中宽' else center_width

        # 查询是否存在该组合（完全自由，不限制任何组合）
        cursor.execute(
            "SELECT template_id FROM bra_templates WHERE cup_type = %s AND (side_ratio_type = %s OR (side_ratio_type IS NULL AND %s IS NULL)) AND (center_width = %s OR (center_width IS NULL AND %s IS NULL))",
            (cup_type, side_ratio_type, side_ratio_type, db_center, db_center)
        )
        existing = cursor.fetchone()

        if existing:
            update_fields = []
            params = []
            if template_path is not None:
                update_fields.append("template_ai_path = %s")
                params.append(template_path)
            if annotation_path is not None:
                update_fields.append("annotation_ai_path = %s")
                params.append(annotation_path)
            if remark:
                update_fields.append("remark = %s")
                params.append(remark)
            if update_fields:
                params.append(existing['template_id'])
                sql = f"UPDATE bra_templates SET {', '.join(update_fields)} WHERE template_id = %s"
                cursor.execute(sql, params)
            template_id = existing['template_id']
        else:
            cursor.execute(
                "INSERT INTO bra_templates (cup_type, side_ratio_type, center_width, template_ai_path, annotation_ai_path, remark, category_id) VALUES (%s, %s, %s, %s, %s, %s, 2)",
                (cup_type, side_ratio_type, db_center, template_path, annotation_path, remark)
            )
            template_id = cursor.lastrowid

        conn.commit()
        conn.close()
        return jsonify({'status': 'success', 'template_id': template_id, 'message': '模板上传成功'})
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
        cursor.execute("UPDATE bra_cup_shapes SET remark = %s WHERE cup_shape_code = %s", (remark, cup_shape_code))
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
        if row and row['cup_shape_img_path']:
            uuid_file = row['cup_shape_img_path'].split('/')[-1]
            if SUPABASE_SERVICE_KEY:
                supabase_delete('cup-shapes', uuid_file)
        cursor.execute("DELETE FROM bra_cup_shapes WHERE cup_shape_code = %s", (cup_shape_code,))
        conn.commit()
        conn.close()
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
        cursor.execute("UPDATE bra_templates SET remark = %s WHERE template_id = %s", (remark, template_id))
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
        cursor.execute(
            "SELECT template_ai_path, annotation_ai_path FROM bra_templates WHERE template_id = %s",
            (template_id,)
        )
        row = cursor.fetchone()

        if SUPABASE_SERVICE_KEY:
            if row and row['template_ai_path']:
                uuid_file = row['template_ai_path'].split('/')[-1]
                supabase_delete('bra-templates', uuid_file)
            if row and row['annotation_ai_path']:
                uuid_file = row['annotation_ai_path'].split('/')[-1]
                supabase_delete('bra-annotations', uuid_file)

        cursor.execute("DELETE FROM bra_templates WHERE template_id = %s", (template_id,))
        conn.commit()
        conn.close()
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
