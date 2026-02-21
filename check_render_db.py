"""
Quick script to check Render PostgreSQL database contents
Show all tables with their columns and last 10 rows in table format
Export to Excel file: database_export.xlsx
"""
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv
from tabulate import tabulate
import pandas as pd
from datetime import datetime

load_dotenv()

# Get DATABASE_URL from environment
db_url = os.getenv('DATABASE_URL')
if not db_url:
    print(" DATABASE_URL not found in .env file")
    exit(1)

print(f" Connecting to Render PostgreSQL...")
engine = create_engine(db_url)

# Excel file path (will be overwritten each time)
excel_file = "database_export.xlsx"

try:
    # Create Excel writer (will overwrite existing file)
    with pd.ExcelWriter(excel_file, engine='openpyxl', mode='w') as excel_writer:
        with engine.connect() as conn:
            # Get all tables
            tables_result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            
            tables = [row[0] for row in tables_result]
            print(f"\n Found {len(tables)} tables in database\n")
            print("=" * 100)
            
            # For each table, show columns and last 10 rows
            for table_name in tables:
                print(f"\n TABLE: {table_name.upper()}")
                print("-" * 100)
                
                # Get column names
                columns_result = conn.execute(text(f"""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = '{table_name}'
                    ORDER BY ordinal_position
                """))
                
                columns = [(row[0], row[1]) for row in columns_result]
                column_names = [col[0] for col in columns]
                
                # Display columns as table
                print(f"\n COLUMNS:")
                col_table = [[i+1, col[0], col[1]] for i, col in enumerate(columns)]
                print(tabulate(col_table, headers=["#", "Column Name", "Data Type"], tablefmt="grid"))
                
                # Count total rows
                count = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
                print(f"\n Total rows: {count}")
                
                if count > 0:
                    # Get last 10 rows
                    print(f"\n LAST 10 ROWS:")
                    result = conn.execute(text(f"""
                        SELECT * FROM {table_name}
                        ORDER BY 1 DESC
                        LIMIT 10
                    """))
                    
                    rows = result.fetchall()
                    
                    # Prepare data for table (truncate long text)
                    table_data = []
                    for row in rows:
                        row_data = []
                        for value in row:
                            if isinstance(value, str) and len(value) > 50:
                                row_data.append(value[:50] + "...")
                            else:
                                row_data.append(value)
                        table_data.append(row_data)
                    
                    print(tabulate(table_data, headers=column_names, tablefmt="grid"))
                    
                    # Export to Excel (each table as separate sheet)
                    df = pd.DataFrame(rows, columns=column_names)
                    # Truncate sheet name to max 31 characters (Excel limit)
                    sheet_name = table_name[:31] if len(table_name) > 31 else table_name
                    df.to_excel(excel_writer, sheet_name=sheet_name, index=False)
                    print(f" Exported to Excel sheet: {sheet_name}")
                else:
                    print("  (No data)")
                    # Create empty sheet for tables with no data
                    df = pd.DataFrame(columns=column_names)
                    sheet_name = table_name[:31] if len(table_name) > 31 else table_name
                    df.to_excel(excel_writer, sheet_name=sheet_name, index=False)
                
                print("\n" + "=" * 100)
        
    print(f"\n Database check complete!")
    print(f" Excel file saved: {excel_file}")
    print(f" (File will be overwritten on next run)")
    
except Exception as e:
    print(f"\n Error: {e}")
