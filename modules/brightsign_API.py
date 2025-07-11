from dataclasses import dataclass
import os
import subprocess
import requests
from requests.auth import HTTPDigestAuth

@dataclass
class credentials:
    url:str
    login:str
    password:str
    primary_port:int
    secondary_port:int
    serial:str

    def __init__(self, url:str, password:str, primary_port:int=8080, secondary_port:int=80, serial:str=None):
        self.url = url
        self.password = password
        self.login = 'admin'
        self.primary_port = primary_port
        self.secondary_port = secondary_port
        self.serial = serial

def ping(url):
    if os.sys.platform.lower() == 'win32':
        param = '-n'
    else:
        param = '-c'
    try:
        result = subprocess.run(
            ['ping', param, '1', url],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True
        )
        output = result.stdout.lower()

        # Conditions for a successful ping
        if (
            'reply from' in output and
            'destination host unreachable' not in output and
            'request timed out' not in output
        ):
            return True
        else:
            return False
    except Exception:
        return False
    
def reachUrl(IP, port):
    url = f"http://{IP}:{port}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code in (200, 401):
            return True
        else:
            return f'HTTP {response.status_code}'
    except requests.RequestException:
        return False
    

def init_login(url, port, login, password) -> bool:
    endpoint = '/api/v1/info/'
    full_url = f'http://{url}:{port}{endpoint}'
    r = requests.get(full_url, auth=HTTPDigestAuth(login, password))
    return r


def disable_autorun(url, port, login, password):
    endpoint = '/api/v1/control/reboot'
    full_url = f'http://{url}:{port}{endpoint}'
    body = {"autorun":"disable"}
    r = requests.put(full_url, auth=HTTPDigestAuth(login, password), json=body)
    return r

def format_storage(url, port, login, password):
    endpoint = '/api/v1/storage/sd/'
    full_url = f'http://{url}:{port}{endpoint}'
    body = {
    "fs": "exfat"
    }
    r = requests.delete(full_url, auth=HTTPDigestAuth(login, password), json=body)
    return r

def upload_file(url, port, login, password, file, path:str='sd/'):
    endpoint = f'/api/v1/files/{path}'
    full_url = f'http://{url}:{port}{endpoint}'
    r = requests.put(full_url, files=file, auth=HTTPDigestAuth(login, password))
    return r

def reboot(url, port, login, password):
    endpoint = '/api/v1/control/reboot'
    full_url = f'http://{url}:{port}{endpoint}'
    r = requests.put(full_url, auth=HTTPDigestAuth(login, password))
    return r