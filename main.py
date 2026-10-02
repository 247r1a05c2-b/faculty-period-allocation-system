import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent / 'faculty_allocation_system'
sys.path.insert(0, str(ROOT))

from app import app

handler = app
