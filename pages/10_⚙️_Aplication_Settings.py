import streamlit as st
from modules.update_check import check_for_update

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
        st.write(update)