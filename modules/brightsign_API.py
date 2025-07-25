from dataclasses import dataclass
from requests.auth import HTTPDigestAuth
import base64, json, os, subprocess, requests
from io import BytesIO
from PIL import Image

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
    

def init_login(url, port, login, password):
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

def capture_snapshot(url, port, login, password):
    endpoint = '/api/v1/snapshot/'
    full_url = f'http://{url}:{port}{endpoint}'
    body = {
        "width": 960,
        "height": 540
    }
    r = requests.post(full_url, auth=HTTPDigestAuth(login, password), json=body)
    return r

def capture_snapshot_thumbnail(url, port, login, password):
    response = capture_snapshot(url, port, login, password)
    payload = response.text
    payload_json = json.loads(payload)
    base64_image = payload_json['data']['result']['remoteSnapshotThumbnail']
    if base64_image.startswith("data:image"):
        base64_image = base64_image.split(",")[1]
    image_bytes = base64.b64decode(base64_image)
    image = Image.open(BytesIO(image_bytes))
    return image

def get_device_name(url, port, login, password):
    response = init_login(url, port, login, password)
    device_info = json.loads(response.text)
    return device_info['data']['result']['networking']['result']['name']

def get_logs(url, port, login, password):
    endpoint = '/api/v1/logs/'
    full_url = f'http://{url}:{port}{endpoint}'
    r = requests.get(full_url, auth=HTTPDigestAuth(login, password))
    r_json = json.loads(r.text)
    logs = r_json['data']['result']
    return logs