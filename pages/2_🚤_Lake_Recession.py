import streamlit as st
import ee
import geemap.foliumap as geemap

st.set_page_config(layout="wide")


# ---------------------------------------------------------------------------------------------------
# Map1: Lake Mead

Map1 = geemap.Map(dragging=False, scrollWheelZoom=False, zoomControl=False)

collection1 = (
    ee.ImageCollection("LANDSAT/LE07/C02/T1_L2")
    .filter(ee.Filter.date('2001-01-01', '2002-01-01'))
    .median()
)

collection2 = (
    ee.ImageCollection("LANDSAT/LE07/C02/T1_L2")
    .filter(ee.Filter.date('2020-01-01', '2021-01-01'))
    .median()
)

vis = {
  'bands': ['SR_B3', 'SR_B2', 'SR_B1'],
  'min': 0.0,
  'max': 40000,
}

left = geemap.ee_tile_layer(collection1, vis, 'Year of 2001')
right = geemap.ee_tile_layer(collection2, vis, 'Year of 2020')

Map1.split_map(left, right)
Map1.setCenter(-114.41, 36.20, 10.2)

# ---------------------------------------------------------------------------------------------------
# Map2: Salton Sea

Map2 = geemap.Map(dragging=False, scrollWheelZoom=False, zoomControl=False)

collection1 = (
    ee.ImageCollection("LANDSAT/LE07/C02/T1_L2")
    .filter(ee.Filter.date('2001-01-01', '2002-01-01'))
    .median()
)

collection2 = (
    ee.ImageCollection("LANDSAT/LE07/C02/T1_L2")
    .filter(ee.Filter.date('2020-01-01', '2021-01-01'))
    .median()
)

vis = {
  'bands': ['SR_B3', 'SR_B2', 'SR_B1'],
  'min': 0.0,
  'max': 40000,
}

left = geemap.ee_tile_layer(collection1, vis, 'Year of 2001')
right = geemap.ee_tile_layer(collection2, vis, 'Year of 2020')

Map2.split_map(left, right)
Map2.setCenter( -115.85446197484563,33.31321356759435, 10)

# ---------------------------------------------------------------------------------------------------
# Map3: Salt Lake

Map3 = geemap.Map(dragging=False, scrollWheelZoom=False, zoomControl=False)

collection1 = (
    ee.ImageCollection("LANDSAT/LE07/C02/T1_L2")
    .filter(ee.Filter.date('2001-01-01', '2002-01-01'))
    .median()
)

collection2 = (
    ee.ImageCollection("LANDSAT/LE07/C02/T1_L2")
    .filter(ee.Filter.date('2020-01-01', '2021-01-01'))
    .median()
)

vis = {
  'bands': ['SR_B3', 'SR_B2', 'SR_B1'],
  'min': 0.0,
  'max': 40000,
}

left = geemap.ee_tile_layer(collection1, vis, 'Year of 2001')
right = geemap.ee_tile_layer(collection2, vis, 'Year of 2020')

Map3.split_map(left, right)
Map3.setCenter(-112.43915367456692, 41.08008337991904, 9.3)

# ---------------------------------------------------------------------------------------------------
# Map4: Aral Sea

Map4 = geemap.Map(dragging=False, scrollWheelZoom=False, zoomControl=False)

collection1 = (
    ee.ImageCollection("LANDSAT/LE07/C02/T1_L2")
    .filter(ee.Filter.date('2001-01-01', '2002-01-01'))
    .median()
)

collection2 = (
    ee.ImageCollection("LANDSAT/LE07/C02/T1_L2")
    .filter(ee.Filter.date('2020-01-01', '2021-01-01'))
    .median()
)

vis = {
  'bands': ['SR_B3', 'SR_B2', 'SR_B1'],
  'min': 0.0,
  'max': 40000,
}

left = geemap.ee_tile_layer(collection1, vis, 'Year of 2001')
right = geemap.ee_tile_layer(collection2, vis, 'Year of 2020')

Map4.split_map(left, right)
Map4.setCenter(59.013008598795004, 45.25402686187612, 8)

# ---------------------------------------------------------------------------------------------------

option = st.selectbox(
    'Which lake would you like to view?',
    ('Lake Mead', 'Salton Sea', 'Salt Lake', 'Aral Sea'))

if option == 'Lake Mead':
    Map1.to_streamlit(height=600)

elif option == 'Salton Sea':
    Map2.to_streamlit(height=600)

elif option == 'Salt Lake':
    Map3.to_streamlit(height=600)

elif option == 'Aral Sea':
    Map4.to_streamlit(height=600)
