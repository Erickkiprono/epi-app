import sys
import pandas as pd
import numpy as np
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton,
    QFileDialog, QLabel, QTextEdit, QComboBox
)
import matplotlib.pyplot as plt

class EpiProApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Epidemiological Analysis Pro")
        self.setGeometry(200, 200, 700, 600)

        self.data = None

        layout = QVBoxLayout()

        # Load
        self.load_btn = QPushButton("Load CSV Data")
        self.load_btn.clicked.connect(self.load_data)
        layout.addWidget(self.load_btn)

        # Column selectors
        self.exposure_label = QLabel("Select Exposure Column:")
        layout.addWidget(self.exposure_label)

        self.exposure_box = QComboBox()
        layout.addWidget(self.exposure_box)

        self.outcome_label = QLabel("Select Outcome (Disease) Column:")
        layout.addWidget(self.outcome_label)

        self.outcome_box = QComboBox()
        layout.addWidget(self.outcome_box)

        # Buttons
        self.summary_btn = QPushButton("Summary Statistics")
        self.summary_btn.clicked.connect(self.summary_stats)
        layout.addWidget(self.summary_btn)

        self.analysis_btn = QPushButton("Run Epidemiological Analysis")
        self.analysis_btn.clicked.connect(self.run_analysis)
        layout.addWidget(self.analysis_btn)

        self.plot_btn = QPushButton("Plot Histogram")
        self.plot_btn.clicked.connect(self.plot_data)
        layout.addWidget(self.plot_btn)

        self.export_btn = QPushButton("Export Results to Excel")
        self.export_btn.clicked.connect(self.export_results)
        layout.addWidget(self.export_btn)

        # Output
        self.output = QTextEdit()
        layout.addWidget(self.output)

        self.setLayout(layout)
        self.results = {}

    def load_data(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open CSV", "", "CSV Files (*.csv)")
        if file_path:
            self.data = pd.read_csv(file_path)
            self.output.setText(str(self.data.head()))

            self.exposure_box.clear()
            self.outcome_box.clear()
            self.exposure_box.addItems(self.data.columns)
            self.outcome_box.addItems(self.data.columns)

    def summary_stats(self):
        if self.data is not None:
            self.output.setText(str(self.data.describe()))
        else:
            self.output.setText("Load data first.")

    def run_analysis(self):
        if self.data is None:
            self.output.setText("Load data first.")
            return

        exposure = self.exposure_box.currentText()
        outcome = self.outcome_box.currentText()

        table = pd.crosstab(self.data[exposure], self.data[outcome])

        try:
            a = table.iloc[1,1]
            b = table.iloc[1,0]
            c = table.iloc[0,1]
            d = table.iloc[0,0]

            or_value = (a * d) / (b * c)
            rr = (a / (a + b)) / (c / (c + d))

            incidence = self.data[outcome].mean()
            prevalence = incidence  # if cross-sectional

            result_text = f"""
2x2 Table:
{table}

Odds Ratio (OR): {or_value:.4f}
Relative Risk (RR): {rr:.4f}
Incidence: {incidence:.4f}
Prevalence: {prevalence:.4f}
"""
            self.output.setText(result_text)

            self.results = {
                "OR": or_value,
                "RR": rr,
                "Incidence": incidence,
                "Prevalence": prevalence
            }

        except Exception as e:
            self.output.setText(f"Error: {str(e)}")

    def plot_data(self):
        if self.data is not None:
            self.data.hist()
            plt.show()
        else:
            self.output.setText("Load data first.")

    def export_results(self):
        if not self.results:
            self.output.setText("Run analysis first.")
            return

        file_path, _ = QFileDialog.getSaveFileName(self, "Save File", "", "Excel Files (*.xlsx)")
        if file_path:
            df = pd.DataFrame([self.results])
            df.to_excel(file_path, index=False)
            self.output.setText("Results exported successfully!")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = EpiProApp()
    window.show()
    sys.exit(app.exec())