import streamlit as st
import leafmap.foliumap as leafmap

st.set_page_config(layout="wide")

# Customize the sidebar
markdown = """
To go back to my personal website follow this link:

"""

# st.sidebar.title("About")
# st.sidebar.info(markdown)
# logo = "https://i.imgur.com/UbOXYAU.png"
# st.sidebar.image(logo)

# Customize page title
st.title("Gesopatial Applications for Dynamically Viewing Our Earth!")

st.markdown(
    """
    This website is a branch off of my personal website 'Will Nelson's World.' Here you can find my python-created geospatial applications. 
    """
)

st.header("Summary")

markdown = """

From lake recession to global land temperature changes, I will be adding more and more projects here over time. 

"""

st.markdown(markdown)

m = leafmap.Map(minimap_control=True)
m.add_basemap("SATELLITE")
m.to_streamlit(height=500)