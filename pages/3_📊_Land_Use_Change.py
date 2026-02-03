import streamlit as st
import ee
import leafmap
import leafmap.foliumap as foliumap
import folium

import pandas as pd
import json
import os
import tempfile
import plotly.express as px
from google.oauth2.credentials import Credentials as UserCredentials

# =============================================================================
# EE AUTH
# =============================================================================
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

# =============================================================================
# PAGE CONFIG
# =============================================================================
st.set_page_config(layout="wide")

# =============================================================================
# NLCD LABELS + COLORS (compact legend)
# =============================================================================
NLCD_CLASSES = {
    "Class_11": "11 - Open Water",
    "Class_12": "12 - Perennial Ice/Snow",
    "Class_21": "21 - Developed, Open Space",
    "Class_22": "22 - Developed, Low Intensity",
    "Class_23": "23 - Developed, Medium Intensity",
    "Class_24": "24 - Developed, High Intensity",
    "Class_31": "31 - Barren Land (Rock/Sand/Clay)",
    "Class_41": "41 - Deciduous Forest",
    "Class_42": "42 - Evergreen Forest",
    "Class_43": "43 - Mixed Forest",
    "Class_51": "51 - Dwarf Scrub",
    "Class_52": "52 - Shrub/Scrub",
    "Class_71": "71 - Grassland/Herbaceous",
    "Class_72": "72 - Sedge/Herbaceous",
    "Class_73": "73 - Lichens",
    "Class_74": "74 - Moss",
    "Class_81": "81 - Pasture/Hay",
    "Class_82": "82 - Cultivated Crops",
    "Class_90": "90 - Woody Wetlands",
    "Class_95": "95 - Emergent Herbaceous Wetlands",
}

# NLCD class colors as hex (no '#'), used for palette + compact legend
NLCD_COLORS = {
    11: ("Open Water", "466B9F"),
    12: ("Perennial Ice/Snow", "D1DEF8"),
    21: ("Developed, Open Space", "DEC5C5"),
    22: ("Developed, Low Intensity", "D99282"),
    23: ("Developed, Medium Intensity", "EB0000"),
    24: ("Developed, High Intensity", "AB0000"),
    31: ("Barren Land", "B3AC9F"),
    41: ("Deciduous Forest", "68AB5F"),
    42: ("Evergreen Forest", "1C5F2C"),
    43: ("Mixed Forest", "B5C58F"),
    51: ("Dwarf Scrub", "AF963C"),
    52: ("Shrub/Scrub", "CCB879"),
    71: ("Grassland/Herbaceous", "DFDFC2"),
    72: ("Sedge/Herbaceous", "D1D182"),
    73: ("Lichens", "A3CC51"),
    74: ("Moss", "82BA9E"),
    81: ("Pasture/Hay", "DCD939"),
    82: ("Cultivated Crops", "AB6C28"),
    90: ("Woody Wetlands", "B8D9EB"),
    95: ("Emergent Herbaceous Wetlands", "6C9FB8"),
}

YEARS = ("2001", "2004", "2006", "2008", "2011", "2013", "2016", "2019")

# =============================================================================
# HELPERS
# =============================================================================
def geojson_upload_to_ee_geometry(uploaded_file):
    """Convert uploaded GeoJSON (Geometry/Feature/FeatureCollection) to ee.Geometry."""
    data = json.loads(uploaded_file.getvalue().decode("utf-8"))

    if isinstance(data, dict) and "type" in data:
        if data["type"] in (
            "Polygon", "MultiPolygon", "Point", "MultiPoint",
            "LineString", "MultiLineString"
        ):
            return ee.Geometry(data)

        if data["type"] == "Feature":
            geom = data.get("geometry")
            return ee.Geometry(geom) if geom else None

        if data["type"] == "FeatureCollection":
            feats = data.get("features", [])
            geoms = [f.get("geometry") for f in feats if f.get("geometry")]

            if not geoms:
                return None

            # If multiple geometries, union them into one geometry (robust)
            ee_geoms = [ee.Geometry(g) for g in geoms]
            merged = ee.Geometry(ee_geoms[0])
            for g in ee_geoms[1:]:
                merged = merged.union(g, maxError=1)
            return merged

    return None


