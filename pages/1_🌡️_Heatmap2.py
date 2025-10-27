import streamlit as st
import ee
import geemap.foliumap as geemap

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

st.header('Global Land Temperatures')

st.markdown(
    """
    The split map below shows the average global land temperatures. On the left side of the slider,
    average land temperatures from 1990-1999 are displayed. On the right side of the slider, average
    land temperatures from 2010-2019 are displayed.
    """
)

Map = geemap.Map()

land9099 = (
    ee.ImageCollection("ECMWF/ERA5_LAND/MONTHLY")
    .filter(ee.Filter.date('1990-05-01','1999-5-01'))
    .map(lambda img: img.subtract(273.15))
)


land1019 = (
    ee.ImageCollection("ECMWF/ERA5_LAND/MONTHLY")
    .filter(ee.Filter.date('2010-05-01','2019-05-01'))
    .map(lambda img: img.subtract(273.15))
)


vis = {
    'min': -15,
    'max': 38,
    'bands': ['skin_temperature'],
    'palette': [
    "#000080","#0000D9","#4000FF","#8000FF","#0080FF","#00FFFF",
    "#00FF80","#80FF00","#DAFF00","#FFFF00","#FFF500","#FFDA00",
    "#FFB000","#FFA400","#FF4F00","#FF2500","#FF0A00","#FF00FF",
  ]
}


left_layer = geemap.ee_tile_layer(land9099, vis, 'Land Temps 9099')
right_layer = geemap.ee_tile_layer(land1019, vis, 'Land Temps 1019')

# --------------------------------------------------------------------------------------


date1 = '1990-1999'
date2 = '2010-2019'

params1 = {
    'fontsize': 30,
    'fontcolor': 'blue',
    'bold': True,
    'padding': '10px',
    'background': True,
    'bg_color': 'white',
    'border_radius': '5px',
    'position': 'bottomleft',
}

params2 = {
    'fontsize': 30,
    'fontcolor': 'blue',
    'bold': True,
    'padding': '10px',
    'background': True,
    'bg_color': 'white',
    'border_radius': '5px',
    'position': 'bottomright',
}

# --------------------------------------------------------------------------------------

Map.split_map(left_layer, right_layer)
Map.add_colorbar(vis, label="Temp (C)", layer_name="Land Temp")
Map.add_text(date1, **params1)
Map.add_text(date2, **params2)
Map.to_streamlit(height=600)

st.markdown(
    """
    The layer for this map was acquired through Google Earth Engine Datasets. 
    Temperature data was recorded by Copernicus Climate Data.
    """
)
