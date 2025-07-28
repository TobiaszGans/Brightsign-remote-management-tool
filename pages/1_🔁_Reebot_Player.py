import streamlit as st
from modules import utils as u, brightsign_API as bsp
from modules.utils import go_to
import time

st.set_page_config(
    page_title="Reboot Player",
    page_icon="🔁",
    layout="wide"
    )

st.title('Reboot Player')

key = 'reboot'
u.st_init(key, 'menu')

if st.session_state[key] == 'menu':
    u.menu(key)

elif st.session_state[key] == 'single_player':
    u.st_init('fail', False)
    if st.session_state.fail:
        st.error(st.session_state.error_message)
    u.single_player_input(key)

elif st.session_state[key] == 'single_verify':
    with st.spinner('Veryfying connection'):
        address = st.session_state.url
        password = st.session_state.password
        serial = st.session_state.serial
        connection_valid = u.verify_player_info(address=address,password=password,serial=serial)
        if connection_valid.ping and connection_valid.dws and connection_valid.login:
            player = connection_valid.player
            st.session_state.player = player
            for i in range (0,20):
                st.write('')
            go_to(key, 'reboot')
            st.rerun()
        else:
            st.session_state.fail = True
            if not connection_valid.ping:
                error_message = 'Could not reach the player.'
            elif connection_valid.ping and not connection_valid.dws:
                error_message = 'Could not reach the player on port 8080 or port 80.'
            elif connection_valid.ping and connection_valid.dws and not connection_valid.login:
                error_message = 'Could not connect with provided password or serial number.'

            st.session_state.error_message = error_message
            go_to(key, 'single_player')
            st.rerun()
        
elif st.session_state[key] == 'reboot':
    with st.spinner('Rebooting the player'):
        player = st.session_state.player
        with st.empty():
            st.write('Sending command')
            reboot_command = bsp.reboot(url=player.url, password=player.password, port=player.primary_port)
            if reboot_command.status_code != 200:
                st.write('Failed to send command. Trying again in 3s.')
                time.sleep(1)
                st.write('Failed to send command. Trying again in 2s.')
                time.sleep(1)
                st.write('Failed to send command. Trying again in 1s.')
                time.sleep(1)
                reboot_command = bsp.reboot(url=player.url, password=player.password, port=player.primary_port)
                if reboot_command.status_code != 200:
                    st.session_state.fail = True
                    st.session_state.error_message = 'Failed to send the reboot command to the player'
                    go_to(key, 'single_player')
                    st.rerun
            else:
                st.write('Reboot command sent.')
                time.sleep(4)
            
            player_available = False
            player_ping = False
            st.write('Player rebooting. Awaiting player response.')
            time.sleep(2)
            while not player_available:
                if not player_ping:
                    while not player_ping:
                        player_ping = bsp.ping(player.url)
                        time.sleep(2)
                player_available = bsp.reachUrl(player.url, player.primary_port)
                
            go_to(key, 'reboot_complete')
            st.rerun()

elif st.session_state[key] == 'reboot_complete':
    st.success('Player was rebooted successfully.')

    if st.button('Go back'):
        for k in list(st.session_state.keys()):
            if k != key:
                del st.session_state[k]
        st.session_state[key] = 'menu'
        st.rerun()