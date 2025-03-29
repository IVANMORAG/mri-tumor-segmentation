import os
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

def authenticate():
    gauth = GoogleAuth()
    
    # Configura rutas para Render
    client_secrets = os.getenv('PYDRIVE_CLIENT_SECRET_FILE', 'client_secrets.json')
    credentials_file = os.getenv('PYDRIVE_CREDENTIALS_FILE', 'mycreds.txt')
    
    gauth.LoadCredentialsFile(credentials_file)
    
    if gauth.credentials is None:
        if os.path.exists(client_secrets):
            gauth.LocalWebserverAuth()
        else:
            raise Exception("Archivo client_secrets.json no encontrado")
    elif gauth.access_token_expired:
        gauth.Refresh()
    else:
        gauth.Authorize()
    
    gauth.SaveCredentialsFile(credentials_file)
    
    return GoogleDrive(gauth)