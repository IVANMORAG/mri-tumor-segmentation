from flask import Blueprint, jsonify, current_app
from datetime import datetime
import os
import traceback
import shutil

history_bp = Blueprint('history', __name__)

@history_bp.route('/api/history')
def get_history():
    try:
        analyses = []
        upload_dir = current_app.config['UPLOAD_FOLDER']
        
        # Ordenar por fecha de modificación (más reciente primero)
        folders = sorted([d for d in os.listdir(upload_dir) if d.startswith('analysis_')], 
                        key=lambda x: os.path.getmtime(os.path.join(upload_dir, x)), 
                        reverse=True)
        
        for folder in folders[:100]:  # Limitar a 100 análisis más recientes
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

@history_bp.route('/api/delete/<analysis_id>', methods=['DELETE'])
def delete_analysis(analysis_id):
    try:
        folder_path = os.path.join(current_app.config['UPLOAD_FOLDER'], analysis_id)
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)
            return jsonify({'success': True})
        return jsonify({'error': 'Analysis not found'}), 404
    except Exception as e:
        print(f"Error deleting analysis: {str(e)}")
        return jsonify({'error': str(e)}), 500