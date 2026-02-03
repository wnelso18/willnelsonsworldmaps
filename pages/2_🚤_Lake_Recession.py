import streamlit as st
import ee
import leafmap.foliumap as leafmap
import folium
from folium.plugins import SideBySideLayers

# ---------------- EE AUTH ----------------
import json, os
from google.oauth2.credentials import Credentials as UserCredentials

@st.cache_resource
def init_ee():
    data = st.secrets.get("ee_private_key") or os.environ.get("EE_OAUTH_JSON")
    project = st.secrets.get("ee_project") or os.environ.get("EE_PROJECT")

    if not data or not project:
        st.error("Missing ee_private_key and/or ee_project in Streamlit Secrets.")
        st.stop()

    info = json.loads(data) if isinstance(data, str) else dict(data)
    needed = {"client_id", "client_secret", "refresh_token", "scopes"}
    if not needed.issubset(info.keys()):
        st.error("ee_private_key must contain client_id, client_secret, refresh_token, scopes.")
        st.stop()

    creds = UserCredentials(
        token=None,
        refresh_token=info["refresh_token"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=info["client_id"],
        client_secret=info["client_secret"],
        scopes=info["scopes"],
    )
    ee.Initialize(credentials=creds, project=project)
    return True

init_ee()
# ---------------- EE AUTH END ----------------

st.set_page_config(layout="wide")

st.header("Lake Recession")
st.markdown(
    """All maps show the same time period change from 2001–2020.

The left side of the slider is 2001 and the right side is 2020.
"""
)

date1 = "2001"
date2 = "2020"

params1 = {
    "fontsize": 30,
    "fontcolor": "blue",
    "bold": True,
    "padding": "10px",
    "background": True,
    "bg_color": "white",
    "border_radius": "5px",
    "position": "bottomleft",
}

params2 = {
    "fontsize": 30,
    "fontcolor": "blue",
    "bold": True,
    "padding": "10px",
    "background": True,
    "bg_color": "white",
    "border_radius": "5px",
    "position": "bottomright",
}

# ---------------- Helpers ----------------
def landsat7_sr_scaled(img: ee.Image) -> ee.Image:
    """
    Landsat Collection 2 Level-2 SR scaling:
      reflectance = SR * 0.0000275 + (-0.2)
    Applies to SR_B1..SR_B7.
    """
    sr = img.select(["SR_B1", "SR_B2", "SR_B3", "SR_B4", "SR_B5", "SR_B7"]) \
            .multiply(0.0000275).add(-0.2)
    return img.addBands(sr, overwrite=True)

@st.cache_resource
def get_landsat_composites():
    ic = ee.ImageCollection("LANDSAT/LE07/C02/T1_L2").map(landsat7_sr_scaled)
    img_2001 = ic.filterDate("2001-01-01", "2002-01-01").median()
    img_2020 = ic.filterDate("2020-01-01", "2021-01-01").median()
    return img_2001, img_2020

img_2001, img_2020 = get_landsat_composites()

# Use a sane natural-color stretch (scaled reflectance)
vis = {
    "bands": ["SR_B7", "SR_B5", "SR_B3"],  # SWIR2, SWIR1, Red
    "min": 0.02,
    "max": 0.40,
    "gamma": 1.1,
}

def ee_to_tilelayer(ee_image: ee.Image, vis_params: dict, name: str) -> folium.TileLayer:
    """
    IMPORTANT: do NOT cache this. getMapId() returns a tokenized tile URL.
    """
    map_id = ee.Image(ee_image).getMapId(vis_params)
    return folium.TileLayer(
        tiles=map_id["tile_fetcher"].url_format,
        attr="Google Earth Engine",
        name=name,
        overlay=True,
        control=True,
        opacity=1.0,
    )

def make_split_map(center_lat: float, center_lon: float, zoom: int) -> leafmap.Map:
    # Set center/zoom in constructor (no lon/lat ambiguity)
    m = leafmap.Map(
        center=[center_lat, center_lon],
        zoom=zoom,
        dragging=False,
        scrollWheelZoom=False,
        zoomControl=False,
    )

    # Give the user something even if EE tiles are slow
    m.add_basemap("HYBRID")

    # Create fresh EE tile layers each run (tokenized URLs)
    left = ee_to_tilelayer(img_2001, vis, "Year of 2001")
    right = ee_to_tilelayer(img_2020, vis, "Year of 2020")

    # MUST add layers to map BEFORE SideBySideLayers
    left.add_to(m)
    right.add_to(m)

    SideBySideLayers(left, right).add_to(m)

    m.add_text(date1, **params1)
    m.add_text(date2, **params2)

    return m

# Prebuild maps (lat, lon)
Map1 = make_split_map(36.20, -114.41, 10)                      # Lake Mead
Map2 = make_split_map(33.31321356759435, -115.85446197484563, 10)  # Salton Sea
Map3 = make_split_map(41.08008337991904, -112.43915367456692, 9)   # Great Salt Lake
Map4 = make_split_map(45.25402686187612, 59.013008598795004, 8)    # Aral Sea

option = st.selectbox(
    "Which lake would you like to view?",
    ("Lake Mead, NV", "Salton Sea, CA", "Great Salt Lake, UT", "Aral Sea, Kazakhstan/Uzebekistan"),
)

if option == "Lake Mead, NV":
    Map1.to_streamlit(height=600)
elif option == "Salton Sea, CA":
    Map2.to_streamlit(height=600)
elif option == "Great Salt Lake, UT":
    Map3.to_streamlit(height=600)
elif option == "Aral Sea, Kazakhstan/Uzebekistan":
    Map4.to_streamlit(height=600)
