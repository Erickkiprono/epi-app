import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Epidemiology GIS App", layout="wide")

st.title("🌍 Epidemiological Analysis & GIS Dashboard (Kenya)")

# -----------------------------
# Upload Dataset
# -----------------------------
st.sidebar.header("Upload Data")

csv_file = st.sidebar.file_uploader("Upload CSV Dataset", type=["csv"])
geo_file = st.sidebar.file_uploader("Upload Kenya GeoJSON", type=["geojson"])

if csv_file:
    data = pd.read_csv(csv_file)
    st.subheader("Dataset Preview")
    st.dataframe(data.head())

    columns = data.columns.tolist()

    exposure_col = st.selectbox("Select Exposure Column (Binary)", columns)
    outcome_col = st.selectbox("Select Outcome Column (Binary)", columns)
    county_col = st.selectbox("Select County Column", columns)

    # -----------------------------
    # Epidemiological Analysis
    # -----------------------------
    st.subheader("📊 Epidemiological Analysis")

    try:
        table = pd.crosstab(data[exposure_col], data[outcome_col])

        if table.shape == (2,2):
            a = table.iloc[1,1]
            b = table.iloc[1,0]
            c = table.iloc[0,1]
            d = table.iloc[0,0]

            OR = (a*d)/(b*c)
            RR = (a/(a+b)) / (c/(c+d))
        else:
            OR = RR = None

        incidence = data[outcome_col].mean()
        prevalence = incidence

        st.write("### 2x2 Table")
        st.dataframe(table)

        st.metric("Odds Ratio (OR)", OR if OR else "N/A")
        st.metric("Relative Risk (RR)", RR if RR else "N/A")
        st.metric("Incidence", round(incidence,4))
        st.metric("Prevalence", round(prevalence,4))

    except Exception as e:
        st.error(f"Analysis error: {e}")

    # -----------------------------
    # GIS Mapping
    # -----------------------------
    if geo_file:
        st.subheader("🗺️ GIS Disease Map")

        try:
            geo = gpd.read_file(geo_file)

            agg = data.groupby(county_col)[outcome_col].mean().reset_index()
            agg.columns = ["County", "DiseaseRate"]

            geo['County'] = geo['County'].str.strip()
            agg['County'] = agg['County'].str.strip()

            merged = geo.merge(agg, on="County", how="left")

            m = folium.Map(location=[1.0, 37.0], zoom_start=6)

            folium.Choropleth(
                geo_data=merged,
                data=merged,
                columns=["County", "DiseaseRate"],
                key_on="feature.properties.County",
                fill_color="Reds",
                fill_opacity=0.7,
                line_opacity=0.2,
                legend_name="Disease Rate"
            ).add_to(m)

            folium.GeoJson(
                merged,
                tooltip=folium.GeoJsonTooltip(
                    fields=["County", "DiseaseRate"],
                    aliases=["County:", "Disease Rate:"]
                )
            ).add_to(m)

            st_folium(m, width=900, height=500)

        except Exception as e:
            st.error(f"GIS Error: {e}")

else:
    st.info("Upload a CSV dataset to begin.")