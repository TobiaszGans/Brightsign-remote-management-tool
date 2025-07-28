import streamlit as st
from modules import utils as u, brightsign_API as bsp
from modules.utils import go_to
import time, threading
from concurrent.futures import ThreadPoolExecutor

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


elif st.session_state[key] == 'multi_player':
    u.st_init('error', False)
    if st.session_state.error:
        st.error(st.session_state.error_message)
    u.multi_player_input(key)

elif st.session_state[key] == 'multi_verify':
    with st.spinner('Veryfying data'):
        verify = u.multi_verify(st.session_state.players)
        if verify.contains_valid_records:
            st.session_state.players = verify.output_df
            st.session_state.dropped_rows = verify.dropped_rows
            if verify.dropped_rows == 0:
                st.session_state.reject_df = None
            else:
                st.session_state.reject_df = verify.reject_df
            st.session_state.error = False
            go_to(key, 'multi_reboot')
            st.rerun()
        else:
            st.session_state.error = True
            st.session_state.error_message = verify.error_message
            go_to(key, 'multi_player')
            st.rerun()

elif st.session_state[key] == 'multi_reboot':
    dropped_rows = st.session_state.dropped_rows
    reject_df = st.session_state.reject_df
    players = st.session_state.players
    lock = threading.Lock()
    if dropped_rows != 1:
        st.toast(f'One player was removed from the data frame as it was not reachable.')
    elif dropped_rows > 1:
        st.toast(f'{dropped_rows} players were removed from the data frame as they were not reachable.')
    
    def process_player(index, address, password):
        try:
            with lock:
                players.at[index, 'reboot'] = 'Sending Command'

            reboot_command = bsp.reboot(
                url=address, login='admin', password=password, port=8080
            )

            if not reboot_command or reboot_command.status_code != 200:
                with lock:
                    players.at[index, 'reboot'] = 'Failed to send command. Trying again in 3s.'
                time.sleep(1)
                with lock:
                    players.at[index, 'reboot'] = 'Retrying...'
                time.sleep(2)

                reboot_command = bsp.reboot(url=address, login='admin', password=password, port=8080)

                if not reboot_command or reboot_command.status_code != 200:
                    with lock:
                        players.at[index, 'reboot'] = f'Final attempt failed. Status: {getattr(reboot_command, "status_code", "None")}'
                    return

            with lock:
                players.at[index, 'reboot'] = 'Reboot command sent.'

            # Continue with reboot check loop...
            time.sleep(4)
            with lock:
                players.at[index, 'reboot'] = 'Awaiting response from player...'

            start_time = time.time()
            max_wait = 60
            player_ping = False
            player_available = False

            while not player_available and (time.time() - start_time) < max_wait:
                if not player_ping:
                    player_ping = bsp.ping(address)
                player_available = bsp.reachUrl(address, 8080)
                time.sleep(2)

            if player_available:
                with lock:
                    players.at[index, 'reboot'] = 'Reboot Complete'
            else:
                with lock:
                    players.at[index, 'reboot'] = 'Timeout waiting for player'

        except Exception as e:
            with lock:
                players.at[index, 'reboot'] = f'Error: {e}'

    
              


    # UI   
    u.st_init("already_processed", False)
    if not st.session_state["already_processed"]:
        players['reboot'] = 'Initializing'
        #players['name'] = 'Initializing'
        threads = []
        table_placeholder = st.empty()

        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = []
            for idx, row in players.iterrows():
                future = executor.submit(process_player, idx, row['address'], row['password'])
                futures.append(future)

            # While threads are running, keep refreshing the table
            while any(not f.done() for f in futures):
                with lock:
                    table_placeholder.dataframe(players, hide_index=True, column_order=['address', 'serial', 'reboot'])
                time.sleep(1)

        # Final update
        with lock:
            table_placeholder.dataframe(players, hide_index=True, column_order=['address', 'serial', 'reboot'])
        
        st.session_state.players = players
        st.session_state.already_processed = True
    players['is_error'] = players['reboot'] != 'Reboot Complete'
        
    # Error Highlighting
    def highlight_errors(row):
        if row['is_error']:
            return ['background-color: rgba(255, 0, 0, 0.2)'] * len(row)
        return [''] * len(row)

    styled_df = players.style.apply(highlight_errors, axis=1)

    table_placeholder.dataframe(styled_df, hide_index=True, column_order=['address', 'serial', 'reboot'])
    
    st.success("All players processed.")

    # Store updated player data and change view state
    st.session_state.players = players
    st.session_state.has_processed = True
    go_to(key, 'multi_final')
    st.rerun()

elif st.session_state[key] == 'multi_final':
    players = st.session_state.players
    reject_df = st.session_state.reject_df

    def highlight_errors(row):
        if row['is_error']:
            return ['background-color: rgba(255, 0, 0, 0.2)'] * len(row)
        return [''] * len(row)
    
    styled_df = players.style.apply(highlight_errors, axis=1)
    st.dataframe(styled_df, hide_index=True, column_order=['address', 'serial', 'reboot'])
    if st.session_state.dropped_rows > 0:
        file_data = reject_df.drop(columns=['password']).to_csv(index=False)
        st.download_button('Download unreachable players', data=file_data, file_name='Unreachable Players.csv')

if st.session_state[key] != 'menu':
    exit1, exit2 = st.columns([7,2])
    with exit2:
        if st.button('Back to Menu', use_container_width=True):
            for k in list(st.session_state.keys()):
                if k != key:
                    del st.session_state[k]
            st.session_state[key] = 'menu'
            st.rerun()