import streamlit as st
from modules import utils as u, brightsign_API as bsp
from modules.utils import go_to
import time, threading
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
import base64
from io import BytesIO

st.set_page_config(
    page_title="Take Screenshots",
    page_icon="🖼️",
    layout="wide"
    )

key = 'screenshot'
u.st_init(key, 'menu')

st.title('Take screenshot from the player')

if st.session_state[key] == 'menu':
    c1,c2 = st.columns([1,1])
    with c1:
        if st.button('Single Player', use_container_width=True, disabled=False):
            go_to(key, 'single_player')
            st.rerun()
    with c2:
        if st.button('Multiple Players', use_container_width=True, disabled=False):
            go_to(key, 'multi_player')
            st.rerun()


elif st.session_state[key] == 'single_player':
    u.st_init('fail', False)
    if st.session_state.fail:
        st.error(st.session_state.error_message)
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
    st.button('Continue', on_click=lambda: go_to(key, 'single_verify'), disabled=disable_continue)

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
                device_name = bsp.get_device_name(url=url, port=port, login=login, password=password)
                st.write('Success')
            st.session_state.device_name = device_name
            st.session_state.port = port
            st.session_state.url = url
            st.session_state.password = password
            st.session_state.init_response = response
            time.sleep(1)
            go_to(key, 'single_screenshot')
            st.rerun()

elif st.session_state[key] == 'single_screenshot':
    st.session_state.continuous = False
    device_name = st.session_state.device_name
    st.session_state.device_name = device_name
    st.markdown(f'#### {device_name}')
    url = st.session_state.url
    password = st.session_state.password
    port = st.session_state.port
    login = 'admin'
    if st.button('Take a screenshot'):
        with st.spinner('loading screenshot'):
            image = bsp.capture_snapshot_thumbnail(url=url,port=port,password=password,login=login)
            st.image(image, caption="Remote Snapshot")

    st.button('Continuous snapshot', on_click=lambda: go_to(key, 'single_continuous'))

elif st.session_state[key] == 'single_continuous':
    device_name = st.session_state.device_name
    url = st.session_state.url
    password = st.session_state.password
    port = st.session_state.port
    login = 'admin'
    st.markdown(f'#### {device_name}')
    u.st_init('continuous', False)
    delay = st.slider('Refresh period (seconds)', min_value=5, max_value=60, step=1)

    c1,c2,c3 = st.columns([2,3,2])
    with c1:
        if not st.session_state.continuous:
            if st.button('Start Snapshots', use_container_width=True):
                st.session_state.continuous = True
                st.rerun()
        else:
            if st.button('Stop Snapshots', use_container_width=True):
                st.session_state.continuous = False
                st.rerun()
    with c3:
        st.button('Return to single snapshot', use_container_width=True, on_click=lambda: go_to(key, 'single_screenshot'))
    
    with st.empty():
        while st.session_state.continuous:
            image = bsp.capture_snapshot_thumbnail(url=url,port=port,password=password,login=login)
            st.image(image, caption="Remote Snapshot")
            time.sleep(delay)

elif st.session_state[key] == 'multi_player':
    u.st_init('error', False)
    if st.session_state.error:
        st.error(st.session_state.error_message)
    playerfile = st.file_uploader('Please upload a csv file containing device addresses, device passwords, and device serial numbers (optional).', type='csv')
    template = u.upload_template()
    st.info('Please keep in mind that going over 20 devices may result in performance issues.')

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
            players['login'] = players.apply(
                lambda row: try_login(row['address'], row['password']),
                axis=1
            )
            data_before_strip = players.shape[0]
            players = players[players['login'] == True]
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
    players = st.session_state.players
    with st.spinner('Requesting device names'):
        players['Name'] = players.apply(
            lambda row: bsp.get_device_name(url=row['address'], port=8080, login='admin', password=row['password']),
            axis=1
        )

        go_to(key, 'multi_generate')
        u.clear_screen()
        time.sleep(1)
        st.rerun()


elif st.session_state[key] == 'multi_generate':
    u.st_init('has_processed', False)
    players = st.session_state.players.copy()
    lock = threading.Lock()
    if st.session_state.strip == 1:
        st.toast(f'One player was removed from the list, because it was not reachable.')
    elif st.session_state.strip > 1:
        st.toast(f'{st.session_state.strip} players were removed from the list, because they were not reachable.')

    def process_player(index, address, password, serial):
        """Threaded function to get a screenshot from a player."""
        try:
            with lock:
                players.at[index, 'Screenshot'] = 'Generating...'

            picture = bsp.capture_snapshot_thumbnail(
                url=address, login='admin', password=password, port=8080
            )

            with lock:
                players.at[index, 'Screenshot'] = picture
        except Exception as e:
            with lock:
                players.at[index, 'Screenshot'] = f'Error: {e}'

    if not st.session_state.has_processed:
        players['Screenshot'] = 'Initializing'

        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [
                executor.submit(
                    process_player, idx, row['address'], row['password'], row['serial']
                )
                for idx, row in players.iterrows()
            ]

            with st.spinner('Generating snapshots...'):
                while any(not f.done() for f in futures):
                    time.sleep(1)  # Just wait; updates aren't needed live here

        # Store updated player data and change view state
        st.session_state.players = players
        st.session_state.has_processed = True
        go_to(key, 'display_screenshots')
        st.rerun()


elif st.session_state[key] == 'display_screenshots':
    st.markdown("### Screenshots")
    st.button('Refresh', on_click=lambda: go_to(key, 'multi_generate'))

    players = st.session_state.players
    col1, col2 = st.columns(2)

    for i, (_, row) in enumerate(players.iterrows()):
        name = row.get('Name', f"Player {i}")
        screenshot = row['Screenshot']
        col = col1 if i % 2 == 0 else col2

        with col:
            st.write(f"**{name}**")
            if isinstance(screenshot, str):
                if screenshot.startswith("Error"):
                    st.error(screenshot)
                else:
                    st.warning("Still waiting...")
            else:
                st.image(screenshot)

# Menu Button
if st.session_state[key] != 'menu':
    c1, c2, c3 = st.columns([1, 1, 1])
    with c3:
        if st.button('Go back to menu', use_container_width=True):
            # Preserve the main state key only
            for k in list(st.session_state.keys()):
                if k != key:
                    del st.session_state[k]
            st.session_state[key] = 'menu'
            st.rerun()