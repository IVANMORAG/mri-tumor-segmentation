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

        # 2. Parsear JSON y formatear clave privada CORRECTAMENTE
        service_account_info = json.loads(service_account_str)
        
        # Formateo PROFESIONAL de la clave privada
        private_key = service_account_info['private_key']
        if '-----BEGIN PRIVATE KEY-----' not in private_key:
            # Limpiar caracteres extraños y formatear como PEM válido
            private_key = private_key.replace('\\n', '\n').replace(' ', '')
            if '\n' not in private_key:
                private_key = '\n'.join([private_key[i:i+64] for i in range(0, len(private_key), 64)])
            service_account_info['private_key'] = (
                "-----BEGIN PRIVATE KEY-----\n" +
                private_key +
                "\n-----END PRIVATE KEY-----\n"
            )
        
        # 3. Configuración ÓPTIMA para PyDrive2
        settings = {
            "client_config_backend": "service",
            "service_config": {
                "client_json": service_account_info,  # Como dict, no string
                "client_user_email": service_account_info['client_email']
            }
        }

        # 4. Autenticación con manejo de errores mejorado
        gauth = GoogleAuth(settings=settings)
        try:
            gauth.ServiceAuth()
        except Exception as auth_error:
            if "DECODER routines" in str(auth_error):
                raise ValueError("Formato de clave privada inválido. Verifica que el JSON esté completo y bien formateado")
            raise
        
        return GoogleDrive(gauth)
        
    except Exception as e:
        print(f"❌ Error FATAL en autenticación: {str(e)}")
        raise
