import streamlit as st
import pandas as pd
import os, shutil, stat, time, subprocess, keyboard, threading
from .brightsign_API import credentials, ping, reachUrl, init_login
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor

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
    
def validate_csv(players: pd.DataFrame) -> list:
    expected_columns = {'address', 'password', 'serial'}
    required_columns = {'address', 'password'}
    df_columns_set = set(players.columns)

    missing_columns = expected_columns - df_columns_set
    has_required_columns = required_columns.issubset(df_columns_set)

    if not has_required_columns:
        valid = False
        error_message = f"The file must contain the columns: {', '.join(expected_columns)}. The uploaded file does not match this structure."
        return [valid, error_message]

    address_invalid = players['address'].isna().any()
    password_invalid = players['password'].isna().any()

    if missing_columns or address_invalid or password_invalid:
        st.session_state['error'] = True
        error_message = "The uploaded file has the following issue(s): "
        issues = []

        if missing_columns:
            issues.append(f"Missing columns: {', '.join(missing_columns)}.")
        if address_invalid:
            issues.append("Some cells in the 'address' column are empty.")
        if password_invalid:
            issues.append("Some cells in the 'password' column are empty.")

        error_message += " ".join(issues)
        valid = False
        return [valid, error_message]

    return [True, None]

    
def shutdown():
    # Close streamlit browser tab
    keyboard.press_and_release('ctrl+w')
    # Terminate streamlit python process
    time.sleep(2)
    os._exit(0)

def menu(key):
    c1,c2 = st.columns([1,1])
    with c1:
        if st.button('Single Player', use_container_width=True, disabled=False):
            go_to(key, 'single_player')
            st.rerun()
    with c2:
        if st.button('Multiple Players', use_container_width=True, disabled=False):
            go_to(key, 'multi_player')
            st.rerun()

def single_player_input(key:str, next_step:str='single_verify', use_continue_button:bool=True):
    '''
    Goes to next_step or returns a bool. Sets following streamlit session states:\n
    st.session_state.URL\n
    st.session_state.password\n
    st.session_state.serial
    '''
    st.markdown('Please fill out the following inputs:')
    url = st.text_input('Player URL or IP address. Please do not include the 8080 port number.')
    password = st.text_input('The player password',type='password')
    serial = st.text_input('Player serial number (optional)')

    if url.strip() == '' or password.strip() == '':
        disable_continue = True
    else:
        st.session_state.url = url.strip()
        st.session_state.password = password.strip()
        st.session_state.serial = serial.strip()
        disable_continue = False
    if use_continue_button:
        st.button('Continue', on_click=lambda: go_to(key, next_step), disabled=disable_continue)
    else:
        return not disable_continue
    

@dataclass
class verify_player_info:
    player: credentials
    ping: bool
    dws: bool
    login: bool

    def __init__(self, address:str, password:str, serial:str=None):
        
        ping_bool = ping(address)
        self.ping = ping_bool

        player = credentials(url=address, password=password, serial=serial)

        dws_bool = reachUrl(player.url,player.primary_port)
        if not dws_bool:
            dws_bool = reachUrl(player.url, player.secondary_port)
            if dws_bool:
                player.primary_port = player.secondary_port
        self.dws = dws_bool
        if dws_bool:
            api_login = init_login(url=player.url, port=player.primary_port, password=player.password)
            if api_login.status_code == 200:
                self.login = True
            elif api_login.status_code == 401:
                api_login = init_login(url=player.url, port=player.primary_port, password=player.serial)
                if api_login.status_code == 200:
                    player.password = player.serial
                    self.login = True
                else:
                    self.login = False
            else:
                self.login = False
        else:
            self.login = False

        self.player = player

def multi_player_input(key:str, next_step:str='multi_verify', performance_warining:bool= False, use_continue_button:bool=True, custom_template=None):
    '''
    When use_continue_button is True (default): 
    Sets a pandas Data Frame with the player info as st.session_state.players and goes to the next session state\n
    When use_continue_button is False: 
    Returns the Data Frame\n
    Performance warning may be turned on by setting performance_warining to True.
    '''

    playerfile = st.file_uploader('Please upload a csv file containing device addresses, device passwords, and device serial numbers (optional).', type='csv')
    if custom_template is None:
        template = upload_template()
    else:
        template = custom_template

    if performance_warining:
        st.info('Please keep in mind that going over 20 devices may result in performance issues.')

    st.download_button('Download csv file template', data=template, file_name='Player upload template.csv')

    if use_continue_button:
        if playerfile == None:
            disable_continue = True
        else:
            st.session_state.players = pd.read_csv(playerfile)
            disable_continue = False
        st.button('Continue', on_click=lambda:go_to(key, next_step), disabled=disable_continue)
    else:
        return pd.read_csv(playerfile)

@dataclass    
class multi_verify:
    input_df:pd.DataFrame
    output_df:pd.DataFrame
    reject_df:pd.DataFrame
    dropped_rows: int
    contains_valid_records:bool
    error_message:str

    def __init__(self, df):
        self.input_df = df
        df['login'] = False
        lock = threading.Lock()
        
        def verify_player(index, address: str, password: str, serial: str = None):
            verify = verify_player_info(address, password, serial)
            player = verify.player
            if verify.ping and verify.dws and verify.login:
                with lock:
                    df.at[index, 'password'] = player.password
                return True
            return False

        validation = validate_csv(df)
        if not validation[0]:
            self.output_df = None
            self.dropped_rows = None
            self.contains_valid_records = False
            self.error_message = validation[1]
            return
        else:
            with ThreadPoolExecutor(max_workers=50) as executor:
                futures = [
                    executor.submit(
                        verify_player, idx, row['address'], row['password'], row['serial']
                    )
                    for idx, row in df.iterrows()
                ]

                results = [f.result() for f in futures]

                    
            df['login'] = results
            self.reject_df = df[df['login'] == False].copy()
            data_before_strip = df.shape[0]
            df = df[df['login'] == True].copy()
            data_after_strip = df.shape[0]
            self.dropped_rows = data_before_strip - data_after_strip
            if data_after_strip == 0:
                self.contains_valid_records = False
                self.error_message = 'Could not connect to any of the provided players.'
                self.output_df = df
                return
            else:
                self.contains_valid_records = True
                self.output_df = df
                self.error_message = None