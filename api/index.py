import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / 'faculty_allocation_system'
sys.path.insert(0, str(ROOT))

try:
    from app import app
except Exception as exc:
    from flask import Flask, jsonify
    app = Flask(__name__)
    _error = traceback.format_exc()

    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def startup_error(path):
        return jsonify({
            'status': 'startup_error',
            'error_type': type(exc).__name__,
            'error': str(exc),
            'traceback': _error,
        }), 500

# Vercel discovers the Flask application as `app`.
