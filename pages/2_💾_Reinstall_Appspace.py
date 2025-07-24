import streamlit as st
from modules import utils as u, brightsign_API as bsp
from modules.utils import go_to
import time, json, threading
import pandas as pd
from concurrent.futures import ThreadPoolExecutor

st.set_page_config(
    page_title="Reinstall Appspace",
    page_icon="💾",
    layout="wide"
    )

key = 'reinstall'
u.st_init(key, 'menu')

st.title('Reinstall Appspace on the player')

if st.session_state[key] == 'menu':
    st.write('Select the mode.')
    col1,col2 = st.columns([1,1])
    with col1:
        st.button('Single Player Mode', use_container_width=True, on_click=lambda: go_to(key, 'singleplayer'))
    with col2:
        st.button('Multi Player Mode', use_container_width=True, on_click=lambda: go_to(key, 'multiplayer'))

elif st.session_state[key] == 'singleplayer':
    u.st_init('fail', False)
    if st.session_state.fail:
        st.error(st.session_state.error_message)
    st.markdown('Please fill out the following inputs:')
    url = st.text_input('Player URL or IP address. Please do not include the 8080 port number.')
    password = st.text_input('The player password',type='password')
    serial = st.text_input('Player serial number (optional)')
    if serial.strip() != '':
        login_info = bsp.credentials(url=url, password=password, serial=serial)
    else:
        login_info = bsp.credentials(url=url, password=password)
    
    if url.strip() == '' or password.strip() == '':
        disable_button = True
    else:
        disable_button = False

    col1,col2 = st.columns([8,1])
    with col1:
        if st.button('Continue', disabled=disable_button):
            st.session_state.login_info = login_info
            go_to(key, 'uploadAutorun')
            st.rerun()
    with col2:
        st.button('Back to menu', use_container_width=True, on_click=lambda: go_to(key, 'menu'))
    

elif st.session_state[key] == 'uploadAutorun':
    st.write('Please upload a current autorun file.')
    file = u.select_autourn()
    if file is not None:
        disable_button2 = False
    else:
        disable_button2 = True
    
    if st.button('continue',disabled=disable_button2):
        st.session_state.autorun = file
        go_to(key, 'connect_to_player')
        st.rerun()
        
elif st.session_state[key] == 'connect_to_player':
    login_info = st.session_state.login_info
    with st.spinner('Connecting to the player...'):
        with st.empty():
            st.write('Pinging the player')
            ping = bsp.ping(login_info.url)
            st.write(f'Ping result: {ping}')
            time.sleep(1)
            st.write(f'Checking DWS port and availability on port {login_info.primary_port}')
            dws_status = bsp.reachUrl(login_info.url, login_info.primary_port)
            if dws_status != True:
                st.write(f'Failed to connect on port {login_info.primary_port}. Retrying on port {login_info.secondary_port}')
                dws_status2 = bsp.reachUrl(login_info.url, login_info.secondary_port)
                if dws_status2 == True:
                    st.write(f'Succesfully connected on port {login_info.secondary_port}')
                    time.sleep(1)
                    port = login_info.secondary_port
                else:
                    st.write(f'Failed to connect on ports {login_info.primary_port} and {login_info.secondary_port}')
                    st.session_state.fail = True
                    st.session_state.error_message = 'Failed to connect to the player. Maybe the player is offline?'
                    go_to(key, 'singleplayer')
                    st.rerun()
            else:
                port = login_info.primary_port
                st.write(f'Succesfully connected on port {login_info.primary_port}')
                time.sleep(1)
            


            st.write('Checking API access with provided password')
            response = bsp.init_login(url=login_info.url, port=port, login=login_info.login, password=login_info.password)
            if response.status_code >= 400 and login_info.serial is not None:
                st.write('Could not connect with provided Password. Attempting to log in using device serial number.')
                response = bsp.init_login(url=login_info.url, port=port, login=login_info.login, password=login_info.serial)
                login_info.password = login_info.serial
                if response.status_code >= 400:
                    st.session_state.error_message = 'Could not connect with provided password or serial number.'
                    st.session_state.fail = True
                    go_to(key, 'singleplayer')
                    st.rerun()
                else:
                    response = response
                    st.write('Success')
            elif response.status_code >= 400 and login_info.serial is None:
                st.session_state.error_message = 'Could not connect with provided password.'
                st.session_state.fail = True
                go_to(key, 'singleplayer')
                st.rerun()
            else:
                response = response
                st.write('Success')
            st.session_state.response = response
            st.session_state.port = port
            st.session_state.login_info = login_info
            time.sleep(1)
            go_to(key, 'disable_autorun')
            st.rerun()

