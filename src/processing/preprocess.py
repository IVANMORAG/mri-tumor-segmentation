import cv2
import numpy as np
from skimage import io

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