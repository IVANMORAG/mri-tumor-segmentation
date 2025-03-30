import os
import json
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

def authenticate():
    try:
        # 1. Obtener el JSON desde variables de entorno
        service_account_str = os.getenv('GOOGLE_SERVICE_ACCOUNT')
        if not service_account_str:
            raise ValueError("❌ Variable GOOGLE_SERVICE_ACCOUNT no configurada")

        # 2. Parsear JSON y formatear clave privada
        service_account_info = json.loads(service_account_str)
        
        # Formatear correctamente la clave privada (¡ESTE ES EL CAMBIO CLAVE!)
        private_key = service_account_info['private_key']
        if '\\n' not in private_key and '\n' not in private_key:
            # Insertar saltos de línea cada 64 caracteres (formato PEM estándar)
            formatted_key = '\n'.join([private_key[i:i+64] for i in range(0, len(private_key), 64)])
            service_account_info['private_key'] = (
                "-----BEGIN PRIVATE KEY-----\n" +
                formatted_key +
                "\n-----END PRIVATE KEY-----"
            )
        
        # 3. Configuración para PyDrive2
        settings = {
            "client_config_backend": "service",
            "service_config": {
                "client_json": json.dumps(service_account_info),
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
