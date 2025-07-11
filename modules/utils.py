import streamlit as st

def st_init(key, state):
    if key not in st.session_state:
        st.session_state[key] = state

def go_to(key, state):
    st.session_state[key] = state

