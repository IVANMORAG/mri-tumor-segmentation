import cv2
import numpy as np

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