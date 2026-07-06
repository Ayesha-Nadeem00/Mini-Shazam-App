"""
db_config.py
Ye file sirf DATABASE se connection banane ke liye hai.
Doosri files isay import karke database use karengi.
"""

import psycopg2

# ⚠️ Yahan apni details bharein (jo aap ne CREATE DATABASE ke waqt use ki thi)
DB_CONFIG = {
    "host": "localhost",
    "database": "shazam_clone",
    "user": "postgres",
    "password": "ayeshanad000",   # <-- apna postgres password yahan likhein
    "port": 5432
}


def get_connection():
    """
    Database se connection banata hai aur return karta hai.
    Har file jo DB use karegi, ye function call karegi.
    """
    conn = psycopg2.connect(**DB_CONFIG)
    return conn


# Test: agar ye file seedhi run karein to check hoga connection ban raha hai ya nahi
if __name__ == "__main__":
    try:
        conn = get_connection()
        print("✅ Database se connection kamyab!")
        conn.close()
    except Exception as e:
        print("❌ Connection fail hua. Error:")
        print(e)