elif st.session_state[key] == 'disable_autorun':
    login_info = st.session_state.login_info
    port = st.session_state.port
    with st.spinner('Disabling autorun...'):
        with st.empty():
            st.write('Sending command')
            response = bsp.disable_autorun(url=login_info.url, port=port, login=login_info.login, password=login_info.password)
            if response.status_code == 200:
                st.write('Command sent successfully.')
            else:
                st.write('Command failed, trying again in 10 seconds')
                time.sleep(12)
                response = bsp.disable_autorun(url=login_info.url, port=port, login=login_info.login, password=login_info.password)
                if response.status_code != 200:
                    st.session_state.error_message = 'Failed to disable autorun'
                    st.session_state.fail = True
                    st.error(st.session_state.error_message)
                    quit()
                else:
                    st.write('Command sent successfully.')
            
            ping_response = False
            time.sleep(2)
            st.write('Waiting for player to respond')
            while not ping_response:
                ping_response = bsp.ping(login_info.url)
                time.sleep(2)
            time.sleep(10)
            if ping_response:
                t=15
                st.write('Attempting to connect to the player')
                dws = False
                attempt = 1
                while not dws:
                    with st.empty():
                        st.write(f'''Attempting to connect to the player\nAttempt {attempt}''')
                        dws = bsp.reachUrl(login_info.url, port)
                        attempt = attempt + 1
                        time.sleep(2)

                st.write('Continuing')    
                go_to(key, 'format_storage')
                st.rerun()

elif st.session_state[key] == 'format_storage':
    with st.spinner('Formating SD card'):
        login_info = st.session_state.login_info
        port = st.session_state.port
        response = bsp.format_storage(url=login_info.url, port=port, login=login_info.login, password=login_info.password)
        if response.status_code == 200:
            st.write('SD Card formatted')
        else:
            st.write('Failed, trying again')
            st.write(response)
            time.sleep(5)
            response = bsp.format_storage(url=login_info.url, port=port, login=login_info.login, password=login_info.password)
            if response.status_code == 200:
                st.write('SD Card formatted')
            else:
                st.session_state.error_message = 'Failed to format SD card'
                st.session_state.fail = True
                st.error(st.session_state.error_message)
                quit()
        
        go_to(key, 'upload')
        st.rerun()

elif st.session_state[key] == 'upload':
    with st.spinner('Uploading autorun'):
        login_info = st.session_state.login_info
        port = st.session_state.port
        bytes_data = st.session_state.autorun
        files = files = {
                'file[0]': ('autorun.zip', bytes_data, 'application/zip')
            }
        response = bsp.upload_file(url=login_info.url, port=port, login=login_info.login, password=login_info.password, file=files)
        if response.status_code == 200:
            st.write('Success')
            time.sleep(1)
            go_to(key, 'reboot')
            st.rerun()
        else:
            st.error(f'Something went wrong. Status code: {response.status_code}')

elif st.session_state[key] == 'reboot':
    st.write('Rebooting the player')
    login_info = st.session_state.login_info
    port = st.session_state.port
    reboot = bsp.reboot(url=login_info.url, port=port, login=login_info.login, password=login_info.password)
    if reboot.status_code == 200:
        st.write('Command sent successfully.')
    else:
        st.write('Command failed, trying again in 10 seconds')
        time.sleep(10)
        reboot = bsp.reboot(url=login_info.url, port=port, login=login_info.login, password=login_info.password)
        if reboot.status_code != 200:
            st.session_state.error_message = 'Failed to reboot the player'
            st.session_state.fail = True
            st.error(st.session_state.error_message)
            quit()
        else:
            st.write('Command sent successfully.')
    
    ping_response = False
    st.write('Waiting for player to respond')
    while not ping_response:
        ping_response = bsp.ping(login_info.url)
        time.sleep(2)
    time.sleep(10)
    if ping_response:
        st.write('Attempting to connect to the player')
        dws = False
        attempt = 1
        with st.empty():
            while not dws:
                st.write(f'Attempt {attempt}')
                dws = bsp.reachUrl(login_info.url, port)
                attempt = attempt + 1
                time.sleep(2)

        st.write('Complete. Please verify')
    
    c1, c2, c3 = st.columns([1,1,1])
    with c3:    
        if st.button('Go back to menu', use_container_width=True):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
                key = 'reinstall'
                u.st_init(key, 'menu')
            st.rerun()
    


