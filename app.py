from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import cv2
from datetime import datetime
import traceback
import subprocess
import threading
import tempfile
import time
import requests
from flask_cors import CORS
import os
import numpy as np
import tensorflow as tf
from tensorflow.keras import backend as K
from skimage import io
from io import BytesIO

app = Flask(__name__)
CORS(app)

# Configuración
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 1. Definir primero las funciones personalizadas
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

def load_model_from_parts(parts_folder, custom_objects):
    """Carga el modelo desde partes usando un archivo temporal"""
    try:
        print(f"🔍 Combinando partes del modelo desde '{parts_folder}'...")
        
        # Crear un archivo temporal
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.hdf5')
        temp_path = temp_file.name
        
        try:
            # Escribir todas las partes en el archivo temporal
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
            
            # Cerrar el archivo temporal antes de cargarlo
            temp_file.close()
            
            print("⚙️ Cargando modelo desde archivo temporal...")
            model = tf.keras.models.load_model(temp_path, custom_objects=custom_objects)
            print("✅ Modelo cargado exitosamente desde partes")
            return model
            
        finally:
            # Eliminar el archivo temporal después de cargar el modelo
            if os.path.exists(temp_path):
                os.unlink(temp_path)
                
    except Exception as e:
        print(f"❌ Error cargando modelo desde partes: {str(e)}")
        traceback.print_exc()
        return None
    
    
def load_models():
    try:
        print("⏳ Iniciando carga de modelos...")
        custom_objects = {
            'tversky_loss': tversky_loss,
            'focal_tversky': focal_tversky,
            'tversky': tversky
        }
        
        # Cargar modelo de clasificación desde partes
        model_class = load_model_from_parts('weights_parts', custom_objects)
        if model_class is None:
            raise Exception("No se pudo cargar el modelo de clasificación")
        
        # Cargar modelo de segmentación (asumiendo que no está dividido)
        model_seg = tf.keras.models.load_model(
            'weights_seg.hdf5',
            custom_objects=custom_objects
        )
        if model_seg is None:
            raise Exception("No se pudo cargar el modelo de segmentación")
        
        print("🎉 Todos los modelos cargados exitosamente")
        return model_class, model_seg
        
    except Exception as e:
        print(f"❌ Error crítico cargando modelos: {str(e)}")
        traceback.print_exc()
        return None, None

model_class, model_seg = load_models()

# 4. Funciones de procesamiento mejoradas
def preprocess_image(image_path):
    """Preprocesamiento mejorado de imágenes"""
    try:
        img = io.imread(image_path)
        
        # Convertir a RGB si es escala de grises
        if len(img.shape) == 2:
            img = np.stack((img,)*3, axis=-1)
        
        # Normalización mejorada
        img = cv2.resize(img, (256, 256))
        img = img.astype(np.float32) / 255.0
        img = (img - img.mean()) / (img.std() + 1e-7)
        
        return np.expand_dims(img, axis=0)
    except Exception as e:
        print(f"Error preprocesando imagen: {str(e)}")
        raise

def postprocess_mask(mask):
    """Postprocesamiento de la máscara para mejor visualización"""
    kernel = np.ones((3,3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)  # Elimina ruido
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel) # Rellena huecos
    return mask

def create_overlay(original_img, mask):
    """Crear overlay con transparencia mejorada"""
    if len(original_img.shape) == 2:  # Si es escala de grises
        overlay_img = cv2.cvtColor(original_img, cv2.COLOR_GRAY2RGBA)
    else:
        overlay_img = cv2.cvtColor(original_img, cv2.COLOR_RGB2RGBA)
    
    # Crear máscara de color rojo semitransparente
    red_mask = np.zeros_like(overlay_img)
    red_mask[mask > 0] = [255, 0, 0, 128]  # RGBA
    
    # Combinar overlay
    return cv2.addWeighted(overlay_img, 1, red_mask, 0.7, 0)

