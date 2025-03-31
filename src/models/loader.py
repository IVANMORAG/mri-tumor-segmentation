import tensorflow as tf
from .custom_metrics import tversky_loss, focal_tversky, tversky
import traceback

class ModelLoader:
    @staticmethod
    def load_models():
        try:
            print("⏳ Cargando modelos...")
            custom_objects = {
                'tversky_loss': tversky_loss,
                'focal_tversky': focal_tversky,
                'tversky': tversky
            }
            
            model_class = tf.keras.models.load_model(
                'weights/weights.hdf5',
                custom_objects=custom_objects
            )
            
            model_seg = tf.keras.models.load_model(
                'weights/weights_seg.hdf5',
                custom_objects=custom_objects
            )
            
            print("✅ Modelos cargados exitosamente")
            return model_class, model_seg
            
        except Exception as e:
            print(f"❌ Error cargando modelos: {str(e)}")
            traceback.print_exc()
            return None, None