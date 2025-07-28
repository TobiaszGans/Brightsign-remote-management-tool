import streamlit as st
from modules import brightsign_API as bsp, utils as u
from modules.utils import go_to
import time, threading, io, zipfile
import pandas as pd
from concurrent.futures import ThreadPoolExecutor

def display_logs(logs, height=500):
    container = st.container(height=height, border=True)
    with container:
        st.code(logs, language="text")


st.set_page_config(
    page_title="Pull device logs",
    page_icon="🖹",
    layout="wide"
    )

key = 'logs'
u.st_init(key, 'menu')

st.title('Get logs from the player')

if st.session_state[key] == 'menu':
    u.menu(key)

elif st.session_state[key] == 'single_player':
    u.st_init('fail', False)
    if st.session_state.fail:
        st.error(st.session_state.error_message)
    u.single_player_input(key)

elif st.session_state[key] == 'single_verify':
    url = st.session_state.url
    password = st.session_state.password
    serial = st.session_state.serial
    primary_port = 8080
    secondary_port = 80
    login = 'admin'
    with st.spinner('Connecting to the player...'):
        with st.empty():
            st.write('Pinging the player')
            ping = bsp.ping(url)
            st.write(f'Ping result: {ping}')
            time.sleep(1)
            st.write(f'Checking DWS port and availability on port {primary_port}')
            dws_status = bsp.reachUrl(url, primary_port)
            if dws_status != True:
                st.write(f'Failed to connect on port {primary_port}. Retrying on port {secondary_port}')
                dws_status2 = bsp.reachUrl(url, secondary_port)
                if dws_status2 == True:
                    st.write(f'Succesfully connected on port {secondary_port}')
                    time.sleep(1)
                    port = secondary_port
                else:
                    st.write(f'Failed to connect on ports {primary_port} and {secondary_port}')
                    st.session_state.fail = True
                    st.session_state.error_message = 'Failed to connect to the player. Maybe the player is offline?'
                    go_to(key, 'single_player')
                    st.rerun()
            else:
                port = primary_port
                st.write(f'Succesfully connected on port {primary_port}')
                time.sleep(1)
            


            st.write('Checking API access with provided password')
            response = bsp.init_login(url=url, port=port, login=login, password=password)
            if response.status_code >= 400 and serial is not None:
                st.write('Could not connect with provided Password. Attempting to log in using device serial number.')
                response = bsp.init_login(url=url, port=port, login=login, password=serial)
                password = serial
                if response.status_code >= 400:
                    st.session_state.error_message = 'Could not connect with provided password or serial number.'
                    st.session_state.fail = True
                    go_to(key, 'single_player')
                    st.rerun()
                else:
                    response = response
                    st.write('Success')
            elif response.status_code >= 400 and serial is None:
                st.session_state.error_message = 'Could not connect with provided password.'
                st.session_state.fail = True
                go_to(key, 'single_player')
                st.rerun()
            else:
                response = response
                device_name = bsp.get_device_name(url=url, port=port, password=password)
                st.write('Success')
            st.session_state.device_name = device_name
            st.session_state.port = port
            st.session_state.url = url
            st.session_state.password = password
            st.session_state.init_response = response
            st.session_state.serial = serial
            time.sleep(1)
            go_to(key, 'single_get_logs')
            st.rerun()

elif st.session_state[key] == 'single_get_logs':
    device_name = st.session_state.device_name
    st.markdown(f'#### {device_name}')
    url = st.session_state.url
    password = st.session_state.password
    port = st.session_state.port
    serial = st.session_state.serial
    login = 'admin'

    with st.spinner('Downloading the log'):
        try:
            logs = bsp.get_logs(url=url,port=port,password=password,login=login)
        except:
            st.warning("Failed to download logs, retrying again in 10 seconds")
            time.sleep(10)
            try:
                logs = bsp.get_logs(url=url,port=port,password=password,login=login)
            except:
                st.error('Failed to download logs for the device.')
                st.stop()
        if serial is None or serial.strip() == '': 
            file_name = f'{device_name} device log.txt'
        else:
            file_name = f'{device_name} - {serial}: device log.txt'

        display_logs(logs)

        c1,c2,c3 = st.columns([1,1,3])
        with c1:
            if st.button('Refresh', use_container_width=True):
                st.rerun()
        with c2:
            st.download_button('Download the log file', data=logs, file_name=file_name, use_container_width=True)



elif st.session_state[key] == 'multi_player':
    u.st_init('error', False)
    if st.session_state.error:
        st.error(st.session_state.error_message)
    playerfile = st.file_uploader('Please upload a csv file containing device addresses, device passwords, and device serial numbers (optional).', type='csv')
    template = u.upload_template()

    st.download_button('Download csv file template', data=template, file_name='Player upload template.csv')

    if playerfile == None:
        disable_continue = True
    else:
        st.session_state.players = pd.read_csv(playerfile)
        disable_continue = False
    
    st.button('Continue', on_click=lambda:go_to(key, 'multi_verify'), disabled=disable_continue)

elif st.session_state[key] == 'multi_verify':
    def try_login(address, password):
        try:
            response = bsp.init_login(url=address, port=8080, login='admin', password=password)
            return response.status_code == 200
        except Exception:
            return False
    def threaded_try_login(row):
        return try_login(row['address'], row['password'])

    with st.spinner('Validating uploaded list'):
        players = st.session_state.players
        st.session_state.error = False
        validation = u.validate_csv(players)
        if not validation[0]:
            st.session_state['error'] = True
            st.session_state.error_message = validation[1]
            go_to(key, 'multi_player')
            st.rerun()
        else:
            with ThreadPoolExecutor(max_workers=20) as executor:
                login_results = list(executor.map(threaded_try_login, [row for _, row in players.iterrows()]))

            players['login'] = login_results
            data_before_strip = players.shape[0]
            players = players[players['login'] == True].copy()
            data_after_strip = players.shape[0]

            if data_after_strip == 0:
                st.session_state['error'] = True
                st.session_state.error_message = 'Could not connect to any of the provided players'
                go_to(key, 'multi_player')
                st.rerun()
            elif data_before_strip == data_after_strip:
                st.session_state.strip = 0
            else:
                st.session_state.strip = data_before_strip - data_after_strip
            st.session_state.players = players
            go_to(key, 'convert_multi')
            u.clear_screen()
            time.sleep(1)
            st.rerun()

