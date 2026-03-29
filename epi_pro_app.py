import streamlit as st
import pandas as pd
import numpy as np
import geopandas as gpd
import folium
from streamlit_folium import st_folium
from scipy.stats import chi2_contingency
from sklearn.linear_model import LogisticRegression
from lifelines import KaplanMeierFitter, CoxPHFitter
from sklearn.cluster import KMeans
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
import streamlit_authenticator as stauth

# -----------------------------
# AUTHENTICATION
# -----------------------------
names = ["Admin"]
usernames = ["admin"]
passwords = ["1234"]

hashed_pw = stauth.Hasher(passwords).generate()
authenticator = stauth.Authenticate(names, usernames, hashed_pw, "epi_app", "abcdef")

name, auth_status, username = authenticator.login("Login", "main")

if auth_status != True:
    st.warning("Please login")
    st.stop()

# -----------------------------
# APP TITLE
# -----------------------------
st.title("🌍 Advanced Epidemiology & GIS Platform")

# -----------------------------
# FILE UPLOAD
# -----------------------------
csv_file = st.sidebar.file_uploader("Upload CSV", type=["csv"])
geo_file = st.sidebar.file_uploader("Upload GeoJSON", type=["geojson"])

if csv_file:
    data = pd.read_csv(csv_file)
    st.dataframe(data.head())

    cols = data.columns.tolist()

    exposure = st.selectbox("Exposure", cols)
    outcome = st.selectbox("Outcome", cols)

    # -----------------------------
    # 2x2 + Chi-square
    # -----------------------------
    st.subheader("📊 Epidemiological Measures")

    table = pd.crosstab(data[exposure], data[outcome])

    if table.shape == (2,2):
        a, b, c, d = table.iloc[1,1], table.iloc[1,0], table.iloc[0,1], table.iloc[0,0]

        OR = (a*d)/(b*c)
        RR = (a/(a+b)) / (c/(c+d))
        RD = (a/(a+b)) - (c/(c+d))

        chi2, p, _, _ = chi2_contingency(table)

        st.write(table)
        st.write(f"OR: {OR}, RR: {RR}, RD: {RD}")
        st.write(f"Chi-square: {chi2}, p-value: {p}")

    # -----------------------------
    # MULTIVARIABLE REGRESSION
    # -----------------------------
    st.subheader("📊 Multivariable Logistic Regression")

    predictors = st.multiselect("Select predictors", cols)

    if predictors:
        try:
            X = data[predictors]
            y = data[outcome]

            model = LogisticRegression(max_iter=1000)
            model.fit(X, y)

            coef_df = pd.DataFrame({
                "Variable": predictors,
                "Coefficient": model.coef_[0]
            })

            st.dataframe(coef_df)
        except Exception as e:
            st.error(e)

    # -----------------------------
    # SURVIVAL ANALYSIS
    # -----------------------------
    st.subheader("🧬 Survival Analysis")

    time_col = st.selectbox("Time Column", cols)
    event_col = st.selectbox("Event Column (0/1)", cols)

    if st.button("Run Survival Analysis"):
        kmf = KaplanMeierFitter()
        kmf.fit(data[time_col], event_observed=data[event_col])

        km_plot = kmf.plot_survival_function()
        st.pyplot(km_plot.figure)

        # Cox Regression
        try:
            cph = CoxPHFitter()
            df = data[[time_col, event_col] + predictors].dropna()
            cph.fit(df, duration_col=time_col, event_col=event_col)

            st.write("Cox Regression Results")
            st.dataframe(cph.summary)
        except:
            st.warning("Cox model needs numeric predictors")

    # -----------------------------
    # GIS + HEATMAP + CLUSTERING
    # -----------------------------
    st.subheader("🗺️ Spatial Analysis")

    lat_col = st.selectbox("Latitude", cols)
    lon_col = st.selectbox("Longitude", cols)

    if st.button("Generate Map"):
        m = folium.Map(location=[data[lat_col].mean(), data[lon_col].mean()], zoom_start=6)

        # Points
        for _, row in data.iterrows():
            folium.CircleMarker(
                location=[row[lat_col], row[lon_col]],
                radius=4,
                popup=str(row[outcome])
            ).add_to(m)

        # Clustering
        coords = data[[lat_col, lon_col]].dropna()
        kmeans = KMeans(n_clusters=3)
        data['cluster'] = kmeans.fit_predict(coords)

        st.write("Cluster Counts")
        st.write(data['cluster'].value_counts())

        st_folium(m, width=900, height=500)

    # -----------------------------
    # PDF REPORT
    # -----------------------------
    st.subheader("📄 Generate Report")

    if st.button("Generate PDF"):
        doc = SimpleDocTemplate("report.pdf")
        styles = getSampleStyleSheet()

        content = []
        content.append(Paragraph("Epidemiology Report", styles['Title']))
        content.append(Paragraph(f"OR: {OR}, RR: {RR}, RD: {RD}", styles['Normal']))

        doc.build(content)

        with open("report.pdf", "rb") as f:
            st.download_button("Download PDF", f, "report.pdf")

else:
    st.info("Upload a dataset to begin.")