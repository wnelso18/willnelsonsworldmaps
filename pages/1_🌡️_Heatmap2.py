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
st.header("Global Land Temperatures")

st.markdown(
    """
    The split map below shows the average global land temperatures. On the left side of the slider,
    average land temperatures from 1990-1999 are displayed. On the right side of the slider, average
    land temperatures from 2010-2019 are displayed.
    """
)

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

# ---------------- Build ee.Image layers (NOT ImageCollections) ----------------
def era5_land_mean_celsius(start_date: str, end_date: str) -> ee.Image:
    # ERA5-Land monthly band is Kelvin; convert to Celsius after mean.
    col = (
        ee.ImageCollection("ECMWF/ERA5_LAND/MONTHLY")
        .filterDate(start_date, end_date)
        .select("skin_temperature")
    )
    return col.mean().subtract(273.15).rename("skin_temperature")

land_9099 = era5_land_mean_celsius("1990-05-01", "1999-05-01")
land_1019 = era5_land_mean_celsius("2010-05-01", "2019-05-01")

vis = {
    "min": -15,
    "max": 38,
    "bands": ["skin_temperature"],
    "palette": [
        "000080","0000D9","4000FF","8000FF","0080FF","00FFFF",
        "00FF80","80FF00","DAFF00","FFFF00","FFF500","FFDA00",
        "FFB000","FFA400","FF4F00","FF2500","FF0A00","FF00FF",
    ],
}


left_layer = ee_to_folium_tilelayer(land_9099, vis, "Land Temps 1990–1999")
right_layer = ee_to_folium_tilelayer(land_1019, vis, "Land Temps 2010–2019")

# ---------------- Leafmap map + split control ----------------
m = leafmap.Map()
m.split_map(left_layer, right_layer)


m.add_colorbar(
    colors=vis["palette"],
    vmin=vis["min"],
    vmax=vis["max"],
    label="Temp (°C)",
)

date1 = "1990–1999"
date2 = "2010–2019"

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

m.add_text(date1, **params1)
m.add_text(date2, **params2)
m.to_streamlit(height=600)

st.markdown(
    """
    The layer for this map was acquired through Google Earth Engine Datasets. 
    Temperature data was recorded by Copernicus Climate Data.
    """
)
