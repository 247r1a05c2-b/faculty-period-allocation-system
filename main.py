import sys
import traceback
from pathlib import Path
from flask import Flask, jsonify

ROOT = Path(__file__).resolve().parent / 'faculty_allocation_system'
sys.path.insert(0, str(ROOT))

app = Flask(__name__)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def diagnose(path):
    try:
        from app import app as faculty_app
        return faculty_app.test_client().get('/').get_data(as_text=True), 200
    except Exception as exc:
        return jsonify({
            'status': 'application_import_error',
            'error_type': type(exc).__name__,
            'error': str(exc),
            'traceback': traceback.format_exc(),
        }), 500

handler = app