def st_draw_to_ee_geometry(draw_output):
    """Convert leafmap draw output to ee.Geometry."""
    if not draw_output:
        return None

    if isinstance(draw_output, str):
        try:
            draw_output = json.loads(draw_output)
        except Exception:
            return None

    if isinstance(draw_output, dict):
        if draw_output.get("type") == "Feature":
            geom = draw_output.get("geometry")
            return ee.Geometry(geom) if geom else None

        if draw_output.get("type") in ("Polygon", "MultiPolygon", "Point", "LineString", "MultiLineString"):
            return ee.Geometry(draw_output)

        geom = draw_output.get("geometry")
        if geom:
            return ee.Geometry(geom)

    return None


def add_compact_nlcd_legend(m: foliumap.Map, year: str):
    """Inject a small, scrollable NLCD legend into a folium/leafmap map."""
    class_values = list(NLCD_COLORS.keys())

    rows = "".join(
        f"""
        <div style="display:flex; align-items:center; gap:6px; margin:2px 0;">
          <span style="width:12px; height:12px; background:#{NLCD_COLORS[v][1]}; display:inline-block; border:1px solid #333;"></span>
          <span>{v} — {NLCD_COLORS[v][0]}</span>
        </div>
        """
        for v in class_values
    )

    html = f"""
    <div style="
      position: fixed;
      bottom: 18px; left: 18px;
      z-index: 9999;
      background: rgba(255,255,255,0.92);
      padding: 8px 10px;
      border-radius: 8px;
      font-size: 12px;
      line-height: 1.1;
      max-height: 220px;
      overflow-y: auto;
      box-shadow: 0 2px 8px rgba(0,0,0,0.25);
    ">
      <div style="font-weight:700; margin-bottom:6px;">NLCD {year}</div>
      {rows}
    </div>
    """
    m.get_root().html.add_child(folium.Element(html))


def zonal_stats_landcover_km2(landcover_img: ee.Image, roi: ee.Geometry, scale=30):
    """
    leafmap.zonal_stats_by_group -> tidy DataFrame:
      class_key, class_label, area_km2
    """
    tmp_csv = os.path.join(tempfile.gettempdir(), f"zonal_{next(tempfile._get_candidate_names())}.csv")

    leafmap.zonal_stats_by_group(
        landcover_img,
        roi,
        tmp_csv,
        statistics_type="SUM",
        denominator=1_000_000,  # m² -> km²
        scale=scale,
        decimal_places=3,
    )

    df = pd.read_csv(tmp_csv)
    if df.empty:
        return pd.DataFrame(columns=["class_key", "class_label", "area_km2"])

    row = df.iloc[0].to_dict()
    items = []
    for k, v in row.items():
        if isinstance(k, str) and k.startswith("Class_") and k != "Class_sum":
            if v is None:
                continue
            items.append((k, NLCD_CLASSES.get(k, k), float(v)))

    out = pd.DataFrame(items, columns=["class_key", "class_label", "area_km2"])
    out = out.sort_values("area_km2", ascending=False).reset_index(drop=True)
    return out


# =============================================================================
# EE DATASET (analytics + display)
# =============================================================================
dataset = ee.ImageCollection("USGS/NLCD_RELEASES/2019_REL/NLCD")

def ee_landcover_for_year(y: str) -> ee.Image:
    img = dataset.filter(ee.Filter.eq("system:index", y)).first()
    return ee.Image(img).select("landcover")


