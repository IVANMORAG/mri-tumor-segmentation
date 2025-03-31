from flask import Flask
from flask_cors import CORS
from src.config import Config
from src.models.loader import ModelLoader
from src.routes.api import setup_api_routes
from src.routes.views import setup_view_routes
from src.utils.ngrok import start_ngrok
import threading
import os

def create_app():
    app = Flask(__name__)
    CORS(app)
    
    # Configuración
    Config.init_app(app)
    app.config.from_object(Config)
    
    # Cargar modelos
    model_class, model_seg = ModelLoader.load_models()
    
    # Configurar rutas
    setup_api_routes(app, model_class, model_seg)
    setup_view_routes(app)
    
    return app

if __name__ == '__main__':
    app = create_app()
    
    # Iniciar ngrok en un hilo separado
    start_ngrok(Config.NGROK_DOMAIN, Config.FLASK_PORT)
    
    print("🚀 Iniciando servidor Flask...")
    app.run(host='0.0.0.0', port=Config.FLASK_PORT, debug=True)