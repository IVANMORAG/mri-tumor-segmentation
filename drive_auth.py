import os
import json
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

def authenticate():
    try:
        # 1. Carga las credenciales desde variables de entorno
        service_account_info = os.getenv('GOOGLE_SERVICE_ACCOUNT')
        if not service_account_info:
            raise ValueError("Variable GOOGLE_SERVICE_ACCOUNT no configurada")
        
        # 2. Configura la autenticación
        gauth = GoogleAuth()
        gauth.service_account_info = json.loads(service_account_info)
        gauth.service_account_credentials = json.loads(service_account_info)
        gauth.CommandLineAuth()  # Autenticación no interactiva
        
        return GoogleDrive(gauth)
    except Exception as e:
        print(f"❌ Error de autenticación: {str(e)}")
        raise
