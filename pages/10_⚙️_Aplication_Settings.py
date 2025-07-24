import streamlit as st
from modules.update_check import check_for_update, get_repo_url
import webbrowser

st.set_page_config(
    page_title="Application Settings",
    page_icon="⚙️",
    layout="wide"
    )

st.title('Application Settings')
o1,o2,o3,o4 = st.columns([1,1,1,1])
with o1:
    if st.button('Check for updates', use_container_width=True):
        update = check_for_update()
        status = update[0]
        message = update[1]
        if status == False:
            st.success(message)
        elif status == True:
            st.info(message)
            st.write(f'You can download the new version by clicking the button')
            st.button('Newest version', on_click=lambda: webbrowser.open(get_repo_url()))
        elif status == None:
            st.error(message)