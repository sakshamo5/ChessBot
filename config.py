import os

class Config:
    LICHESS_TOKEN = os.environ.get('LICHESS_TOKEN')
    BOT_USERNAME = os.environ.get('BOT_USERNAME')
    FLASK_HOST = '0.0.0.0'
    FLASK_PORT = int(os.environ.get('PORT', 5000))
    DEBUG = False
