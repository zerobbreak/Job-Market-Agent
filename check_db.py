#!/usr/bin/env python3
"""
Check database structure and FTS5 setup
"""

from utils.database import job_db
import sqlite3

conn = job_db._get_connection()
cursor = conn.cursor()

try:
    # Check what tables exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print('Tables in database:')
    for table in tables:
        print(f'  {table[0]}')

    # Check FTS5 table structure
    cursor.execute('PRAGMA table_info(jobs_fts)')
    columns = cursor.fetchall()
    print('\nFTS5 table structure:')
    for col in columns:
        print(f'  {col[1]} ({col[2]})')

    # Check if FTS5 table has data (using FTS5 syntax)
    try:
        cursor.execute('SELECT COUNT(*) FROM jobs_fts')
        fts_count = cursor.fetchone()[0]
        print(f'\nFTS5 table has {fts_count} rows')
    except Exception as e:
        print(f'FTS5 count error: {e}')
        # Try alternative approach
        cursor.execute('SELECT COUNT(*) FROM jobs_fts_data')
        fts_count = cursor.fetchone()[0]
        print(f'FTS5 data table has {fts_count} rows')

    # Check main jobs table
    cursor.execute('SELECT COUNT(*) FROM jobs')
    jobs_count = cursor.fetchone()[0]
    print(f'Jobs table has {jobs_count} rows')

    # Check sample data
    cursor.execute('SELECT * FROM jobs LIMIT 2')
    jobs_sample = cursor.fetchall()
    print('\nSample jobs:')
    for job in jobs_sample:
        print(f'  ID: {job[0]}, Title: {job[1]}, Company: {job[2]}')

except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()

finally:
    conn.close()