def nlcd_display_layer_for_year(y: str):
    """
    Build a discrete-color EE layer that will ALWAYS display properly in folium,
    independent of leafmap version, by remapping NLCD class values to 0..N-1.
    """
    landcover = ee_landcover_for_year(y)
    class_values = list(NLCD_COLORS.keys())
    palette = [NLCD_COLORS[v][1] for v in class_values]

    remapped = landcover.remap(class_values, list(range(len(class_values)))).rename("nlcd")
    vis = {"min": 0, "max": len(class_values) - 1, "palette": palette}
    return remapped, vis


# =============================================================================
# LAYOUT
# =============================================================================
row1_col1, row1_col2 = st.columns([3, 1])

with row1_col1:
    st.title("Land Use Change in the United States")
    st.write("- View NLCD land cover by year (2001–2019).")
    st.write("- Draw an ROI on the map OR upload a GeoJSON ROI.")
    st.write("- Generate a histogram, pie chart, scatter comparison, and percent gain/loss.")

    year = st.selectbox("Select a Year to View", YEARS, index=0)

    st.subheader("ROI Selection")
    data = st.file_uploader("Upload a .geojson ROI (optional)", type=["geojson"])

    # One and only one draw toolbar to prevent duplicates
    m = foliumap.Map(
        basemap="HYBRID",
        center=[38, -95],
        zoom=4,
        draw_control=True,
        measure_control=False,
        locate_control=True,
        scale_control=False,
        fullscreen_control=False,
    )

    # NLCD display (robust)
    nlcd_img, nlcd_vis = nlcd_display_layer_for_year(year)
    m.add_ee_layer(ee_object=nlcd_img, vis_params=nlcd_vis, name=f"NLCD {year}")

    # Small legend (robust)
    add_compact_nlcd_legend(m, year)

    # Render map, capture draw output
    st_map = m.to_streamlit(width=850, height=600)
    try:
        drawn = m.st_last_draw(st_map)
    except Exception:
        drawn = None

    # Resolve ROI: uploaded GeoJSON > drawn geometry
    roi = None
    roi_source = None

    if data is not None:
        roi = geojson_upload_to_ee_geometry(data)
        roi_source = "uploaded GeoJSON"
    else:
        roi = st_draw_to_ee_geometry(drawn)
        roi_source = "drawn geometry" if roi else None

    if roi:
        st.success(f"ROI ready ({roi_source}).")
        st.session_state["roi"] = roi
    else:
        st.info("Draw a polygon/rectangle on the map OR upload a GeoJSON ROI to enable stats.")
        st.session_state.pop("roi", None)


# ---------------- Stats selection ----------------
with row1_col2:
    with st.form("stats_select"):
        st.header("Check the Stats!")
        histogram = st.checkbox("Histogram")
        pie_chart = st.checkbox("Pie Chart")
        scatter_plot = st.checkbox("Scatter Plot")

        st.write("Note: The selected year above is used for Histogram/Pie.")
        st.markdown("---")

        st.write("Scatter Plot Years:")
        year1 = st.selectbox("Year 1", YEARS, index=0)
        year2 = st.selectbox("Year 2", YEARS, index=len(YEARS) - 1)

        submit_button = st.form_submit_button("Submit")


