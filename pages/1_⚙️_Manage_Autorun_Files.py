import os, glob, time
import streamlit as st
from modules import utils as u
from modules.utils import go_to


st.set_page_config(
    page_title="Manage Autorun Files",
    page_icon="⚙️",
    layout="wide"
    )

st.title('Manage Autorun Files')
key = 'manage_autoruns'

disable_editing_buttons = not u.check_cache()

u.st_init(key, 'menu')

if st.session_state[key] == 'menu':
    c1, c2, c3 = st.columns([1,1,1])
    with c1:
        st.button('Upload a new autorun File', use_container_width=True, on_click=lambda:go_to(key, 'upload_new'))
    with c2:
        st.button('Edit existing autorun files', use_container_width=True, disabled=disable_editing_buttons, on_click=lambda:go_to(key, 'edit'))
    with c3:
        st.button('Delete all cached autorun files', use_container_width=True, disabled=disable_editing_buttons, on_click=lambda:go_to(key, 'delete'), type='primary')

elif st.session_state[key] == 'upload_new':
    st.write('Upload New Autorun')
    autorun = st.file_uploader('Please upload the autorun to be installed on the players.', type='zip')
    version = st.text_input('Please state the version of the autorun')

    if autorun is None or version.strip() == '':
        disable_button = True
    else:
        disable_button = False

    if st.button('Save autorun', disabled=disable_button):
        st.session_state.autorun = autorun
        st.session_state.version = version
        go_to(key, 'check_cache')
        st.rerun()

elif st.session_state[key] == 'check_cache':
    cache_folder_exists = os.path.exists('./cache/autoruns/')
    autorun = st.session_state.autorun
    version = st.session_state.version
    if not cache_folder_exists():
        os.mkdir('./cache/autoruns/')
    version_exist = os.path.exists(f'./cache/autoruns/{version}')
    if version_exist:
        st.warning('This autorun version already exists. Do you want to overwrite?')
        deny, confirm = st.columns([1,1])
        with deny:
            if st.button('No, go back to menu', use_container_width=True):
                for k in list(st.session_state.keys()):
                    del st.session_state[k]
                    key = 'manage_autoruns'
                    u.st_init(key, 'menu')
                st.rerun()
        with confirm:
            if st.button('Yes, continue', use_container_width=True, type='primary'):
                files = glob.glob(f'./cache/autoruns/{version}/*')
                hidden_files = glob.glob(f'./cache/autoruns/{version}/.*')
                for f in files:
                    os.remove(f)
                for f in hidden_files:
                    os.remove(f)
                os.rmdir(f'./cache/autoruns/{version}')
                go_to(key, 'save_file')
                st.rerun()
    else:
        go_to(key, 'save_file')
        st.rerun()

elif st.session_state[key] == 'save_file':
    autorun = st.session_state.autorun
    version = st.session_state.version
    try:
        os.makedirs(f'./cache/autoruns/{version}', exist_ok=True)
        with open(f'./cache/autoruns/{version}/autorun.zip', 'wb') as file:
            file.write(autorun.getvalue())
            go_to(key, 'upload_success')
            st.rerun()
    except Exception as e:
        st.error('There was an error while trying to save the file.')
        print(e)

elif st.session_state[key] == 'upload_success':
    st.success('Saved autorun successfully')


elif st.session_state[key] == 'delete':
    st.warning("You're about to delete all saved autorun files. Are you sure you want to continue?")
    deny, confirm = st.columns([1,1])
    with deny:
        if st.button('No, go back to menu', use_container_width=True):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
                key = 'manage_autoruns'
                u.st_init(key, 'menu')
            st.rerun()
    with confirm:
        if st.button('Yes, continue', use_container_width=True, type='primary'):
            go_to(key, 'delete_files')
            st.rerun()

elif st.session_state[key] == 'delete_files':
    with st.spinner('removing all cached files'):
        try:
            u.clean_folder('./cache/autoruns/')
            go_to(key, 'delete_success')
            st.rerun()
        except Exception as e:
            st.error('There was an error while trying to remove all files.')
            print(e)

elif st.session_state[key] == 'delete_success':
    st.success('Succesfully deleted all autorun files')


elif st.session_state[key] == 'edit':
    folders = os.listdir('./cache/autoruns')
    time.sleep(0.1)
    for folder in folders:
        with st.container(border=True):
            c1,c2,c3 = st.columns([1,1,1])
            with c1:
                st.markdown(f'<center><h4>{folder}</h4></center>', unsafe_allow_html=True)
            with c2:
                if st.button('Open in file explorer', key=f'open_in_explorer_{folder}',use_container_width=True):
                    try:
                        u.open_in_explorer(f'./cache/autoruns/{folder}')
                        st.toast('Succesfully deleted the autorun.')
                    except:
                        st.error('Failed to delete the folder')
            with c3:
                st.button('Delete the autorun', on_click=lambda: u.clean_folder(f'./cache/autoruns/{folder}'), key=f'delete_{folder}', type='primary',use_container_width=True)





b1, b2 = st.columns([7,1])
with b2:
    if st.session_state[key] != 'menu':
        if st.button('Go back to menu', use_container_width=True):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
                key = 'manage_autoruns'
                u.st_init(key, 'menu')
            st.rerun()