import streamlit as st
import ee
import leafmap.foliumap as leafmap
import folium

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

# ---------------- Helper: EE -> Folium TileLayer ----------------
def ee_to_folium_tilelayer(ee_image: ee.Image, vis_params: dict, name: str) -> folium.TileLayer:
    """Create a folium.TileLayer from an ee.Image."""
    map_id_dict = ee.Image(ee_image).getMapId(vis_params)
    return folium.TileLayer(
        tiles=map_id_dict["tile_fetcher"].url_format,
        attr="Google Earth Engine",
        name=name,
        overlay=True,
        control=True,
    )

# ---------------- Landsat composites (build once, reuse) ----------------
# Note: Landsat 7 SR has scale factors. Your original code didn’t apply scaling,
# so this keeps your behavior the same (raw SR integers).
@st.cache_resource
def get_landsat7_composites():
    ic = ee.ImageCollection("LANDSAT/LE07/C02/T1_L2")

    img_2001 = (
        ic.filterDate("2001-01-01", "2002-01-01")
          .median()
    )

    img_2020 = (
        ic.filterDate("2020-01-01", "2021-01-01")
          .median()
    )

    return img_2001, img_2020

collection_2001, collection_2020 = get_landsat7_composites()

vis = {
    "bands": ["SR_B1", "SR_B4", "SR_B7"],
    "min": 0,
    "max": 40000,
}

left_layer = ee_to_folium_tilelayer(collection_2001, vis, "Year of 2001")
right_layer = ee_to_folium_tilelayer(collection_2020, vis, "Year of 2020")

# ---------------- Factory to build each split map ----------------
def make_split_map(center_lat: float, center_lon: float, zoom: int) -> leafmap.Map:
    m = leafmap.Map(dragging=False, scrollWheelZoom=False, zoomControl=False)

    # Optional: give it a visible basemap so it never looks "blank"
    m.add_basemap("HYBRID")  # or "SATELLITE", "ROADMAP"

    m.split_map(left_layer, right_layer)
    m.add_text(date1, **params1)
    m.add_text(date2, **params2)

    # NOTE: leafmap (folium) uses lat, lon
    m.set_center(center_lat, center_lon, zoom)
    return m

# Prebuild maps (lat, lon)
Map1 = make_split_map(36.20, -114.41, 10)                    # Lake Mead
Map2 = make_split_map(33.31321356759435, -115.85446197484563, 10)  # Salton Sea
Map3 = make_split_map(41.08008337991904, -112.43915367456692, 9)   # Great Salt Lake
Map4 = make_split_map(45.25402686187612, 59.013008598795004, 8)    # Aral Sea


# ---------------- UI selector ----------------
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
