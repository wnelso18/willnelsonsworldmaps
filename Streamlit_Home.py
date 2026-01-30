import streamlit as st
import leafmap.foliumap as leafmap
# import geemap.foliumap as geemap
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

# Customize the sidebar
# To return to my personal website follow this link: https://willnelsonsworld-production.up.railway.app/

markdown = """
GitHub Repository: https://github.com/wnelso18/willnelsonsworldmaps
"""

st.sidebar.title("Info:")
st.sidebar.info(markdown)
logo = "images/powerT.png"
st.sidebar.image(logo)

# Customize page title
st.title("Geospatial Applications for Dynamically Viewing Earth!")

st.markdown(
    """
    This website is a branch off of my personal website 'Will Nelson's World'. Here you can find my python-created geospatial applications.
    """
)

st.header("Summary")

markdown = """

From lake recession to global land temperature changes, I will be adding more and more projects over time. 

Enjoy this first Map as it shows up-to-date information about global snow cover!

"""

st.markdown(markdown)

MapS = leafmap.Map()

# Build an ee.Image (not ImageCollection)
snowCover = (
    ee.ImageCollection("MODIS/061/MOD10A1")
      .filterDate("2025-12-28", "2026-01-05")
      .select("NDSI_Snow_Cover")
      .mosaic()
)

snowCoverVis = {
    "min": 0,
    "max": 100,
    "palette": ["000000", "0dffff", "0524ff", "ffffff"],
}

collection = ee.FeatureCollection("TIGER/2018/States")
country = ee.FeatureCollection("users/giswqs/public/countries")

style_us = {"color": "yellow", "width": 2, "fillColor": "00000000"}
style_world = {"color": "cyan", "width": 2, "fillColor": "00000000"}

MapS.set_center(-95.13, 43.35, 4)                 # zoom int
MapS.add_basemap("SATELLITE")

# Add EE layers
MapS.add_ee_layer(snowCover, snowCoverVis, "Snow Cover")
MapS.add_ee_layer(collection.style(**style_us), {}, "US States")
MapS.add_ee_layer(country.style(**style_world), {}, "World Countries")

MapS.add_layer_control()
MapS.to_streamlit(height=700)