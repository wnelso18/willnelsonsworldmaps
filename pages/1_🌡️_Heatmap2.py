import streamlit as st
import ee
import leafmap.foliumap as leafmap

# ---------------- EE AUTH (same logic, slightly safer) ----------------
import json, os
from google.oauth2.credentials import Credentials as UserCredentials

@st.cache_resource
def init_ee():
    def _get_oauth_credentials():
        data = st.secrets.get("ee_private_key") or os.environ.get("EE_OAUTH_JSON")
        if not data:
            return None
        info = json.loads(data) if isinstance(data, str) else dict(data)

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
        return True

    # Local interactive fallback only (won't work on Streamlit Cloud)
    try:
        ee.Initialize(project=project)
        return True
    except Exception:
        ee.Authenticate()
        ee.Initialize(project=project)
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

Map = leafmap.Map()

# ---------------- Build ee.Image layers (NOT ImageCollections) ----------------
# ERA5-Land monthly has band 'skin_temperature' (Kelvin).
# Convert to Celsius AFTER selecting the band so we're not subtracting from everything.
def era5_land_mean_celsius(start_date: str, end_date: str) -> ee.Image:
    col = (
        ee.ImageCollection("ECMWF/ERA5_LAND/MONTHLY")
        .filterDate(start_date, end_date)
        .select("skin_temperature")
    )
    # Mean across the period, then convert K -> C
    return col.mean().subtract(273.15).rename("skin_temperature")

land9099_img = era5_land_mean_celsius("1990-05-01", "1999-05-01")
land1019_img = era5_land_mean_celsius("2010-05-01", "2019-05-01")

vis = {
    "min": -15,
    "max": 38,
    "bands": ["skin_temperature"],
    "palette": [
        "#000080", "#0000D9", "#4000FF", "#8000FF", "#0080FF", "#00FFFF",
        "#00FF80", "#80FF00", "#DAFF00", "#FFFF00", "#FFF500", "#FFDA00",
        "#FFB000", "#FFA400", "#FF4F00", "#FF2500", "#FF0A00", "#FF00FF",
    ],
}

# IMPORTANT: ee_tile_layer expects ee.Image (we now provide ee.Image)
left_layer = leafmap.ee_tile_layer(land9099_img, vis, name="Land Temps 1990–1999")
right_layer = leafmap.ee_tile_layer(land1019_img, vis, name="Land Temps 2010–2019")

# ---------------- Labels / UI ----------------
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

# ---------------- Map rendering ----------------
Map.split_map(left_layer, right_layer)
Map.add_colorbar(vis, label="Temp (°C)", layer_name="Land Temp")
Map.add_text(date1, **params1)
Map.add_text(date2, **params2)
Map.to_streamlit(height=600)

st.markdown(
    """
    The layer for this map was acquired through Google Earth Engine Datasets. 
    Temperature data was recorded by Copernicus Climate Data.
    """
)
