import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'change-this-in-production')
    EXPORT_FOLDER = os.path.join(os.path.dirname(__file__), 'exports')