elif st.session_state[key] == 'multiplayer':
    u.st_init('error', False)
    if st.session_state.error:
        st.error(st.session_state.error_message)
    playerfile = st.file_uploader('Please upload a csv file containing device addresses, device passwords, and device serial numbers (optional).', type='csv')
    template = u.upload_template()

    st.download_button('Download csv file template', data=template, file_name='Player upload template.csv')

    autorun = u.select_autourn()

    if not playerfile or autorun is None:
        disable_button = True
    else:
        players = pd.read_csv(playerfile)
        st.session_state.players = players
        st.session_state.autorun = autorun
        disable_button=False

    
    col1,col2 = st.columns([8,1])
    with col1:
        st.button('Continue', disabled=disable_button, on_click=lambda: go_to(key, 'validate_csv'))
    with col2:
        st.button('Back to menu', use_container_width=True, on_click=lambda: go_to(key, 'menu'))

elif st.session_state[key] == 'validate_csv':
    with st.spinner('Validating uploaded list'):
        players = st.session_state.players
        st.session_state.error = False
        validation = u.validate_csv(players)
        if not validation[0]:
            st.session_state['error'] = True
            st.session_state.error_message = validation[1]
            go_to(key, 'multiplayer')
            st.rerun()
        else:
            go_to(key, 'process_players')
            u.clear_screen()
            time.sleep(1)
            st.rerun()
        