elif st.session_state[key] == 'convert_multi':
    def get_name_threaded(row):
        return bsp.get_device_name(url=row['address'], port=8080, password=row['password'])
    
    players = st.session_state.players
    with st.spinner('Requesting device names'):
        with ThreadPoolExecutor(max_workers=10) as executor:
            names = list(executor.map(get_name_threaded, [row for _, row in players.iterrows()]))

        players['Name'] = names

        go_to(key, 'multi_logs')
        u.clear_screen()
        time.sleep(1)
        st.rerun()

elif st.session_state[key] == 'multi_logs':
    players = st.session_state.players
    lock = threading.Lock()
    u.st_init('toasted', False)

    def process_player(index, address, password):
        """Threaded function to get a log from a player."""
        try:
            with lock:
                players.at[index, 'log'] = 'Generating...'

            log = bsp.get_logs(
                url=address, login='admin', password=password, port=8080
            )

            with lock:
                players.at[index, 'log'] = log
        except Exception as e:
            with lock:
                players.at[index, 'log'] = f'Error: {e}'

    players['log'] = ''''''

    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = [
            executor.submit(
                process_player, idx, row['address'], row['password']
            )
            for idx, row in players.iterrows()
        ]

        with st.spinner('Download Logs'):
            while any(not f.done() for f in futures):
                time.sleep(1)  # Just wait; updates aren't needed live here
    # Create a BytesIO object to store the ZIP in memory
    zip_buffer = io.BytesIO()

    # Write text files into the ZIP archive
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED) as zip_file:
        for idx, row in players.iterrows():
            file_name = f"{row['Name']} - log.txt"
            content = row['log']
            zip_file.writestr(file_name, content)

    # Move buffer to the beginning
    zip_buffer.seek(0)

    # Store updated player data and change view state
    st.session_state.zip_buffer = zip_buffer
    st.session_state.players = players
    st.session_state.has_processed = True
    go_to(key, 'display_Logs')
    st.rerun()

elif st.session_state[key]  == 'display_Logs':
    st.markdown("### Logs")
    players = st.session_state.players
    
    
    zip_buffer = st.session_state.zip_buffer
    
    col1,col2,col3 = st.columns([1,1,1])
    with col1:
        st.download_button('Download all logs', data=zip_buffer, file_name="logs.zip", mime="application/zip", use_container_width=True)
    with col3:
        st.button('Refresh', on_click=lambda: go_to(key, 'multi_logs'), use_container_width=True)
    
    if not st.session_state.toasted:
        if st.session_state.strip == 1:
            st.toast(f'One player was removed from the list, because it was not reachable.')
            st.session_state.toasted = True
        elif st.session_state.strip > 1:
            st.toast(f'{st.session_state.strip} players were removed from the list, because they were not reachable.')
            st.session_state.toasted = True
        else:
            st.session_state.toasted = True    

    col1, col2 = st.columns(2)

    for i, (_, row) in enumerate(players.iterrows()):
        name = row.get('Name', f"Player {i}")
        serial = row.get('serial', f"Player {i}")
        log = row['log']
        col = col1 if i % 2 == 0 else col2

        with col:
            with st.container(border=True):
                if pd.isna(serial) or serial == '':
                    st.write(f"**{name}**")
                else:
                    st.write(f"**{name}** - {serial}")

                b1,b2 = st.columns([1,1])
                with b1:
                    if st.button('View Log', use_container_width=True, key=f'view_log-{name}'):
                        st.session_state.current_log = log
                        st.session_state.current_name = name
                        go_to(key, 'view_log_from_list')
                        st.rerun()
                with b2:
                    file_name = name + ' - log.txt'
                    st.download_button('Download this log', data=log, file_name=file_name, use_container_width=True, key=f'download_log-{name}')
    col12,col22,col32 = st.columns([1,1,1])
    with col12:
        st.download_button('Download all logs', data=zip_buffer, file_name="logs.zip", mime="application/zip", use_container_width=True, key='dwonloadall2')
    with col22:
        st.button('Refresh', on_click=lambda: go_to(key, 'multi_logs'), use_container_width=True, key='refresh2')
    with col32:
        if st.button('Go back to menu', use_container_width=True):
            # Preserve the main state key only
            for k in list(st.session_state.keys()):
                if k != key:
                    del st.session_state[k]
            st.session_state[key] = 'menu'
            st.rerun()

elif st.session_state[key] == 'view_log_from_list':
    log = st.session_state.current_log
    name = st.session_state.current_name
    st.markdown(f'### {name}')
    display_logs(log)

    if st.button('Go back to list'):
        del st.session_state['current_log']
        del st.session_state['current_name']
        go_to(key, 'display_Logs')
        st.rerun()








# Menu Button
if st.session_state[key] != 'menu' and st.session_state[key] != 'display_Logs':
    c1, c2, c3 = st.columns([1, 1, 1])
    with c3:
        if st.button('Go back to menu', use_container_width=True):
            # Preserve the main state key only
            for k in list(st.session_state.keys()):
                if k != key:
                    del st.session_state[k]
            st.session_state[key] = 'menu'
            st.rerun()