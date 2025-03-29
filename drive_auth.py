import os
import json
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

def authenticate():
    try:
        # 1. Carga las credenciales como SERVICE ACCOUNT
        service_account_json = os.getenv('GOOGLE_SERVICE_ACCOUNT')
        if not service_account_json:
            raise ValueError("❌ Falta la variable GOOGLE_SERVICE_ACCOUNT")
        
        # 2. Configuración directa sin interacción
        gauth = GoogleAuth()
        
        # Forzamos el modo Service Account
        gauth.service_account_info = json.loads(service_account_json)
        gauth.settings["client_config_backend"] = "service"
        gauth.settings["service_config"] = {
            "client_json": service_account_json
        }
        
        # Autenticación silenciosa
        gauth.ServiceAuth()
        
        return GoogleDrive(gauth)
        
    except Exception as e:
        print(f"❌ Error grave en autenticación: {str(e)}")
        raise
