import streamlit as st
import pandas as pd

def st_init(key, state):
    if key not in st.session_state:
        st.session_state[key] = state

def go_to(key, state):
    st.session_state[key] = state

def clear_screen():
    # Use at the end of a short state or in an emtpy state before a long process
    display = st.empty()
    # the below is the fix
    for i in range(0, 100):
        st.markdown(" ")

def upload_template():
    template_list = [
        ['192.168.1.47', 'Password123','USD1234567'],
        ['usd81233212.corpnet1.com', 'paSSword321','']
    ]
    template = pd.DataFrame(template_list, columns=['address','password','serial'])
    return template.to_csv(index=False)