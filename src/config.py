import os

class Config:
    UPLOAD_FOLDER = 'static/uploads'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
    NGROK_DOMAIN = 'poorly-free-insect.ngrok-free.app'
    FLASK_PORT = 5001

    @staticmethod
    def init_app(app):
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)