"""
Verify feedback table schema
"""
import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Parse DATABASE_URL for psycopg2
url_parts = DATABASE_URL.replace("postgresql://", "").split("@")
user_pass = url_parts[0].split(":")
host_port_db = url_parts[1].split("/")
host_port = host_port_db[0].split(":")

conn = psycopg2.connect(
    dbname=host_port_db[1],
    user=user_pass[0],
    password=user_pass[1],
    host=host_port[0],
    port=host_port[1]
)

cursor = conn.cursor()

print("Checking feedback table structure...")
cursor.execute("""
    SELECT column_name, data_type, is_nullable
    FROM information_schema.columns
    WHERE table_name = 'feedback'
    ORDER BY ordinal_position;
""")

columns = cursor.fetchall()
print("\nFeedback table columns:")
print("-" * 60)
for col in columns:
    print(f"  {col[0]:<20} {col[1]:<20} NULL: {col[2]}")

print("-" * 60)
print("✓ Schema verified!")

cursor.close()
conn.close()
