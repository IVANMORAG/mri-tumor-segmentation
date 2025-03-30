import os
import json
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

def authenticate():
    try:
        # 1. Obtener el JSON como string desde variables de entorno
        service_account_str = os.getenv('GOOGLE_SERVICE_ACCOUNT')
        if not service_account_str:
            raise ValueError("❌ Variable GOOGLE_SERVICE_ACCOUNT no configurada")

        # 2. Convertir a dict y reparar formato de clave privada
        try:
            service_account_info = json.loads(service_account_str)
            
            # Asegurar que la clave privada tenga formato correcto
            private_key = service_account_info.get('private_key', '')
            if '-----BEGIN PRIVATE KEY-----' not in private_key:
                service_account_info['private_key'] = (
                    '-----BEGIN PRIVATE KEY-----\n' +
                    private_key.replace('\\n', '\n') +
                    '\n-----END PRIVATE KEY-----'
                )
            
            # Reconstruir el JSON con las correcciones
            corrected_json = json.dumps(service_account_info)
            
        except json.JSONDecodeError:
            raise ValueError("❌ El JSON de credenciales no es válido")

        # 3. Configuración para PyDrive2
        settings = {
            "client_config_backend": "service",
            "service_config": {
                "client_json": corrected_json,
                "client_user_email": service_account_info['client_email']
            }
        }

        # 4. Autenticación
        gauth = GoogleAuth(settings=settings)
        gauth.ServiceAuth()
        
        return GoogleDrive(gauth)
        
    except Exception as e:
        print(f"❌ Error crítico en autenticación: {str(e)}")
        raise
