import sys
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton,
    QFileDialog, QLabel, QTextEdit, QComboBox
)

class EpiGISApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Epidemiological GIS Tool (Kenya)")
        self.setGeometry(100, 100, 750, 650)

        self.data = None
        self.geo = None
        self.results = {}

        layout = QVBoxLayout()

        # Load CSV
        self.load_csv_btn = QPushButton("Load Dataset (CSV)")
        self.load_csv_btn.clicked.connect(self.load_csv)
        layout.addWidget(self.load_csv_btn)

        # Load GeoJSON
        self.load_geo_btn = QPushButton("Load Kenya GeoJSON")
        self.load_geo_btn.clicked.connect(self.load_geo)
        layout.addWidget(self.load_geo_btn)

        # Column selectors
        self.exposure_label = QLabel("Select Exposure Column (Binary):")
        layout.addWidget(self.exposure_label)
        self.exposure_box = QComboBox()
        layout.addWidget(self.exposure_box)

        self.outcome_label = QLabel("Select Outcome Column (Binary):")
        layout.addWidget(self.outcome_label)
        self.outcome_box = QComboBox()
        layout.addWidget(self.outcome_box)

        self.county_label = QLabel("Select County Column (for mapping):")
        layout.addWidget(self.county_label)
        self.county_box = QComboBox()
        layout.addWidget(self.county_box)

        # Analysis buttons
        self.summary_btn = QPushButton("Summary Statistics")
        self.summary_btn.clicked.connect(self.summary_stats)
        layout.addWidget(self.summary_btn)

        self.analysis_btn = QPushButton("Run Epidemiological Analysis (OR/RR)")
        self.analysis_btn.clicked.connect(self.run_analysis)
        layout.addWidget(self.analysis_btn)

        self.map_btn = QPushButton("Generate GIS Disease Map")
        self.map_btn.clicked.connect(self.generate_map)
        layout.addWidget(self.map_btn)

        # Output panel
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        layout.addWidget(self.output)

        self.setLayout(layout)

    # -----------------------------
    # Load CSV dataset
    # -----------------------------
    def load_csv(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select CSV Dataset", "", "CSV Files (*.csv)")
        if file_path:
            try:
                self.data = pd.read_csv(file_path)
                self.output.setText(f"Loaded CSV ({len(self.data)} rows):\n{self.data.head()}")

                # Populate combo boxes
                self.exposure_box.clear()
                self.exposure_box.addItems(self.data.columns)
                self.outcome_box.clear()
                self.outcome_box.addItems(self.data.columns)
                self.county_box.clear()
                self.county_box.addItems(self.data.columns)
            except Exception as e:
                self.output.setText(f"CSV Load Error: {e}")

    # -----------------------------
    # Load Kenya GeoJSON shapefile
    # -----------------------------
    def load_geo(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Kenya Counties GeoJSON", "", "GeoJSON Files (*.geojson)")
        if file_path:
            try:
                self.geo = gpd.read_file(file_path)
                self.output.setText(f"Loaded GeoJSON with {len(self.geo)} counties:\n{self.geo.head()}")
            except Exception as e:
                self.output.setText(f"GeoJSON Load Error: {e}")

    # -----------------------------
    # Summary statistics
    # -----------------------------
    def summary_stats(self):
        if self.data is not None:
            desc = self.data.describe(include='all').transpose()
            self.output.setText(str(desc))
        else:
            self.output.setText("Load a CSV dataset first.")

    # -----------------------------
    # Epidemiological analysis (OR / RR)
    # -----------------------------
    def run_analysis(self):
        if self.data is None:
            self.output.setText("Load CSV first.")
            return

        exposure_col = self.exposure_box.currentText()
        outcome_col = self.outcome_box.currentText()

        try:
            table = pd.crosstab(self.data[exposure_col], self.data[outcome_col])

            if table.shape == (2,2):
                a = table.iloc[1,1]
                b = table.iloc[1,0]
                c = table.iloc[0,1]
                d = table.iloc[0,0]

                or_value = (a*d)/(b*c)
                rr_value = (a/(a+b)) / (c/(c+d))
            else:
                or_value = rr_value = "N/A"

            incidence = self.data[outcome_col].mean()
            prevalence = incidence  # simple cross-sectional

            result_text = f"""
2x2 Table:
{table}

Odds Ratio (OR): {or_value}
Relative Risk (RR): {rr_value}
Incidence: {incidence:.4f}
Prevalence: {prevalence:.4f}
"""
            self.output.setText(result_text)
            self.results = {
                "OR": or_value,
                "RR": rr_value,
                "Incidence": incidence,
                "Prevalence": prevalence
            }

        except Exception as e:
            self.output.setText(f"Error in analysis: {e}")

    # -----------------------------
    # GIS mapping
    # -----------------------------
    def generate_map(self):
        if self.data is None or self.geo is None:
            self.output.setText("Load both CSV dataset and Kenya GeoJSON first.")
            return

        county_col = self.county_box.currentText()
        outcome_col = self.outcome_box.currentText()

        try:
            # Aggregate disease by county
            agg = self.data.groupby(county_col)[outcome_col].mean().reset_index()
            agg.columns = ["County", "DiseaseRate"]

            # Clean names for merging
            self.geo['County'] = self.geo['County'].str.strip()
            agg['County'] = agg['County'].str.strip()

            # Merge
            merged = self.geo.merge(agg, on="County", how="left")

            # Plot choropleth
            merged.plot(
                column="DiseaseRate",
                cmap="Reds",
                legend=True,
                missing_kwds={"color": "lightgrey", "label": "No data"},
                edgecolor="black"
            )
            plt.title("Disease Distribution by County")
            plt.show()

        except Exception as e:
            self.output.setText(f"GIS Error: {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = EpiGISApp()
    window.show()
    sys.exit(app.exec())