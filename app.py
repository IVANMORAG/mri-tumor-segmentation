from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from flask_cors import CORS
import cv2
from datetime import datetime
import traceback
import tempfile
import os
import numpy as np
import tensorflow as tf
from tensorflow.keras import backend as K
from skimage import io
import absl.logging

# Configuración para reducir logs de TensorFlow
absl.logging.set_verbosity(absl.logging.ERROR)
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

# Inicialización de la app Flask con CORS
app = Flask(__name__)
CORS(app)  # Habilitar CORS para todos los dominios en todas las rutas

# Configuración
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 1. Funciones personalizadas para los modelos
def tversky(y_true, y_pred, smooth=1e-6):
    y_true_pos = K.flatten(y_true)
    y_pred_pos = K.flatten(y_pred)
    true_pos = K.sum(y_true_pos * y_pred_pos)
    false_neg = K.sum(y_true_pos * (1-y_pred_pos))
    false_pos = K.sum((1-y_true_pos)*y_pred_pos)
    alpha = 0.7
    return (true_pos + smooth)/(true_pos + alpha*false_neg + (1-alpha)*false_pos + smooth)

def tversky_loss(y_true, y_pred):
    return 1 - tversky(y_true, y_pred)

def focal_tversky(y_true, y_pred):
    y_true = tf.cast(y_true, tf.float32)
    y_pred = tf.cast(y_pred, tf.float32)
    pt_1 = tversky(y_true, y_pred)
    gamma = 0.75
    return K.pow((1-pt_1), gamma)

# 2. Carga de modelos
def load_model_from_parts(parts_folder, custom_objects):
    """Carga el modelo desde partes usando un archivo temporal"""
    try:
        print(f"🔍 Combinando partes del modelo desde '{parts_folder}'...")
        
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.hdf5')
        temp_path = temp_file.name
        
        try:
            part_number = 0
            while True:
                part_path = os.path.join(parts_folder, f"weights_part{part_number}")
                if not os.path.exists(part_path):
                    if part_number == 0:
                        raise FileNotFoundError(f"No se encontraron partes del modelo en {parts_folder}")
                    break
                
                with open(part_path, 'rb') as f:
                    temp_file.write(f.read())
                part_number += 1
            
            temp_file.close()
            
            print("⚙️ Cargando modelo desde archivo temporal...")
            model = tf.keras.models.load_model(temp_path, custom_objects=custom_objects)
            print("✅ Modelo cargado exitosamente desde partes")
            return model
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
                
    except Exception as e:
        print(f"❌ Error cargando modelo desde partes: {str(e)}")
        traceback.print_exc()
        return None

# Variables globales para los modelos
model_class = None
model_seg = None

def initialize_models():
    """Inicializa solo el modelo principal al inicio"""
    global model_class
    try:
        print("⏳ Iniciando carga del modelo principal...")
        custom_objects = {
            'tversky_loss': tversky_loss,
            'focal_tversky': focal_tversky,
            'tversky': tversky
        }
        model_class = load_model_from_parts('weights_parts', custom_objects)
        return model_class is not None
    except Exception as e:
        print(f"❌ Error inicializando modelos: {str(e)}")
        return False

# 3. Funciones de procesamiento de imágenes
def preprocess_image(image_path):
    """Preprocesamiento optimizado de imágenes"""
    try:
        img = cv2.imread(image_path, cv2.IMREAD_COLOR)
        if img is None:
            img = io.imread(image_path)
        
        if len(img.shape) == 2:
            img = np.stack((img,)*3, axis=-1)
        
        img = cv2.resize(img, (256, 256))
        img = img.astype(np.float32) / 255.0
        return np.expand_dims((img - img.mean()) / (img.std() + 1e-7), axis=0)
    except Exception as e:
        print(f"Error preprocesando imagen: {str(e)}")
        raise

