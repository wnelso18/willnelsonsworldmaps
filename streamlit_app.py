import streamlit as st
import leafmap.foliumap as leafmap
import geemap.foliumap as geemap
import ee

st.set_page_config(layout="wide")

# Customize the sidebar
markdown = """
To return to my personal website follow this link: 

GitHub Repository: https://github.com/wnelso18/willnelsonsworldmaps
"""

st.sidebar.title("About")
st.sidebar.info(markdown)
logo = "images/powerT.png"
st.sidebar.image(logo)

# Customize page title
st.title("Gesopatial Applications for Dynamically Viewing Earth!")

st.markdown(
    """
    This website is a branch off of my personal website 'Will Nelson's World'. Here you can find my python-created geospatial applications. 
    """
)

st.header("Summary")

markdown = """

From lake recession to global land temperature changes, I will be adding more and more projects over time. 

Enjoy this first Map as it shows up to date information about global wildfire locations!

"""

st.markdown(markdown)

MapF = geemap.Map()

dataset = ee.ImageCollection('MODIS/061/MOD14A1') \
                  .filter(ee.Filter.date('2016-11-25', '2016-11-30'))
fireMaskVis = {
  'min': 0.0,
  'max': 6000.0,
  'bands': ['MaxFRP', 'FireMask', 'FireMask'],
}
MapF.setCenter(6.746, 46.529, 2)
MapF.add_basemap("SATELLITE")
MapF.addLayer(dataset, fireMaskVis, 'Fire Mask')


MapF.to_streamlit(height=500)