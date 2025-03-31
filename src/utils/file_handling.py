import os
from datetime import datetime
from werkzeug.utils import secure_filename

def create_analysis_folder(upload_folder):
    analysis_id = datetime.now().strftime('%Y%m%d%H%M%S')
    analysis_folder = os.path.join(upload_folder, f"analysis_{analysis_id}")
    os.makedirs(analysis_folder, exist_ok=True)
    return analysis_folder, analysis_id

def save_uploaded_file(file, folder_path):
    original_filename = secure_filename(file.filename)
    original_path = os.path.join(folder_path, "original.jpg")
    file.save(original_path)
    return original_path