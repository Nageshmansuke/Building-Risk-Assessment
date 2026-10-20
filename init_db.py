#!/usr/bin/env python3
"""
Initialize database for QuakeGuard AI application.
Supports MySQL when available, and initializes SQLite database automatically.
"""

import os
import sys
from dotenv import load_dotenv

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

def init_database():
    mysql_user = os.getenv("MYSQL_USER", "root")
    mysql_pass = os.getenv("MYSQL_PASSWORD", "")
    mysql_host = os.getenv("MYSQL_HOST", "localhost")
    mysql_port = os.getenv("MYSQL_PORT", "3306")
    mysql_db = os.getenv("MYSQL_DATABASE", "quakeguard")

    if mysql_pass:
        try:
            import mysql.connector
            conn = mysql.connector.connect(
                host=mysql_host,
                user=mysql_user,
                password=mysql_pass,
                port=int(mysql_port)
            )
            if conn.is_connected():
                cursor = conn.cursor()
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{mysql_db}`")
                cursor.close()
                conn.close()
                print(f"[OK] MySQL database '{mysql_db}' created or verified on {mysql_host}:{mysql_port}!")
                return True
        except Exception as err:
            print(f"[INFO] MySQL connection failed ({err}).")

    # SQLite fallback
    from app import app, db
    with app.app_context():
        db.create_all()
    print("[OK] SQLite database tables initialized successfully!")
    return True

if __name__ == '__main__':
    print("[INFO] Initializing QuakeGuard AI Database...")
    init_database()
    print("[OK] Database setup complete. You can run: python app.py")
