import sqlite3
import os
import sys

# Add backend dir to path for app imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.auth import verify_password

conn = sqlite3.connect('../data/medifusion.db')
h = conn.execute("SELECT password_hash FROM users WHERE login_id='ADM-001'").fetchone()[0]
print('Result:', verify_password('Admin@123', h))