def postprocess_mask(mask):
    """Postprocesamiento optimizado de máscara"""
    kernel = np.ones((3,3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    return cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

def create_overlay(original_img, mask):
    """Overlay optimizado con transparencia"""
    overlay_img = cv2.cvtColor(original_img, cv2.COLOR_RGB2RGBA) if len(original_img.shape) == 3 else cv2.cvtColor(original_img, cv2.COLOR_GRAY2RGBA)
    red_mask = np.zeros_like(overlay_img)
    red_mask[mask > 0] = [255, 0, 0, 128]
    return cv2.addWeighted(overlay_img, 1, red_mask, 0.7, 0)

def predict_tumor(image_path, model_class, model_seg):
    try:
        img = preprocess_image(image_path)
        
        # Predicción de clasificación
        class_pred = model_class.predict(img, verbose=0, batch_size=1)
        has_tumor = np.argmax(class_pred) == 1
        accuracy = float(np.max(class_pred))
        
        if not has_tumor:
            return {'has_tumor': False, 'accuracy': accuracy, 'mask': None, 'overlay_img': None}
        
        # Predicción de segmentación (solo si hay tumor)
        seg_pred = model_seg.predict(img, verbose=0, batch_size=1)
        mask = (seg_pred.squeeze() > 0.3).astype(np.uint8) * 255
        
        original_img = cv2.imread(image_path)
        return {
            'has_tumor': True,
            'accuracy': accuracy,
            'mask': cv2.resize(mask, (original_img.shape[1], original_img.shape[0])),
            'overlay_img': create_overlay(original_img, mask)
        }
    except Exception as e:
        print(f"Error en predict_tumor: {str(e)}")
        raise

# 4. Endpoints de la API
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health')
def health_check():
    """Endpoint para health checks y mantener la app activa"""
    return jsonify({
        "status": "active",
        "timestamp": datetime.now().isoformat(),
        "models_loaded": model_class is not None
    })

@app.route('/predict', methods=['POST'])
def predict():
    global model_class, model_seg
    
    # Verificación de modelos
    if model_class is None and not initialize_models():
        return jsonify({'error': 'Error inicializando modelos'}), 500
    
    # Validación de archivo
    if 'file' not in request.files:
        return jsonify({'error': 'No se subió ningún archivo'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Nombre de archivo vacío'}), 400
    
    try:
        # Preparación de directorio
        analysis_id = datetime.now().strftime('%Y%m%d%H%M%S')
        analysis_folder = os.path.join(app.config['UPLOAD_FOLDER'], f"analysis_{analysis_id}")
        os.makedirs(analysis_folder, exist_ok=True)
        
        # Guardar archivo
        original_path = os.path.join(analysis_folder, "original.jpg")
        file.save(original_path)
        
        # Carga bajo demanda del modelo de segmentación
        if model_seg is None:
            print("⏳ Cargando modelo de segmentación bajo demanda...")
            model_seg = tf.keras.models.load_model(
                'weights_seg.hdf5',
                custom_objects={'tversky_loss': tversky_loss, 'focal_tversky': focal_tversky, 'tversky': tversky}
            )
        
        # Procesamiento
        print(f"⏳ Iniciando predicción para {original_path}...")
        result = predict_tumor(original_path, model_class, model_seg)
        print("✅ Predicción completada")
        
        # Preparar respuesta
        response = {
            'has_tumor': result['has_tumor'],
            'accuracy': float(result['accuracy']),
            'images': {
                'original': f"analysis_{analysis_id}/original.jpg",
                'mask': None,
                'overlay': None
            }
        }
        
        if result['has_tumor']:
            mask_path = os.path.join(analysis_folder, "mask.png")
            cv2.imwrite(mask_path, result['mask'])
            response['images']['mask'] = f"analysis_{analysis_id}/mask.png"
            
            overlay_path = os.path.join(analysis_folder, "overlay.png")
            cv2.imwrite(overlay_path, result['overlay_img'])
            response['images']['overlay'] = f"analysis_{analysis_id}/overlay.png"
        
        return jsonify(response)
        
    except Exception as e:
        print(f"🔥 Error crítico: {str(e)}")
        return jsonify({'error': 'Error procesando la imagen', 'details': str(e)}), 500

@app.route('/static/uploads/<path:filename>')
def uploaded_file(filename):
    """Sirve archivos subidos"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/api/history')
def get_history():
    """Obtiene el historial de análisis"""
    try:
        analyses = []
        upload_dir = app.config['UPLOAD_FOLDER']
        
        folders = sorted([d for d in os.listdir(upload_dir) if d.startswith('analysis_')], 
                        key=lambda x: os.path.getmtime(os.path.join(upload_dir, x)), 
                        reverse=True)
        
        for folder in folders:
            folder_path = os.path.join(upload_dir, folder)
            if os.path.isdir(folder_path):
                analyses.append({
                    'id': folder,
                    'original': f"{folder}/original.jpg",
                    'date': datetime.strptime(folder.replace('analysis_', ''), '%Y%m%d%H%M%S').strftime('%d/%m/%Y %H:%M:%S')
                })
        
        return jsonify({'analyses': analyses})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/delete/<analysis_id>', methods=['DELETE'])
def delete_analysis(analysis_id):
    """Elimina un análisis específico"""
    try:
        folder_path = os.path.join(app.config['UPLOAD_FOLDER'], analysis_id)
        if os.path.exists(folder_path):
            import shutil
            shutil.rmtree(folder_path)
            return jsonify({'success': True})
        return jsonify({'error': 'Analysis not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.before_request
def before_request():
    """Middleware para validar el tamaño de archivos"""
    max_size = 5 * 1024 * 1024  # 5MB
    if request.content_length and request.content_length > max_size:
        return jsonify({"error": "El archivo es demasiado grande (máx 5MB)"}), 413

if __name__ == '__main__':
    # Configuración inicial
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    # Inicialización ligera del modelo principal
    initialize_models()
    
    # Configuración para Render
    port = int(os.environ.get("PORT", 10000))
    debug_mode = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    
    print(f"🚀 Iniciando servidor Flask en puerto {port}...")
    app.run(host='0.0.0.0', port=port, debug=debug_mode)