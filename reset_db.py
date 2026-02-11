import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Parse the DATABASE_URL
# Format: postgresql://user:password@host:port/dbname
parts = DATABASE_URL.replace("postgresql://", "").split("@")
user_pass = parts[0].split(":")
host_port_db = parts[1].split("/")
host_port = host_port_db[0].split(":")

user = user_pass[0]
password = user_pass[1]
host = host_port[0]
port = host_port[1] if len(host_port) > 1 else "5432"
dbname = host_port_db[1]

# Connect to database
conn = psycopg2.connect(
    host=host,
    port=port,
    dbname=dbname,
    user=user,
    password=password
)
conn.autocommit = True
cursor = conn.cursor()

# Drop all tables
print("Dropping existing tables...")
cursor.execute("""
    DROP TABLE IF EXISTS linguistic_analysis CASCADE;
    DROP TABLE IF EXISTS execution_logs CASCADE;
    DROP TABLE IF EXISTS feedback CASCADE;
    DROP TABLE IF EXISTS bug_patterns CASCADE;
    DROP TABLE IF EXISTS analyses CASCADE;
""")
print("Tables dropped successfully!")

cursor.close()
conn.close()

print("Now run the application to recreate tables with correct schema.")
