import os
import json
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

def authenticate():
    try:
        # 1. Cargar credenciales desde variables de entorno
        service_account_info = json.loads(os.getenv('GOOGLE_SERVICE_ACCOUNT'))
        
        # 2. Configuración adicional requerida
        settings = {
            "client_config_backend": "service",
            "service_config": {
                "client_json": service_account_info,
                "client_user_email": service_account_info['client_email']  # ¡Esta línea faltaba!
            }
        }
        
        # 3. Configurar autenticación
        gauth = GoogleAuth(settings=settings)
        gauth.ServiceAuth()
        
        return GoogleDrive(gauth)
    except Exception as e:
        print(f"❌ Error grave en autenticación: {str(e)}")
        raise
