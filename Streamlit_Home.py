import streamlit as st
import leafmap.foliumap as leafmap
import geemap.foliumap as geemap
import ee

import os, json
from google.oauth2 import service_account

def _get_ee_credentials():
    """
    Load EE service account creds from Streamlit secrets or environment.
    
    """
    if "ee_private_key" in st.secrets:
        key_obj = st.secrets["ee_private_key"]

        if isinstance(key_obj, str):
            info = json.loads(key_obj)
        else:
            info = dict(key_obj)
        return service_account.Credentials.from_service_account_info(
            info,
            scopes=[
                "https://www.googleapis.com/auth/earthengine",
                "https://www.googleapis.com/auth/devstorage.full_control",
            ],
        )

    # 2) (Optional) fallback to environment variables if you deploy elsewhere
    #    Set EE_PRIVATE_KEY_JSON to the full JSON *string*
    env_json = os.environ.get("EE_PRIVATE_KEY_JSON")
    if env_json:
        info = json.loads(env_json)
        return service_account.Credentials.from_service_account_info(
            info,
            scopes=[
                "https://www.googleapis.com/auth/earthengine",
                "https://www.googleapis.com/auth/devstorage.full_control",
            ],
        )

    return None

creds = _get_ee_credentials()
project = st.secrets.get("ee_project", os.environ.get("EE_PROJECT"))

if creds and project:
    ee.Initialize(credentials=creds, project=project)
else:
    try:
        ee.Initialize(project=project)
    except Exception:
        ee.Authenticate()
        ee.Initialize(project=project)

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

MapS = geemap.Map()

collection = ee.FeatureCollection("TIGER/2018/States")

dataset = ee.ImageCollection('MODIS/061/MOD10A1') \
          .filter(ee.Filter.date('2024-10-15', '2024-10-25'))

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
