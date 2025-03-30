import os
import json
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

def authenticate():
    try:
        # 1. Obtener JSON
        service_account_str = os.getenv('GOOGLE_SERVICE_ACCOUNT')
        if not service_account_str:
            raise ValueError("❌ GOOGLE_SERVICE_ACCOUNT no configurado")

        # 2. Parsear (no necesita modificaciones, el formato ya es correcto)
        service_account = json.loads(service_account_str)
        
        # 3. Configuración para PyDrive
        settings = {
            "client_config_backend": "service",
            "service_config": {
                "client_json": service_account,  # Envía el dict directamente
                "client_user_email": service_account['client_email']
            }
        }

        # 4. Autenticación
        gauth = GoogleAuth(settings=settings)
        gauth.ServiceAuth()
        return GoogleDrive(gauth)
        
    except Exception as e:
        print(f"❌ Error FATAL: {str(e)}")
        raise