elif st.session_state[key] == 'process_players':
    players = st.session_state.players
    table_placeholder = st.empty()

    # Lock for thread-safe updates
    lock = threading.Lock()

    # Shared flag to track completion
    processing_done = False



    # Threaded function (logic only)
    def process_player(index, address, password, serial, file):
        try:
            with lock:
                players.at[index, 'status'] = 'Connecting to player'

            # Ping
            ping = bsp.ping(address)
            if not ping:
                with lock:
                    players.at[index, 'status'] = 'No ping, attempting to connect anyway'

            # Try reaching DWS
            port = None
            for p in (8080, 80):
                if bsp.reachUrl(address, p):
                    port = p
                    break

            if port is None and ping:
                with lock:
                    players.at[index, 'status'] = 'Could not connect to player on ports 80 or 8080'
                    players.at[index, 'name'] = 'Could not reach the player'
                return
            elif port is None and not ping:
                with lock:
                    players.at[index, 'status'] = 'Could not reach the player'
                    players.at[index, 'name'] = 'Could not reach the player'
                return
            
            
            with lock:
                players.at[index, 'status'] = f'Connected on port {port}, checking API access'

            # Attempt login with password
            login = bsp.init_login(url=address, port=port, login='admin', password=password)

            if login.status_code >= 400:
                if serial:
                    with lock:
                        players.at[index, 'status'] = 'Password failed, trying serial number'
                    login = bsp.init_login(url=address, port=port, login='admin', password=serial)
                    password = serial

                    if login.status_code >= 400:
                        with lock:
                            players.at[index, 'status'] = 'Login failed with both password and serial'
                            players.at[index, 'name'] = 'Could not reach the player'
                        return
                else:
                    with lock:
                        players.at[index, 'status'] = 'Login failed with provided password'
                        players.at[index, 'name'] = 'Could not reach the player'
                    return
            
            # Set device name
            device_info = json.loads(login.text)
            name = device_info['data']['result']['networking']['result']['name']
            players.at[index, 'name'] = name
            
            # Disable Autorun
            with lock:
                players.at[index, 'status'] = 'Successfully connected, disabling Autorun'
            disable_autorun = bsp.disable_autorun(url=address, port=port, login='admin', password=password)
            if disable_autorun.status_code == 200:
                with lock:
                    players.at[index, 'status'] = 'Disabling Autorun'
            else:
                time.sleep(10)
                disable_autorun = bsp.disable_autorun(url=address, port=port, login='admin', password=password)
                if disable_autorun.status_code != 200:
                    with lock:
                        players.at[index, 'status'] =  'Failed to disable autorun'
                    return

            # Wait for player to be back online
            time.sleep(5)
            with lock:
                players.at[index, 'status'] = 'Disabled Autorun, Awaiting player response'
            ping_response = False
            max_wait = 60
            elapsed = 0
            while not ping_response and elapsed < max_wait:
                ping_response = bsp.ping(address)
                time.sleep(2)
                elapsed += 2
            if not ping_response:
                with lock:
                    players.at[index, 'status'] = 'Player did not respond to ping in time'
                return
            dws = False
            elapsed = 0
            while not dws and elapsed < max_wait:
                dws = bsp.reachUrl(address, port)
                time.sleep(2)
                elapsed += 2
            if not dws:
                with lock:
                    players.at[index, 'status'] = 'Failed to connect to player after rebooting the player post upload'
                    return

            # Format SD Card
            with lock:
                players.at[index, 'status'] = 'Formating SD card'
            format_sd = bsp.format_storage(url=address, port=port, login='admin', password=password)
            
            if format_sd.status_code != 200:
                # Failed, trying again
                time.sleep(10)
                format_sd = bsp.format_storage(url=address, port=port, login='admin', password=password)
                if format_sd.status_code != 200:
                    with lock:
                        players.at[index, 'status'] = 'Failed to format SD card'
                    return
            
            # Upload Autorun
            with lock:
                players.at[index, 'status'] ='SD Card formatted, uploading Autorun'

            bytes_data = file
            files = {
                    'file[0]': ('autorun.zip', bytes_data, 'application/zip')
                }
            upload = bsp.upload_file(url=address, port=port, login='admin', password=password, file=files)
            if upload.status_code != 200:
                with lock:
                    players.at[index, 'status'] = 'Failed to upload autorun'
                return

            # Last Reboot
            with lock:
                players.at[index, 'status'] = 'Uploaded Autorun. Rebooting...'
            reboot = bsp.reboot(url=address, port=port, login='admin', password=password)
            if reboot.status_code != 200:
                time.sleep(10)
                reboot = bsp.reboot(url=address, port=port, login='admin', password=password)
                if reboot.status_code != 200:
                    with lock:
                        players.at[index, 'status'] = 'Failed to reboot the player trying again in 30 seconds'
                    time.sleep(30)
                    reboot = bsp.reboot(url=address, port=port, login='admin', password=password)
                    if reboot.status_code != 200:
                        with lock:
                            players.at[index, 'status'] = 'Failed to reboot the player after uploading the autorun'
                        return
            
            # Wait for player to be back online again 
            time.sleep(5)
            with lock:
                players.at[index, 'status'] = 'Rebooting, awaiting player response'
            ping_response = False
            max_wait = 60
            elapsed = 0
            while not ping_response and elapsed < max_wait:
                ping_response = bsp.ping(address)
                time.sleep(2)
                elapsed += 2
            if not ping_response:
                with lock:
                    players.at[index, 'status'] = 'Player did not respond to ping in time'
                return
            dws = False
            elapsed = 0
            while not dws and elapsed < max_wait:
                dws = bsp.reachUrl(address, port)
                time.sleep(2)
                elapsed += 2
            if not dws:
                with lock:
                    players.at[index, 'status'] = 'Failed to connect to player after rebooting retrying in 30 seconds'
                    time.sleep(30)
                    elapsed = 0
                    while not dws and elapsed < max_wait:
                        dws = bsp.reachUrl(address, port)
                        time.sleep(2)
                        elapsed += 2
                    if not dws:
                        with lock:
                            players.at[index, 'status'] = 'Failed to connect to player after rebooting the player'
                        return
            
            
            # Process Complete
            with lock:
                players.at[index, 'status'] = 'Reinstall Complete'
        except Exception as e:
            with lock:
                players.at[index, 'status'] = f'Unexpected error: {str(e)}'

        
    # UI
    u.st_init("already_processed", False)
    if not st.session_state["already_processed"]:
        players['status'] = 'Initializing'
        players['name'] = 'Initializing'
        threads = []
        table_placeholder = st.empty()

        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = []
            for idx, row in players.iterrows():
                future = executor.submit(process_player, idx, row['address'], row['password'], row['serial'], st.session_state.autorun)
                futures.append(future)

            # While threads are running, keep refreshing the table
            while any(not f.done() for f in futures):
                with lock:
                    table_placeholder.dataframe(players, hide_index=True, column_order=['address', 'serial', 'name', 'status'])
                time.sleep(1)

        # Final update
        with lock:
            table_placeholder.dataframe(players, hide_index=True, column_order=['address', 'serial', 'name', 'status'])
        
        st.session_state.players = players
        st.session_state.already_processed = True
    players['is_error'] = players['status'] != 'Reinstall Complete'
        
    # Error Highlighting
    def highlight_errors(row):
        if row['is_error']:
            return ['background-color: rgba(255, 0, 0, 0.2)'] * len(row)
        return [''] * len(row)

    styled_df = players.style.apply(highlight_errors, axis=1)

    table_placeholder.dataframe(styled_df, hide_index=True, column_order=['address', 'serial', 'name', 'status'])
    
    st.success("All players processed.")

    fails_df = players.loc[(players['is_error'] == True)]
    fails_file = fails_df.drop(columns=['password', 'is_error']).to_csv(index=False)

    c1, c2, c3 = st.columns([1,1,1])
    with c1:
        st.download_button('Download error players', data=fails_file, file_name='Reinstal Error Players.csv', use_container_width=True)
    with c3:    
        if st.button('Process another batch', use_container_width=True):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
                key = 'reinstall'
                u.st_init(key, 'menu')
            st.rerun()