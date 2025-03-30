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

# Configuración para reducir consumo de recursos
absl.logging.set_verbosity(absl.logging.ERROR)
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_FORCE_GPU_ALLOW_GROWTH'] = 'true'

# Inicialización de la app Flask con CORS
app = Flask(__name__)
CORS(app)  # Habilitar CORS para todos los dominios

# Configuración
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB

# 1. Funciones personalizadas ligeras
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
    return K.pow((1 - tversky(y_true, y_pred)), 0.75)

# 2. Carga optimizada de modelos
model_class = None
model_seg = None

def load_model_segmentacion():
    """Carga el modelo de segmentación solo cuando sea necesario"""
    global model_seg
    if model_seg is None:
        print("⏳ Cargando modelo de segmentación bajo demanda...")
        model_seg = tf.keras.models.load_model(
            'weights_seg.hdf5',
            custom_objects={
                'tversky_loss': tversky_loss,
                'focal_tversky': focal_tversky,
                'tversky': tversky
            }
        )
    return model_seg

def load_model_clasificacion():
    """Carga el modelo de clasificación en partes con manejo de memoria"""
    global model_class
    if model_class is None:
        print("⏳ Cargando modelo de clasificación por partes...")
        
        # 1. Crear modelo vacío con la misma arquitectura
        # (Aquí debes poner la arquitectura de tu modelo)
        # Ejemplo simplificado:
        from tensorflow.keras.models import Sequential
        from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense
        
        model = Sequential([
            Conv2D(32, (3,3), activation='relu', input_shape=(256,256,3)),
            MaxPooling2D((2,2)),
            Flatten(),
            Dense(2, activation='softmax')
        ])
        
        # 2. Cargar pesos desde partes
        try:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.hdf5')
            temp_path = temp_file.name
            
            # Combinar partes
            parts_folder = 'weights_parts'
            part_number = 0
            while True:
                part_path = os.path.join(parts_folder, f"weights_part{part_number}")
                if not os.path.exists(part_path):
                    if part_number == 0:
                        raise FileNotFoundError("No se encontraron partes del modelo")
                    break
                
                with open(part_path, 'rb') as f:
                    temp_file.write(f.read())
                part_number += 1
            
            temp_file.close()
            
            # Cargar pesos
            model.load_weights(temp_path)
            model_class = model
            print("✅ Modelo de clasificación cargado")
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    return model_class

# 3. Endpoints optimizados
@app.route('/predict', methods=['POST'])
def predict():
    try:
        # Validaciones iniciales
        if 'file' not in request.files:
            return jsonify({'error': 'No se subió ningún archivo'}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Nombre de archivo vacío'}), 400
        
        # Cargar modelos bajo demanda
        model_cls = load_model_clasificacion()
        if model_cls is None:
            return jsonify({'error': 'Error cargando modelo'}), 500
        
        # Procesamiento mínimo
        analysis_id = datetime.now().strftime('%Y%m%d%H%M%S')
        original_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{analysis_id}_original.jpg")
        file.save(original_path)
        
        # Preprocesamiento ligero
        img = cv2.imread(original_path, cv2.IMREAD_COLOR)
        if img is None:
            return jsonify({'error': 'Imagen no válida'}), 400
            
        img = cv2.resize(img, (256, 256))
        img = np.expand_dims(img.astype(np.float32)/255.0, axis=0)
        
        # Predicción de clasificación
        class_pred = model_cls.predict(img, verbose=0)[0]
        has_tumor = np.argmax(class_pred) == 1
        accuracy = float(np.max(class_pred))
        
        if not has_tumor:
            return jsonify({
                'has_tumor': False,
                'accuracy': accuracy
            })
        
        # Solo cargar modelo de segmentación si hay tumor
        model_seg = load_model_segmentacion()
        seg_pred = model_seg.predict(img, verbose=0)[0]
        
        # Resultados simplificados
        return jsonify({
            'has_tumor': True,
            'accuracy': accuracy,
            'tumor_size': float(np.mean(seg_pred > 0.3))  # Porcentaje de área con tumor
        })
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'error': 'Error procesando la imagen'}), 500

@app.route('/health')
def health_check():
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=False)