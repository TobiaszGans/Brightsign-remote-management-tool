import os
import json
import subprocess
from dataclasses import dataclass
import venv
import sys

#-----------VENV-----------

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
VENV_DIR = os.path.join(PROJECT_ROOT, ".venv")
PYTHON_EXECUTABLE = os.path.join(VENV_DIR, "Scripts", "python.exe" if os.name == "nt" else "bin/python")

def is_virtual_environment():
    return (
        hasattr(sys, 'real_prefix') or
        (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix) or
        os.getenv('VIRTUAL_ENV') is not None
    )

def create_virtualenv():
    print(f"No virtual enviorment found. Creating virtual environment at: {VENV_DIR}")
    venv.create(VENV_DIR, with_pip=True)

def get_python_executable():
    return PYTHON_EXECUTABLE

#-----------SETUP-----------

def strip_packages(lines) -> list:
    for i in range(len(lines)):
        name = lines[i].split('==')[0]
        lines[i] = name
    return lines

def get_installed_packages() -> list:
    pip_executable = os.path.join(VENV_DIR, "Scripts", "pip.exe" if os.name == "nt" else "bin/pip")
    pip_check = subprocess.check_output([pip_executable, "freeze"]).decode('utf-8')
    installed_packages = pip_check.split()
    installed_packages = strip_packages(installed_packages)
    return installed_packages

def get_required_packages() -> list:
    with open('./requirements.txt', 'r') as file:
        required_packages = file.read().split()
    required_packages = strip_packages(required_packages)
    return required_packages

class verify:
    preferences: bool
    dependencies: bool

    def __init__(self):
        # Check for preferences file and verify if setup was complete
        if os.path.exists('./cache/preferences.json'):
            try:
                with open('./cache/preferences.json', 'r', encoding='UTF-8') as preference_file:
                    file_data = json.load(preference_file)
                    self.preferences = file_data.get('setupComplete', False)
            except (json.JSONDecodeError, IOError):
                self.preferences = False
        else:
            self.preferences = False

        # Check if all dependencies were installed
        installed_packages = get_installed_packages()
        required_packages = get_required_packages()

        required_set = set(required_packages)
        installed_set = set(installed_packages)
        self.dependencies = required_set.issubset(installed_set)


def install_dependencies():
    installed_packages = get_installed_packages()
    required_packages = get_required_packages()

    required_set = set(required_packages)
    installed_set = set(installed_packages)

    missing_packages = required_set.difference(installed_set)

    pip_executable = os.path.join(VENV_DIR, "Scripts", "pip.exe" if os.name == "nt" else "bin/pip")

    print('Updating pip')
    #-m pip install --upgrade pip
    python_executable = os.path.join(VENV_DIR, "Scripts", "python.exe" if os.name == "nt" else "bin/python")

    result = subprocess.run(
        [python_executable, "-m", "pip", "install", "--upgrade", "pip"],
        text=True
    )

    for package in missing_packages:
        print(f"\nInstalling: {package}")
        result = subprocess.run(
            [pip_executable, "install", package],
            #capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print(f"Failed to install {package}")
            print(result.stderr)
        else:
            print(f"Installed {package}")

def write_app_version(version):
    with open('./cache/preferences.json', 'r') as file:
        file_data = json.load(file)
    version_exists = "currentVersion" in file_data
    if not version_exists:
        version_key = {"currentVersion":version}
        file_data.update(version_key)
        with open('./cache/preferences.json', 'w') as file:
            file.write(json.dumps(file_data))
    if version_exists:
        file_data['currentVersion'] = version
        with open('./cache/preferences.json', 'w') as file:
            file.write(json.dumps(file_data))


#-----------CLI UTILS-----------
            
def clearTerminal():
    os.system('cls' if os.name=='nt' else 'clear')