import os
import json
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

def authenticate():
    try:
        # 1. Obtener JSON como string
        sa_json_str = os.getenv('GOOGLE_SERVICE_ACCOUNT')
        if not sa_json_str:
            raise ValueError("❌ GOOGLE_SERVICE_ACCOUNT no está configurado")

        # 2. Parsear a dict para extraer el email
        sa_info = json.loads(sa_json_str)
        
        # 3. Configuración EXACTA que necesita PyDrive2
        settings = {
            "client_config_backend": "service",
            "service_config": {
                "client_json": sa_json_str,  # String original
                "client_user_email": sa_info['client_email']
            }
        }

        # 4. Autenticación
        gauth = GoogleAuth(settings=settings)
        gauth.ServiceAuth()
        
        return GoogleDrive(gauth)
        
    except Exception as e:
        print(f"❌ Error crítico: {str(e)}")
        raise
