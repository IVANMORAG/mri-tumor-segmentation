import numpy as np  # Añade esta línea al inicio del archivo
import cv2
from datetime import datetime
import traceback
import os
from flask import jsonify, request
from src.models.loader import ModelLoader
from src.processing.preprocess import preprocess_image
from src.processing.postprocess import postprocess_mask
from src.processing.visualization import create_overlay
from src.utils.file_handling import create_analysis_folder, save_uploaded_file
import io
from skimage import io as skio  # Para evitar conflicto con io de Python

def setup_api_routes(app, model_class, model_seg):
    @app.route('/api/predict', methods=['POST'])
    def predict():
        if model_class is None or model_seg is None:
            return jsonify({'error': 'Modelos no cargados correctamente'}), 500
            
        if 'file' not in request.files:
            return jsonify({'error': 'No se subió ningún archivo'}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Nombre de archivo vacío'}), 400
            
        try:
            analysis_folder, analysis_id = create_analysis_folder(app.config['UPLOAD_FOLDER'])
            original_path = save_uploaded_file(file, analysis_folder)
            
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

    # Mantener compatibilidad con la ruta anterior
    @app.route('/predict', methods=['POST'])
    def predict_legacy():
        return predict()
    @app.route('/api/history')
    def get_history():
        try:
            analyses = []
            upload_dir = app.config['UPLOAD_FOLDER']
            
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

def predict_tumor(image_path, model_class, model_seg):
    try:
        img = preprocess_image(image_path)
        
        # Clasificación
        class_pred = model_class.predict(img, verbose=0)
        has_tumor = np.argmax(class_pred) == 1
        accuracy = float(np.max(class_pred))
        
        # Leer imagen original para visualización
        original_img = cv2.imread(image_path)
        if original_img is None:
            original_img = skio.imread(image_path)
        
        mask = None
        overlay_img = None
        
        if has_tumor:
            # Segmentación con umbral ajustado
            seg_pred = model_seg.predict(img, verbose=0)
            mask = (seg_pred.squeeze() > 0.3).astype(np.uint8) * 255
            
            # Redimensionar máscara al tamaño original
            mask_resized = cv2.resize(mask, (original_img.shape[1], original_img.shape[0]), 
                                    interpolation=cv2.INTER_NEAREST)
            
            # Postprocesamiento
            mask_resized = postprocess_mask(mask_resized)
            
            # Crear overlay
            overlay_img = create_overlay(original_img, mask_resized)
        
        return {
            'has_tumor': has_tumor,
            'accuracy': accuracy,
            'original_img': original_img,
            'mask': mask_resized if has_tumor else None,
            'overlay_img': overlay_img[..., :3] if has_tumor else None
        }
    except Exception as e:
        print(f"Error durante la predicción: {str(e)}")
        raise