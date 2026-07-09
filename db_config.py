# db_config.py - 支持本地MySQL + 云端PostgreSQL

import os
import pymysql
import psycopg2
import psycopg2.extras

def get_db_connection():
    # 优先使用云端数据库URL（Render会自动设置 DATABASE_URL）
    database_url = os.environ.get('DATABASE_URL')
    
    if database_url and database_url.startswith('postgresql://'):
        # 使用PostgreSQL（云端）
        conn = psycopg2.connect(database_url)
        conn.cursor_factory = psycopg2.extras.RealDictCursor
        return conn
    else:
        # 本地开发使用MySQL
        return pymysql.connect(
            host='localhost',
            user='root',
            password='4732191202',
            database='lingerie_bra_db',
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )