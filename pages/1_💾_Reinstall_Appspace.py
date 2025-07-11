import streamlit as st
from modules import utils as u, brightsign_API as bsp
from modules.utils import go_to
import time
import pandas as pd
import base64

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
        st.button('Multi Player Mode', use_container_width=True, on_click=lambda: go_to(key, 'multiplayer') ,disabled=True)

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

    if st.button('Continue', disabled=disable_button):
        st.session_state.login_info = login_info
        go_to(key, 'uploadAutorun')
        st.rerun()

elif st.session_state[key] == 'uploadAutorun':
    st.write('Please upload a current autorun file.')
    file = st.file_uploader('Upload autorun.zip', type='zip')

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
                        st.write(f'''Attempting to connect to the player\n
                                 Attempt {attempt}''')
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
        uploaded_file = st.session_state.autorun
        #st.write(uploaded_file)
        bytes_data = uploaded_file.getvalue()
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
        response = bsp.disable_autorun(url=login_info.url, port=port, login=login_info.login, password=login_info.password)
        if response.status_code != 200:
            st.session_state.error_message = 'Failed to disable autorun'
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
#st.write(st.session_state)