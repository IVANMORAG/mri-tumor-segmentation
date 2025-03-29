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