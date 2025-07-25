from modules import setup
import os
import sys
import subprocess
import time

setup.clearTerminal()

APP_VERSION = 'v.0.1.1-beta'

# Check if running in a virtual enviorment
if not setup.is_virtual_environment():
    python_executable = setup.get_python_executable()
    if not os.path.exists(python_executable):
        setup.create_virtualenv()

    script_path = os.path.abspath(__file__)
    print(f"Script running from global interpreter. Re-running program inside virtual environment.")

    env = os.environ.copy()
    env["BOOTSTRAPPED"] = "1"  # ✅ pass flag

    if os.name == 'nt':
        subprocess.run([python_executable, script_path] + sys.argv[1:], env=env)
        sys.exit(0)
    else:
        os.execve(python_executable, [python_executable, script_path] + sys.argv[1:], env)

    
# ✅ Now you're in the virtual environment
if os.getenv("BOOTSTRAPPED") == "1":
    print("Switched to Virtual enviorment")

print('Launching Application.')
print(f'App version: {APP_VERSION}')
# Verify configuration
verify = setup.verify()

if not verify.preferences:
    print('Initiating first setup.')
    setup_needed = True
elif not verify.dependencies and verify.preferences:
    print('Found missing dependencies despite existing setup.')
    setup_needed = True
else:
    setup_needed = False


if setup_needed:
    if not verify.dependencies:
        print('\nInstalling missing dependencies:')
        setup.install_dependencies()
    if not os.path.exists('./requirements.txt'):
        raise FileNotFoundError("Missing requirements.txt in project root.")


    confirm_setup = setup.verify()
    if confirm_setup.dependencies:
        if not os.path.exists('./cache'):
            os.mkdir('./cache')
        with open('./cache/preferences.json', 'w', encoding='UTF-8') as file:
            string_to_write = '{"setupComplete": true}'
            file.write(string_to_write)

    final_verify = setup.verify()
    if final_verify.preferences:
        setup.write_app_version(APP_VERSION)
        print('Setup complete, starting the program.')
        setup_needed = False
        time.sleep(1)
    else:
        print('Setup failed. Please restart the program.\nQuitting...')
        quit()
    setup.write_app_version(APP_VERSION)


if not setup_needed:
    setup.clearTerminal()
    setup.write_app_version(APP_VERSION)
    subprocess.run([setup.get_python_executable(), "-m", "streamlit", "run", "Home.py"])