# =============================================================================
# STATS EXECUTION
# =============================================================================
if submit_button:
    if "roi" not in st.session_state:
        st.warning("No ROI selected yet. Draw/upload an ROI first.")
    else:
        roi = st.session_state["roi"]

        # Histogram + Pie use selected year
        landcover = ee_landcover_for_year(year)

        if histogram:
            df_stats = zonal_stats_landcover_km2(landcover, roi, scale=30)
            st.session_state["df_stats_year"] = df_stats

            fig = px.bar(
                df_stats.head(15),
                x="class_label",
                y="area_km2",
                title=f"NLCD Area by Class ({year})",
                labels={"class_label": "Landcover", "area_km2": "Area (km²)"},
            )
            fig.update_layout(title_x=0.5)
            with row1_col1:
                st.plotly_chart(fig, use_container_width=True)

        if pie_chart:
            df_stats = st.session_state.get("df_stats_year")
            if df_stats is None:
                df_stats = zonal_stats_landcover_km2(landcover, roi, scale=30)
                st.session_state["df_stats_year"] = df_stats

            fig = px.pie(
                df_stats,
                names="class_label",
                values="area_km2",
                title=f"NLCD Composition ({year})",
            )
            fig.update_layout(title_x=0.5)
            with row1_col1:
                st.plotly_chart(fig, use_container_width=True)

        if scatter_plot:
            lc1 = ee_landcover_for_year(year1)
            lc2 = ee_landcover_for_year(year2)

            df1 = zonal_stats_landcover_km2(lc1, roi, scale=30).rename(columns={"area_km2": "area_km2_y1"})
            df2 = zonal_stats_landcover_km2(lc2, roi, scale=30).rename(columns={"area_km2": "area_km2_y2"})

            compare = pd.merge(df1, df2, on=["class_key", "class_label"], how="outer").fillna(0.0)
            st.session_state["compare_df"] = compare
            st.session_state["compare_years"] = (year1, year2)

            melted = compare.melt(
                id_vars=["class_label", "class_key"],
                value_vars=["area_km2_y1", "area_km2_y2"],
                var_name="Year",
                value_name="Coverage (km²)",
            )
            melted["Year"] = melted["Year"].map({"area_km2_y1": year1, "area_km2_y2": year2})

            fig = px.scatter(
                melted,
                x="class_label",
                y="Coverage (km²)",
                color="Year",
                title=f"Landcover Comparison: {year1} vs {year2}",
                hover_data=["class_key", "Coverage (km²)"],
            )
            fig.update_layout(title_x=0.5)
            with row1_col1:
                st.plotly_chart(fig, use_container_width=True)


# =============================================================================
# PERCENT GAIN/LOSS
# =============================================================================
with row1_col2:
    with st.form("class_selection"):
        st.header("Percent Gain/Loss")
        st.write("Pick which classes to compute percent gain/loss for (requires Scatter Plot run).")
        checks = {k: st.checkbox(v, value=True) for k, v in NLCD_CLASSES.items()}
        submit_button2 = st.form_submit_button("Submit Selection")

if submit_button2:
    compare = st.session_state.get("compare_df")
    years_pair = st.session_state.get("compare_years")

    if compare is None or years_pair is None:
        st.warning("Run the Scatter Plot comparison first (it generates the year1/year2 table).")
    else:
        y1, y2 = years_pair
        compare = compare.copy()

        compare["pct_change"] = compare.apply(
            lambda r: ((r["area_km2_y2"] - r["area_km2_y1"]) / r["area_km2_y1"] * 100.0)
            if r["area_km2_y1"] > 0 else None,
            axis=1,
        )

        with row1_col1:
            st.subheader(f"Percent Gain/Loss ({y1} → {y2})")

            for class_key, enabled in checks.items():
                if not enabled:
                    continue

                row = compare.loc[compare["class_key"] == class_key]
                label = NLCD_CLASSES.get(class_key, class_key)

                if row.empty:
                    st.write(f"{label}: No data")
                    continue

                pct = row["pct_change"].values[0]
                a1 = row["area_km2_y1"].values[0]
                a2 = row["area_km2_y2"].values[0]

                if pct is None:
                    st.write(f"{label}: baseline is 0 km² in {y1} (cannot compute %). ({a1:.3f} → {a2:.3f} km²)")
                elif pct > 0:
                    st.write(f"🔺 {label}: {pct:.2f}% ({a1:.3f} → {a2:.3f} km²)")
                elif pct < 0:
                    st.write(f"🔻 {label}: {pct:.2f}% ({a1:.3f} → {a2:.3f} km²)")
                else:
                    st.write(f"{label}: {pct:.2f}% ({a1:.3f} → {a2:.3f} km²)")
