from flask import Flask, render_template
from flask_cors import CORS
from models.model_loader import load_models
from routes.analysis_routes import analysis_bp
from routes.history_routes import history_bp
import os

def create_app():
    app = Flask(__name__)
    CORS(app)
    
    # Configuración
    app.config['UPLOAD_FOLDER'] = 'static/uploads'
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Cargar modelos al iniciar
    app.config['MODELS'] = load_models()
    
    # Registrar blueprints
    app.register_blueprint(analysis_bp)
    app.register_blueprint(history_bp)
    
    # Ruta principal
    @app.route('/')
    def index():
        return render_template('index.html')
    
    return app

if __name__ == '__main__':
    app = create_app()
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    print("🚀 Iniciando servidor Flask...")
    app.run(host='0.0.0.0', port=5001, debug=True)