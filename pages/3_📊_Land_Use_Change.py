import streamlit as st
import ee
import geemap.foliumap as geemap
import geopandas as gpd
import pandas as pd
import tempfile
import os
import uuid
import fiona
import sankee
import plotly.graph_objects as go
import plotly.express as px

# Create dictionary of landcover classes
# dict = {Class_11: 'Open Water', Class_12: 'Perennial Ice/Snow', Class_21: 'Developed, Open Space', Class_22: 'Developed, Low Intensity', 
#         Class_23: 'Developed, Medium Intensity', Class_24: 'Developed, High Intensity', Class_31: 'Barren Land (Rock/Sand/Clay)', Class_41: 'Deciduous Forest', 
#         Class_42: 'Evergreen Forest', Class_43: 'Mixed Forest', Class_51: 'Dwarf Scrub', Class_52: 'Shrub/Scrub', Class_71: 'Grassland/Herbaceous', 
#         Class_72: 'Sedge/Herbaceous', Class_73: 'Lichens', Class_74: 'Moss', Class_81: 'Pasture/Hay', Class_82: 'Cultivated Crops', 
#         Class_90: 'Woody Wetlands', Class_95: 'Emergent Herbaceous Wetlands'}

st.set_page_config(layout='wide')

def uploaded_file_to_gdf(data):

    _, file_extension = os.path.splitext(data.name)
    file_id = str(uuid.uuid4())
    file_path = os.path.join(tempfile.gettempdir(), f"{file_id}{file_extension}")

    with open(file_path, "wb") as file:
        file.write(data.getbuffer())

    if file_path.lower().endswith(".kml"):
        fiona.drvsupport.supported_drivers["KML"] = "rw"
        gdf = gpd.read_file(file_path, driver="KML")
    else:
        gdf = gpd.read_file(file_path)

    return gdf



row1_col1, row1_col2 = st.columns([3, 1])

# NLCD MAP ---------------------------------------------------------------------------------------------------

with row1_col1:

    year = st.selectbox('Select a Year to View', ('2001', '2004', '2006', '2008', '2011', '2013', '2016', '2019'))

    Map1 = geemap.Map(  
                basemap="HYBRID",
                plugin_Draw=True,
                Draw_export=True,
                locate_control=True,
                plugin_LatLngPopup=False
    )
            

    dataset = ee.ImageCollection(f'USGS/NLCD_RELEASES/2019_REL/NLCD')

    nlcd = dataset.filter(ee.Filter.eq('system:index', f'{year}')).first()


    landcover = nlcd.select('landcover')

    Map1.setCenter(-95, 38, 4)
    Map1.add_legend(builtin_legend="NLCD")

    Map1.addLayer(landcover, None, 'Landcover')

    # FILE UPLOAD ------------------------------------------------------
    data = st.file_uploader("Upload a .geojson file", type=["geojson"])

    # GEOMETRY APPLIED -------------------------------------------------

    if data is None:
        with row1_col2:
            st.info(
                    "Draw a rectangle on the map -> Export it as a GeoJSON -> Upload it back to the app -> Click Submit button"
                )
    else:
        gdf = uploaded_file_to_gdf(data)
        st.session_state["roi"] = geemap.gdf_to_ee(gdf, geodesic=False)
        Map1.add_gdf(gdf, "ROI")
        Map1.centerObject(st.session_state["roi"], 8)

    Map1.to_streamlit(width=850, height=600)

with row1_col2: 
    
