import streamlit as st
from modules import brightsign_API as bsp, utils as u
from modules.utils import go_to
import time, threading, io, zipfile
import pandas as pd
from concurrent.futures import ThreadPoolExecutor

def custom_template():
    template_list = [
        ['192.168.1.47', 'usd81233212.corpnet1.com', 'Password123','USD1234567'],
    ]
    template = pd.DataFrame(template_list, columns=['ip', "fqdn",'password','serial'])
    return template.to_csv(index=False)


st.set_page_config(
    page_title="Check Live Players",
    page_icon="🟢",
    layout="wide"
    )

st.title('Check Live Players')

key = 'CheckLiveDevices'
u.st_init(key, 'multi_player')

if st.session_state[key] == 'multi_player':
    template = custom_template()
    u.multi_player_input(key, next_step='ping_players', custom_template=template)

elif st.session_state[key] == 'ping_players':
    players = st.session_state.players

    # Lock for thread-safe updates
    lock = threading.Lock()

    # Shared flag to track completion
    processing_done = False

    # Threaded function (logic only)
    def process_player(index, ip, fqdn ,password, serial):
        # Ping IP
        if pd.notna(ip):
            with lock:
                players.at[index, 'ping_ip'] = 'Pinging the player'
            ip_ping = bsp.ping(ip)
            with lock:
                players.at[index, 'ping_ip'] = ip_ping
        else:
            with lock:
                players.at[index, 'ping_ip'] = 'No IP'
        # Ping FQDN
        if pd.notna(fqdn):
            with lock:
                players.at[index, 'ping_fqdn'] = 'Pinging the player'
            fqdn_ping = bsp.ping(fqdn)
            with lock:
                players.at[index, 'ping_fqdn'] = fqdn_ping
        else:
            with lock:
                players.at[index, 'ping_fqdn'] = 'No FQDN'
        # Reach IP
        if pd.notna(ip):
            with lock:
                players.at[index, 'reach_ip'] = 'Trying to Reach the player'
            ip_reach = bsp.reachUrl(ip, 8080)
            with lock:
                players.at[index, 'reach_ip'] = ip_reach
        else:
            ip_reach = False
            with lock:
                players.at[index, 'reach_ip'] = 'No IP'
        # Reach FQDN
        if pd.notna(fqdn):
            with lock:
                players.at[index, 'reach_fqdn'] = 'Trying to Reach the player'
            fqdn_reach = bsp.reachUrl(fqdn, 8080)
            with lock:
                players.at[index, 'reach_fqdn'] = fqdn_reach
        else:
            fqdn_reach = False
            with lock:
                players.at[index, 'reach_fqdn'] = 'No FQDN'
            # Validate password
        if fqdn_reach or ip_reach:
            with lock:
                players.at[index, 'password_valid'] = 'Trying to log into the player'
            if ip_reach:
                login = bsp.init_login(url=ip,password=password, port=8080)
            elif fqdn_reach:
                login = bsp.init_login(url=fqdn,password=password, port=8080)
            
            password_valid = login.status_code == 200
            with lock:
                players.at[index, 'password_valid'] = password_valid
        else:
            with lock:
                players.at[index, 'password_valid'] = 'Skip'
        
        

    # UI
    u.st_init("already_processed", False)
    if not st.session_state["already_processed"]:
        players['name'] = 'Initialising'
        players['ping_ip'] = 'Initialising'
        players['ping_fqdn'] = 'Initialising'
        players['reach_ip'] = 'Initialising'
        players['reach_fqdn'] = 'Initialising'
        players['password_valid'] = 'Initialising'
        threads = []
        table_placeholder = st.empty()

        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = []
            for idx, row in players.iterrows():
                future = executor.submit(process_player, idx, row['ip'], row['fqdn'], row['password'], row['serial'])
                futures.append(future)

            # While threads are running, keep refreshing the table
            while any(not f.done() for f in futures):
                with lock:
                    table_placeholder.dataframe(players, hide_index=True, column_order=['ip', "fqdn",'serial', 'name', 'ping_ip', 'ping_fqdn', 'reach_ip', 'reach_fqdn', 'password_valid'])
                time.sleep(1)

        # Final update
        def style_row(row):
            num_columns = len(row)
            
            # Set variables for easier color matching
            if row['ping_ip'] == 'No IP' or row['ping_ip'] == False:
                ip_ping = False
            else:
                ip_ping = True

            if row['ping_fqdn'] == 'No FQDN' or row['ping_fqdn'] == False:
                fqdn_ping = False
            else:
                fqdn_ping = True

            if row['reach_ip'] == 'No IP' or row['reach_ip'] == False:
                reach_ip = False
            else:
                reach_ip = True

            if row['reach_fqdn'] == 'No FQDN' or row['reach_fqdn'] == False:
                reach_fqdn = False
            else:
                reach_fqdn = True
            
            password_valid = row['password_valid']
            
            if (ip_ping or fqdn_ping) and (reach_ip or reach_fqdn) and password_valid:
                return ['background-color: #014d12'] * num_columns  # green for success
            elif (ip_ping or fqdn_ping) and (reach_ip or reach_fqdn) and not password_valid:
                return ['background-color: #64c0f5; color: black'] * num_columns # blue for wrong Pasword
            elif not ip_ping and not fqdn_ping and not reach_ip and not reach_fqdn:
                return ['background-color: #910117'] * num_columns  # red for fail
            return [''] * num_columns
        
        styled_players = players.style.apply(style_row, axis=1)

        table_placeholder.dataframe(
            styled_players,
            hide_index=True,
            column_order=['ip', "fqdn", 'serial', 'name', 'ping_ip', 'ping_fqdn', 'reach_ip', 'reach_fqdn', 'password_valid']
        )
    square = '■'
    st.write('Legend:')
    st.markdown(f':green[{square}] - Player Online')
    st.markdown(f':blue[{square}] - Player Online, incorrect password')
    st.markdown(f':red[{square}] - Player Offline')
        
    st.session_state.players = players
    st.session_state.already_processed = True

    if st.button('Process another batch'):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
            u.st_init(key, 'multi_player')
        st.rerun()