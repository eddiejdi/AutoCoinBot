import os
from dotenv import load_dotenv
load_dotenv()
print(f"DATABASE_URL = {os.getenv('DATABASE_URL', 'NOT_SET')}")
print(f"TRADES_DB = {os.getenv('TRADES_DB', 'NOT_SET')}")