# STATS SELECTION ---------------------------------------------------------------------------------------------------

    with st.form("stats_select"):
        st.write("Select which diagram(s) you would like to view below:")
        histogram = st.checkbox("Histogram")
        pie_chart = st.checkbox("Pie Chart")
        scatter_plot = st.checkbox("Scatter Plot")
        st.write("Note: Year selected above file uploader will be used for the histogram and pie chart")
        st.markdown("""--------------""")
        st.write("Select what years you would like to compare for the scatter plot:")
        year1 = st.selectbox('Year 1', ('2001', '2004', '2006', '2008', '2011', '2013', '2016', '2019'))
        year2 = st.selectbox('Year 2', ('2001', '2004', '2006', '2008', '2011', '2013', '2016', '2019'))

        submit_button = st.form_submit_button("Submit")
    
    if submit_button:
        st.write(f"You selected:") 
        st.write(f"Histogram = *{histogram}*")
        st.write(f"Pie Chart = *{pie_chart}*")
        st.write(f"Scatter Plot Comparison = *{scatter_plot}*")

        logo = "images/legend.jpg"
        st.sidebar.image(logo)

        # HISTOGRAM -------------------------------------------------

        if histogram == True:

            csv = "zonal_stats.csv"
            
            geemap.zonal_stats_by_group(
                landcover,
                st.session_state["roi"],
                csv,
                statistics_type="SUM",
                denominator=1000000,
                scale=1000,
                decimal_places=2,
            )

            gdf_csv = gpd.read_file('zonal_stats.csv')
            transposed_gdf = gdf_csv.T
            zst = transposed_gdf.to_csv('zonal_stats_transposed.csv', index=True, header=True)
            zst = pd.read_csv('zonal_stats_transposed.csv')

            zst = zst.set_index('Unnamed: 0') # set the index to the first column
            zst = zst.drop('Class_sum', axis=0) # drop the row that contains 'Class_sum'
            zst = zst.drop('system:index', axis=0) # drop the row that contains 'system:index'
            zst.to_csv('zonal_stats_transposed.csv', index=True, header=True)
            zst = pd.read_csv('zonal_stats_transposed.csv')


            chart1 = geemap.histogram(
                data=zst,
                x='Unnamed: 0',
                y='0',
                x_label="Landcover",
                y_label="Area (km2)",
                descending=True,
                max_rows=15,
                title="Histogram",
                height=500,
                layout_args={'title_x': 0.5, 'title_y': 0.9}
            )
            with row1_col1:
                st.plotly_chart(chart1, use_container_width=True)
        
        # PIE CHART -------------------------------------------------

        if pie_chart == True:

            zst = pd.read_csv('zonal_stats_transposed.csv')

            chart2 = geemap.pie_chart(
                data=zst,
                names='Unnamed: 0',
                values='0',
                title="Pie Chart",
                legend_title="Landcover",
                height=500,
                layout_args={'title_x': 0.5, 'title_y': 0.9}
            )
            with row1_col1:
                st.plotly_chart(chart2, use_container_width=True)
        
        # SCATTER PLOT ----------------------------------------------

        if scatter_plot == True:

            nlcd2 = dataset.filter(ee.Filter.eq('system:index', f'{year1}')).first()
            landcover2 = nlcd2.select('landcover')
        
            nlcd3 = dataset.filter(ee.Filter.eq('system:index', f'{year2}')).first()
            landcover3 = nlcd3.select('landcover')


            year1_csv = "zonal_stats_year1.csv"
            year2_csv = "zonal_stats_year2.csv"

            geemap.zonal_stats_by_group(landcover2, st.session_state["roi"], year1_csv, statistics_type='SUM', denominator=1000000, scale=1000)
            geemap.zonal_stats_by_group(landcover3, st.session_state["roi"], year2_csv, statistics_type='SUM', denominator=1000000, scale=1000)
            
            
            # TRANSPOSE THE CSV FILES --------------------------------------------

            gdf_csv = gpd.read_file(year1_csv)
            transposed_gdf = gdf_csv.T
            zst1 = transposed_gdf.to_csv('year1_transposed.csv', index=True, header=True)
            zst1 = pd.read_csv('year1_transposed.csv')
            zst1 = zst1.set_index('Unnamed: 0') # set the index to the first column
            zst1 = zst1.drop('Class_sum', axis=0) # drop the row that contains 'Class_sum'
            zst1 = zst1.drop('system:index', axis=0) # drop the row that contains 'system:index'
            zst1.to_csv('year1_transposed.csv', index=True, header=True)
            zst1 = pd.read_csv('year1_transposed.csv')
            
            gdf_csv = gpd.read_file(year2_csv)
            transposed_gdf = gdf_csv.T
            zst2 = transposed_gdf.to_csv('year2_transposed.csv', index=True, header=True)
            zst2 = pd.read_csv('year2_transposed.csv')
            zst2 = zst2.set_index('Unnamed: 0') # set the index to the first column
            zst2 = zst2.drop('Class_sum', axis=0) # drop the row that contains 'Class_sum'
            zst2 = zst2.drop('system:index', axis=0) # drop the row that contains 'system:index'
            zst2.to_csv('year2_transposed.csv', index=True, header=True)
            zst2 = pd.read_csv('year2_transposed.csv')

            merged_df1 = pd.merge(zst1, zst2, on='Unnamed: 0')
            merged_df_csv = merged_df1.to_csv('merged_df.csv', index=True, header=True)

            # Reshape the dataframe
            merged_df = merged_df1.melt(id_vars=['Unnamed: 0'], var_name='File', value_name='Coverage (km2)')

            # Create a scatter plot to compare the two files
            fig = px.scatter(merged_df, x='Unnamed: 0', y='Coverage (km2)', color='File', 
                            labels={"x": "Landcover", "y": "Coverage (km2)"}, 
                            title="Comparison of Year 1 (0_x) and Year 2 (0_y)", 
                            hover_data=['File', 'Coverage (km2)'])

            # Update the y-axis labels to indicate which file they belong to
            fig.update_yaxes(title_text="Coverage (km2) - File 1", tickprefix="File 1: ")
            fig.update_yaxes(title_text="Coverage (km2) - File 2", tickprefix="File 2: ", side="right")

            with row1_col1:
                st.plotly_chart(fig, use_container_width=True)

            # Form for Percent Gain/Loss --------------------------------------------

