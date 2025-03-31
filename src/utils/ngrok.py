import subprocess
import time
import threading

def start_ngrok(domain, port):
    def run():
        time.sleep(2)
        process = subprocess.Popen(
            ['ngrok', 'http', '--domain='+domain, str(port)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        time.sleep(2)
        print(f"\n* NGROK URL FIJADA: https://{domain} -> http://localhost:{port} *\n")
        return process
    
    ngrok_thread = threading.Thread(target=run)
    ngrok_thread.daemon = True
    ngrok_thread.start()
    return ngrok_thread