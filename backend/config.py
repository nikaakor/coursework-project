import os
from database import BASE_DIR

ADMIN_KEY = os.getenv("ADMIN_KEY", "admin")   
DEFAULT_LAT, DEFAULT_LON = 49.8419, 24.0315     
STATIC_DIR = BASE_DIR.parent / "frontend"