with row1_col2:

    with st.form('class_selection'):
        st.write("Pick which landcover class(es) you would like to calculate the percent gain/loss for.")
        Class_11 = st.checkbox("11 - Open Water", value=True)
        Class_12 = st.checkbox("12 - Perennial Ice/Snow", value=True)
        Class_21 = st.checkbox("21 - Developed, Open Space", value=True)
        Class_22 = st.checkbox("22 - Developed, Low Intensity", value=True)
        Class_23 = st.checkbox("23 - Developed, Medium Intensity", value=True)
        Class_24 = st.checkbox("24 - Developed, High Intensity", value=True)
        Class_31 = st.checkbox("31 - Barren Land (Rock/Sand/Clay)", value=True)
        Class_41 = st.checkbox("41 - Deciduous Forest", value=True)
        Class_42 = st.checkbox("42 - Evergreen Forest", value=True)
        Class_43 = st.checkbox("43 - Mixed Forest", value=True)
        Class_51 = st.checkbox("51 - Dwarf Scrub", value=True)
        Class_52 = st.checkbox("52 - Shrub/Scrub", value=True)
        Class_71 = st.checkbox("71 - Grassland/Herbaceous", value=True)
        Class_72 = st.checkbox("72 - Sedge/Herbaceous", value=True)
        Class_73 = st.checkbox("73 - Lichens", value=True)
        Class_74 = st.checkbox("74 - Moss", value=True)
        Class_81 = st.checkbox("81 - Pasture/Hay", value=True)
        Class_82 = st.checkbox("82 - Cultivated Crops", value=True)
        Class_90 = st.checkbox("90 - Woody Wetlands", value=True)
        Class_95 = st.checkbox("95 - Emergent Herbaceous Wetlands", value=True)

        submit_button2 = st.form_submit_button("Submit Selection")

    if submit_button2:
        def calculate_percent_gain_loss(class_number):
            calc = pd.read_csv('merged_df.csv')
            calc['Percent Gain/Loss'] = (calc['0_y'] - calc['0_x']) / calc['0_x'] * 100
            try:
                percent_gain_loss = calc.loc[calc['Unnamed: 0']== class_number, 'Percent Gain/Loss'].values[0]
                if percent_gain_loss is not None:
                    if percent_gain_loss > 0:
                        st.write(f"🔺 {percent_gain_loss:.2f}%")
                    elif percent_gain_loss < 0:
                        st.write(f"🔻 {percent_gain_loss:.2f}%")
                    else:
                        st.write(f"{percent_gain_loss:.2f}%")
                else:
                    st.write(f"No data found for class {class_number}")
            except KeyError:
                st.write(f"No data found for class {class_number}")
            except IndexError:
                st.write(f"No data found for class {class_number}")


        with row1_col1:
            if Class_11 == True:
                st.write("11 - Open Water")
                class_number = 'Class_11'
                calculate_percent_gain_loss(class_number)



            if Class_12 == True:
                st.write("12 - Perennial Ice/Snow")
                class_number = 'Class_12'
                calculate_percent_gain_loss(class_number)




            if Class_21 == True:
                st.write("21 - Developed, Open Space")
                class_number = 'Class_21'
                calculate_percent_gain_loss(class_number)




            if Class_22 == True:
                st.write("22 - Developed, Low Intensity")
                class_number = 'Class_22'
                calculate_percent_gain_loss(class_number)




            if Class_23 == True:
                st.write("23 - Developed, Medium Intensity")
                class_number = 'Class_23'
                calculate_percent_gain_loss(class_number)




            if Class_24 == True:
                st.write("24 - Developed, High Intensity")
                class_number = 'Class_24'
                calculate_percent_gain_loss(class_number)




            if Class_31 == True:
                st.write("31 - Barren Land (Rock/Sand/Clay)")
                class_number = 'Class_31'
                calculate_percent_gain_loss(class_number)




            if Class_41 == True:
                st.write("41 - Deciduous Forest")
                class_number = 'Class_41'
                calculate_percent_gain_loss(class_number)




            if Class_42 == True:
                st.write("42 - Evergreen Forest")
                class_number = 'Class_42'
                calculate_percent_gain_loss(class_number)




            if Class_43 == True:
                st.write("43 - Mixed Forest")
                class_number = 'Class_43'
                calculate_percent_gain_loss(class_number)



            if Class_51 == True:
                st.write("51 - Dwarf Scrub")
                class_number = 'Class_51'
                calculate_percent_gain_loss(class_number)




            if Class_52 == True:
                st.write("52 - Shrub/Scrub")
                class_number = 'Class_52'
                calculate_percent_gain_loss(class_number)




            if Class_71 == True:
                st.write("71 - Grassland/Herbaceous")
                class_number = 'Class_71'
                calculate_percent_gain_loss(class_number)




            if Class_72 == True:
                st.write("72 - Sedge/Herbaceous")
                class_number = 'Class_72'
                calculate_percent_gain_loss(class_number)




            if Class_73 == True:
                st.write("73 - Lichens")
                class_number = 'Class_73'
                calculate_percent_gain_loss(class_number)




            if Class_74 == True:
                st.write("74 - Moss")
                class_number = 'Class_74'
                calculate_percent_gain_loss(class_number)




            if Class_81 == True:
                st.write("81 - Pasture/Hay")
                class_number = 'Class_81'
                calculate_percent_gain_loss(class_number)




            if Class_82 == True:
                st.write("82 - Cultivated Crops")
                class_number = 'Class_82'
                calculate_percent_gain_loss(class_number)




            if Class_90 == True:
                st.write("90 - Woody Wetlands")
                class_number = 'Class_90'
                calculate_percent_gain_loss(class_number)




            if Class_95 == True:
                st.write("95 - Emergent Herbaceous Wetlands")
                class_number = 'Class_95'
                calculate_percent_gain_loss(class_number)
