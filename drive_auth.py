import os
import json
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

def authenticate():
    try:
        # 1. Obtener JSON como string
        service_account_str = os.getenv('GOOGLE_SERVICE_ACCOUNT')
        if not service_account_str:
            raise ValueError("❌ GOOGLE_SERVICE_ACCOUNT no configurado")
        
        # 2. Asegurarnos que tenemos un diccionario con las credenciales
        if isinstance(service_account_str, dict):
            # Ya es un diccionario
            service_account = service_account_str
        else:
            # Es un string, tenemos que parsearlo
            try:
                service_account = json.loads(service_account_str)
            except json.JSONDecodeError:
                raise ValueError("❌ GOOGLE_SERVICE_ACCOUNT no es un JSON válido")
        
        # 3. Configuración para PyDrive (usando client_json_dict)
        settings = {
            "client_config_backend": "service",
            "service_config": {
                "client_json_dict": service_account  # Pasamos el diccionario completo
            }
        }
        
        # 4. Autenticación
        gauth = GoogleAuth(settings=settings)
        gauth.ServiceAuth()
        return GoogleDrive(gauth)
        
    except Exception as e:
        print(f"❌ Error FATAL: {str(e)}")
        raise
