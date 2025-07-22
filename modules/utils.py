import streamlit as st
import pandas as pd
import os, shutil, stat, time, subprocess, json

def st_init(key, state):
    if key not in st.session_state:
        st.session_state[key] = state

def go_to(key, state):
    st.session_state[key] = state

def clear_screen():
    # Use at the end of a short state or in an emtpy state before a long process
    display = st.empty()
    # the below is the fix
    for i in range(0, 100):
        st.markdown(" ")

def upload_template():
    template_list = [
        ['192.168.1.47', 'Password123','USD1234567'],
        ['usd81233212.corpnet1.com', 'paSSword321','']
    ]
    template = pd.DataFrame(template_list, columns=['address','password','serial'])
    return template.to_csv(index=False)


def handle_remove_readonly(func, path, _):
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception as e:
        print(f"Error force-deleting {path}: {e}")

def clean_folder(folder_path):
    absolute_path = os.path.abspath(folder_path)
    if not os.path.exists(absolute_path):
        return

    for filename in os.listdir(absolute_path):
        file_path = os.path.join(absolute_path, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path, onerror=handle_remove_readonly)
        except Exception as e:
            print(f'Failed to delete {file_path}. Reason: {e}')

    # Try to remove the folder itself after cleaning
    try:
        time.sleep(1)
        os.rmdir(absolute_path)
    except Exception as e:
        print(f"Could not delete folder {absolute_path}: {e}")

def open_in_explorer(path):
    absolute_path = os.path.abspath(path)
    subprocess.Popen(f'explorer "{absolute_path}"')

def check_cache() -> bool:
    cache_folder_exists = os.path.exists('./cache/autoruns/')
    if cache_folder_exists:
        autorun_folders = os.listdir('./cache/autoruns/')
    return cache_folder_exists and autorun_folders

def get_cache() -> list:
    folders = os.listdir('./cache/autoruns')
    folders.reverse()
    return folders

def select_autourn():
    if not check_cache():
        autorun = st.file_uploader('Please upload the autorun to be installed on the players.', type='zip')
        if autorun is not None:
            autorun = autorun.getvalue()
        return autorun
    else:
        options = get_cache()
        options.append('Use a new Autorun')
        ar_selection = st.selectbox('Select the autourn', options=options, index=None)
        if ar_selection == 'Use a new Autorun':
            autorun = st.file_uploader('Please upload the autorun to be installed on the players.', type='zip')
            if autorun is not None:
                autorun = autorun.getvalue()
        elif ar_selection == None:
            return
        else:
            with open(f'./cache/autoruns/{ar_selection}/autorun.zip', 'rb') as file:
                autorun = file.read()
        return autorun
    
def validate_csv(players:pd.DataFrame) -> list:
    expected_columns = ['address','password','serial']
    required_columns = set(['address','password'])
    df_columns = players.columns.values.tolist()
    df_columns_set = set(df_columns)
    
    columns_invalid = expected_columns != df_columns
    has_required_columns = required_columns.issubset(df_columns_set)
    if not has_required_columns:
        valid = False
        error_message = "The file must contain the columns: 'address', 'password', and 'serial'. The uploaded file does not match this structure."
        return[valid, error_message]

    address_invalid = players['address'].isna().any()
    password_invalid = players['password'].isna().any()

    if columns_invalid or address_invalid or password_invalid:
        st.session_state['error'] = True
        error_message = "The uploaded file has the following issue(s): "

        issues = []

        if columns_invalid:
            issues.append("The file must contain the columns: 'address', 'password', and 'serial'. The uploaded file does not match this structure.")
        if address_invalid:
            issues.append("Some cells in the 'address' column are empty. All addresses must be provided.")
        if password_invalid:
            issues.append("Some cells in the 'password' column are empty. All passwords must be provided.")

        error_message += " ".join(issues)
        valid = False
        return[valid, error_message]
    else:
        valid = True
        error_message = None
        return[valid, error_message]