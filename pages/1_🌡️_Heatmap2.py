import streamlit as st
import ee
import geemap.foliumap as geemap

st.set_page_config(layout="wide")

Map = geemap.Map()

land9099 = (
    ee.ImageCollection("ECMWF/ERA5_LAND/MONTHLY")
    .filter(ee.Filter.date('1990-05-01','1999-5-01'))
    .map(lambda img: img.subtract(273.15))
)


land1019 = (
    ee.ImageCollection("ECMWF/ERA5_LAND/MONTHLY")
    .filter(ee.Filter.date('2010-05-01','2019-05-01'))
    .map(lambda img: img.subtract(273.15))
)


vis = {
    'min': -15,
    'max': 38,
    'bands': ['skin_temperature'],
    'palette': [
    "#000080","#0000D9","#4000FF","#8000FF","#0080FF","#00FFFF",
    "#00FF80","#80FF00","#DAFF00","#FFFF00","#FFF500","#FFDA00",
    "#FFB000","#FFA400","#FF4F00","#FF2500","#FF0A00","#FF00FF",
  ]
}


left_layer = geemap.ee_tile_layer(land9099, vis, 'Land Temps 1985')
right_layer = geemap.ee_tile_layer(land1019, vis, 'Land Temps 1019')

Map.split_map(left_layer, right_layer)
Map.add_colorbar(vis, label="Temp (C)", layer_name="Land Temp")

Map.to_streamlit(height=700)