# 5. Función de predicción mejorada
def predict_tumor(image_path, model_class, model_seg):
    try:
        # Preprocesamiento más rápido
        img = cv2.imread(image_path, cv2.IMREAD_COLOR)
        if img is None:
            img = io.imread(image_path)
        
        img = cv2.resize(img, (256, 256))
        img = img.astype(np.float32) / 255.0
        img = (img - img.mean()) / (img.std() + 1e-7)
        img = np.expand_dims(img, axis=0)
        
        # Predicción con timeout
        try:
            class_pred = model_class.predict(img, verbose=0)
            has_tumor = np.argmax(class_pred) == 1
            
            if not has_tumor:
                return {
                    'has_tumor': False,
                    'accuracy': float(np.max(class_pred)),
                    'original_img': None,
                    'mask': None,
                    'overlay_img': None
                }
            
            seg_pred = model_seg.predict(img, verbose=0)
            mask = (seg_pred.squeeze() > 0.3).astype(np.uint8) * 255
            return {
                'has_tumor': True,
                'accuracy': float(np.max(class_pred)),
                'original_img': cv2.imread(image_path),
                'mask': mask,
                'overlay_img': create_overlay(cv2.imread(image_path), mask)
            }
        except Exception as e:
            print(f"Prediction timeout: {str(e)}")
            return None
            
    except Exception as e:
        print(f"Error during prediction: {str(e)}")
        raise



# 6. Rutas de la API
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    if model_class is None or model_seg is None:
        return jsonify({'error': 'Modelos no cargados correctamente'}), 500
        
    if 'file' not in request.files:
        return jsonify({'error': 'No se subió ningún archivo'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Nombre de archivo vacío'}), 400
        
    try:
        analysis_id = datetime.now().strftime('%Y%m%d%H%M%S')
        analysis_folder = os.path.join(app.config['UPLOAD_FOLDER'], f"analysis_{analysis_id}")
        os.makedirs(analysis_folder, exist_ok=True)
        
        original_filename = secure_filename(file.filename)
        original_path = os.path.join(analysis_folder, "original.jpg")
        file.save(original_path)
        
        print(f"⏳ Iniciando predicción para {original_path}...")
        result = predict_tumor(original_path, model_class, model_seg)
        print("✅ Predicción completada")
        
        output_images = {
            'original': f"analysis_{analysis_id}/original.jpg",
            'mask': None,
            'overlay': None
        }

        if result['has_tumor']:
            # Guardar máscara
            mask_path = os.path.join(analysis_folder, "mask.png")
            cv2.imwrite(mask_path, result['mask'])
            output_images['mask'] = f"analysis_{analysis_id}/mask.png"
            
            # Guardar overlay
            overlay_path = os.path.join(analysis_folder, "overlay.png")
            cv2.imwrite(overlay_path, result['overlay_img'])
            output_images['overlay'] = f"analysis_{analysis_id}/overlay.png"
        
        return jsonify({
            'has_tumor': 'true' if result['has_tumor'] else 'false',
            'accuracy': float(result['accuracy']),
            'images': output_images
        })
        
    except Exception as e:
        print(f"🔥 Error durante el procesamiento: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': f"Error durante el procesamiento: {str(e)}"}), 500

@app.route('/static/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# 7. Rutas para el historial
@app.route('/api/history')
def get_history():
    try:
        analyses = []
        upload_dir = app.config['UPLOAD_FOLDER']
        
        # Ordenar por fecha de modificación (más reciente primero)
        folders = sorted([d for d in os.listdir(upload_dir) if d.startswith('analysis_')], 
                        key=lambda x: os.path.getmtime(os.path.join(upload_dir, x)), 
                        reverse=True)
        
        for folder in folders:
            folder_path = os.path.join(upload_dir, folder)
            if os.path.isdir(folder_path):
                original_img = f"{folder}/original.jpg"
                timestamp = folder.replace('analysis_', '')
                timestamp = datetime.strptime(timestamp, '%Y%m%d%H%M%S')
                
                analyses.append({
                    'id': folder,
                    'original': original_img,
                    'date': timestamp.strftime('%d/%m/%Y %H:%M:%S')
                })
        
        return jsonify({'analyses': analyses})
    
    except Exception as e:
        print(f"Error getting history: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/delete/<analysis_id>', methods=['DELETE'])
def delete_analysis(analysis_id):
    try:
        folder_path = os.path.join(app.config['UPLOAD_FOLDER'], analysis_id)
        if os.path.exists(folder_path):
            import shutil
            shutil.rmtree(folder_path)
            return jsonify({'success': True})
        return jsonify({'error': 'Analysis not found'}), 404
    except Exception as e:
        print(f"Error deleting analysis: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    # Configuración específica para Render
    port = int(os.environ.get("PORT", 10000))  # Render usa puerto 10000
    debug_mode = False  # Siempre False en producción
    
    print(f"🚀 Iniciando servidor Flask en puerto {port}...")
    app.run(host='0.0.0.0', port=port, debug=debug_mode)