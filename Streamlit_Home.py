import streamlit as st
import leafmap.foliumap as leafmap
import geemap.foliumap as geemap
import ee

if "ee_service_account" in st.secrets:
    sa = st.secrets["ee_service_account"]
    key_json = st.secrets["ee_private_key"]   # paste the entire JSON key into this secret
    project = st.secrets["ee_project"]

    credentials = ee.ServiceAccountCredentials(sa, key_data=key_json)
    ee.Initialize(credentials=credentials, project=project)
else:
    # Local dev fallback (interactive on your laptop only)
    try:
        ee.Initialize()
    except Exception:
        ee.Authenticate()
        ee.Initialize()

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
