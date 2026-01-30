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

collection = ee.FeatureCollection("TIGER/2018/States")

dataset = ee.ImageCollection('MODIS/061/MOD10A1') \
          .filter(ee.Filter.date('2025-12-28', '2026-1-05'))

country = (ee.FeatureCollection('users/giswqs/public/countries'))

snowCover = dataset.select('NDSI_Snow_Cover')


snowCoverVis = {
  'min': 0.0,
  'max': 100.0,
  'palette': ['black', '0dffff', '0524ff', 'ffffff'],
}

style = {
    'color':'white',
    'width': 0.3,
    'lineType':'solid',
    'fillColor':'ffffff00',
}


MapS.setCenter(-95.13, 43.35, 3.5)
MapS.add_basemap(basemap='SATELLITE')
MapS.addLayer(snowCover, snowCoverVis, 'Snow Cover')
MapS.addLayer(collection.style(**style), {}, 'US States')
MapS.addLayer(country.style(**style), {}, 'World Countries')

MapS.to_streamlit()
