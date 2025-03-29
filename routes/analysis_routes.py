from flask import Blueprint, request, jsonify, send_from_directory, current_app
from werkzeug.utils import secure_filename
from datetime import datetime
import traceback
import os
import cv2
from models.predictors import predict_tumor

analysis_bp = Blueprint('analysis', __name__)

@analysis_bp.route('/predict', methods=['POST'])
def predict():
    models = current_app.config['MODELS']
    if not models or not models['classification']:
        return jsonify({'error': 'Modelos no cargados correctamente'}), 500
        
    if 'file' not in request.files:
        return jsonify({'error': 'No se subió ningún archivo'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Nombre de archivo vacío'}), 400
        
    try:
        analysis_id = datetime.now().strftime('%Y%m%d%H%M%S')
        analysis_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], f"analysis_{analysis_id}")
        os.makedirs(analysis_folder, exist_ok=True)
        
        original_filename = secure_filename(file.filename)
        original_path = os.path.join(analysis_folder, "original.jpg")
        file.save(original_path)
        
        print(f"⏳ Iniciando predicción para {original_path}...")
        result = predict_tumor(original_path, models)
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

@analysis_bp.route('/static/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)