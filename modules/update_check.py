import json
from pathlib import Path
import requests
import streamlit as st

GITHUB_USER = "TobiaszGans"
REPO_NAME = "Brightsign-remote-management-tool"
PREFERENCES_PATH = Path("cache/preferences.json")

def get_current_version():
    if not PREFERENCES_PATH.exists():
        return None
    with open(PREFERENCES_PATH, "r") as f:
        prefs = json.load(f)
    return prefs.get("currentVersion")


def get_repo_url():
    return f"https://github.com/{GITHUB_USER}/{REPO_NAME}/releases/latest"

def get_latest_release_version(user, repo):
    url = f"https://api.github.com/repos/{user}/{repo}/releases/latest"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    return data["tag_name"]

def check_for_update():
    current_version = get_current_version()
    if current_version is None:
        return (None ,"Could not find current version information")
        

    latest_version = get_latest_release_version(GITHUB_USER, REPO_NAME)

    if latest_version != current_version:
        return (True, f"Update available! Latest version: {latest_version}, Your version: {current_version}")
    else:
        return(False ,"You're running the latest version of the application")
