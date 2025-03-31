import cv2
import numpy as np

def postprocess_mask(mask):
    """Postprocesamiento de la máscara para mejor visualización"""
    kernel = np.ones((3,3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)  # Elimina ruido
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel) # Rellena huecos
    return mask