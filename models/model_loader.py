from drive_auth import authenticate
import io
import tensorflow as tf
from utils.custom_metrics import tversky, tversky_loss, focal_tversky
import os


# Configura esto con tus IDs reales
MODEL_IDS = {
    'classification': os.getenv('CLASSIFICATION_MODEL_ID'),
    'segmentation': os.getenv('SEGMENTATION_MODEL_ID')
}

def load_model_from_drive(drive, file_id, model_name):
    try:
        # Crea un archivo manejador
        model_file = drive.CreateFile({'id': file_id})
        
        # Crea un buffer en memoria
        model_buffer = io.BytesIO()
        model_file.GetContentIOBuffer(model_buffer)
        
        # Mueve el cursor al inicio del buffer
        model_buffer.seek(0)
        
        # Carga el modelo con las métricas personalizadas
        model = tf.keras.models.load_model(
            model_buffer,
            custom_objects={
                'tversky_loss': tversky_loss,
                'focal_tversky': focal_tversky,
                'tversky': tversky
            },
            compile=False
        )
        
        print(f"✅ {model_name} cargado desde Google Drive")
        return model
    except Exception as e:
        print(f"❌ Error cargando {model_name}: {str(e)}")
        raise

def load_models():
    try:
        print("⏳ Autenticando con Google Drive...")
        drive = authenticate()
        
        print("⏳ Cargando modelos desde Google Drive...")
        model_class = load_model_from_drive(drive, MODEL_IDS['classification'], "Modelo de Clasificación")
        model_seg = load_model_from_drive(drive, MODEL_IDS['segmentation'], "Modelo de Segmentación")
        
        return {
            'classification': model_class,
            'segmentation': model_seg
        }
    except Exception as e:
        print(f"❌ Error inicializando modelos: {str(e)}")
        raise
