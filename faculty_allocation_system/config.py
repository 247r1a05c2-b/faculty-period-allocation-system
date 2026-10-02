import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'change-this-in-production')
    if os.environ.get('EXPORT_FOLDER'):
        EXPORT_FOLDER = os.environ['EXPORT_FOLDER']
    elif os.environ.get('VERCEL'):
        EXPORT_FOLDER = '/tmp/faculty-allocation-exports'
    else:
        EXPORT_FOLDER = os.path.join(os.path.dirname(__file__), 'exports')
