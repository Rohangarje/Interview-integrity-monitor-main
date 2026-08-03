import MySQLdb
import sys

try:
    db = MySQLdb.connect(host="localhost", user="root", passwd="NewStrongPassword123!")
    cursor = db.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS interview_db")
    print("Database interview_db created successfully or already exists.")
    db.close()
except Exception as e:
    print(f"Failed to create database: {e}")
    sys.exit(1)
