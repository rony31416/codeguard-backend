"""
Fix feedback table schema to match updated models
"""
import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Parse DATABASE_URL for psycopg2
# Format: postgresql://user:password@host:port/database
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

print("Dropping old feedback table...")
cursor.execute("DROP TABLE IF EXISTS feedback CASCADE;")

print("Creating new feedback table with correct schema...")
cursor.execute("""
    CREATE TABLE feedback (
        id SERIAL PRIMARY KEY,
        analysis_id INTEGER NOT NULL,
        rating INTEGER NOT NULL,
        comment TEXT,
        is_helpful BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (analysis_id) REFERENCES analyses(analysis_id) ON DELETE CASCADE
    );
""")

conn.commit()
print("✓ Feedback table recreated successfully!")

cursor.close()
conn.close()
