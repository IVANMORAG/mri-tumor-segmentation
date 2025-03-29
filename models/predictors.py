import numpy as np
import cv2
from skimage import io
from utils.image_processing import preprocess_image, postprocess_mask, create_overlay

def predict_tumor(image_path, models):
    try:
        img = preprocess_image(image_path)
        model_class = models['classification']
        model_seg = models['segmentation']
        
        # Clasificación
        class_pred = model_class.predict(img, verbose=0)
        has_tumor = np.argmax(class_pred) == 1
        accuracy = float(np.max(class_pred))
        
        # Leer imagen original para visualización
        original_img = cv2.imread(image_path)
        if original_img is None:
            original_img = io.imread(image_path)
        
        mask = None
        overlay_img = None
        
        if has_tumor and model_seg:
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