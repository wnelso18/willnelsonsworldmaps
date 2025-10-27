
import streamlit as st
import leafmap.foliumap as leafmap
import ee

# AUTHENTICATE AND INITIALIZE EARTH ENGINE-----------------------------------------------------------------------
import json, os
from google.oauth2.credentials import Credentials as UserCredentials

def _get_oauth_credentials():
    data = st.secrets.get("ee_private_key") or os.environ.get("EE_OAUTH_JSON")
    if not data:
        return None
    info = json.loads(data) if isinstance(data, str) else dict(data)

    # Must contain: client_id, client_secret, refresh_token, scopes (list)
    needed = {"client_id", "client_secret", "refresh_token", "scopes"}
    if not needed.issubset(info.keys()):
        return None

    return UserCredentials(
        token=None,
        refresh_token=info["refresh_token"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=info["client_id"],
        client_secret=info["client_secret"],
        scopes=info["scopes"],
    )

project = st.secrets.get("ee_project") or os.environ.get("EE_PROJECT")
creds = _get_oauth_credentials()

if creds and project:
    ee.Initialize(credentials=creds, project=project)
else:
    # Local interactive fallback only (won't work on Streamlit Cloud)
    try:
        ee.Initialize(project=project)
    except Exception:
        ee.Authenticate()
        ee.Initialize(project=project)

# AUTHENTICATE AND INITIALIZE EARTH ENGINE (end)-------------------------------------------------------------------

st.set_page_config(layout="wide")

st.sidebar.info('Credits:')
st.sidebar.markdown('leafmap foliumap module')

col1, col2 = st.columns([7, 3])

options = list(leafmap.basemaps.keys())


with col2:
    dropdown = st.selectbox("Basemap", options)

    default_url = leafmap.basemaps[dropdown].tiles

    url = st.text_input("Enter URL", default_url)

m = leafmap.Map()
m.add_basemap(dropdown)

if url:
    m.add_tile_layer(url, name='Tile Layer', attribution=' ')

with col1:
    m.to_streamlit()

