"""Interactive Shiny dashboard for the MIMIC-III microbiology alert system.

This module mirrors the class-based structure used in the food-emissions app so
the portfolio demonstrates a consistent object-oriented design approach across
projects.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from shiny import App, reactive, render, ui


# ── Severity helpers ──────────────────────────────────────────────────────────

def severity_to_rag(s: float) -> str:
    """Map a numeric severity score to the dashboard RAG colour scale."""
    if s >= 30:
        return "#e74c3c"
    if s >= 15:
        return "#f39c12"
    return "#27ae60"

def get_risk_label(s: float) -> str:
    """Map a numeric severity score to a labelled risk band."""
    if s >= 30:
        return "HIGH"
    if s >= 15:
        return "MEDIUM"
    return "LOW"


# ── Data loading ──────────────────────────────────────────────────────────────

class DatasetLoader(ABC):
    """Abstract interface for loading dashboard input data."""

    @abstractmethod
    def load(self) -> pd.DataFrame:
        """Return a dataframe for a concrete data source."""
        raise NotImplementedError


class CsvLoader(DatasetLoader):
    """Load a CSV file from disk."""

    def __init__(self, path: Path):
        self.path = path

    def load(self) -> pd.DataFrame:
        """Read the CSV input and fail early if the file is missing."""
        if not self.path.exists():
            raise FileNotFoundError(f"Missing dataset: {self.path}")
        return pd.read_csv(self.path)


class MimicRepository:
    """Repository wrapper around alert dataset access."""

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir

    def load_alerts(self) -> pd.DataFrame:
        """Return the precomputed microbiology alert table."""
        return CsvLoader(self.data_dir / "microalerts.csv").load()


# ── Analysis ──────────────────────────────────────────────────────────────────

class AlertsAnalyzer:
    """Prepare alert metrics and filtered views for the dashboard."""

    def __init__(self, df: pd.DataFrame):
        """Store the cleaned alert table used across all outputs."""
        self.df = self._prepare(df)

    def _prepare(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize types and derive display fields consumed by the UI."""
        out = df.copy()
        out["START_TIME"] = pd.to_datetime(out["START_TIME"])
        out["WARD_LABEL"] = "Ward " + out["WARD_ID"].astype(str)
        out["RISK"] = out["SEVERITY"].apply(get_risk_label)
        out["RAG_COLOR"] = out["SEVERITY"].apply(severity_to_rag)
        return out.sort_values("START_TIME").reset_index(drop=True)

    def summary_metrics(self) -> dict[str, str]:
        """Return headline metrics for the dashboard header."""
        return {
            "Total alerts": str(len(self.df)),
            "Wards affected": str(self.df["WARD_ID"].nunique()),
            "Pathogens detected": str(self.df["ORG_NAME"].nunique()),
            "High-risk alerts": str((self.df["RISK"] == "HIGH").sum()),
        }

    def alerts_by_ward(self) -> pd.DataFrame:
        """Count alerts per ward for the ward ranking chart."""
        return (
            self.df.groupby("WARD_LABEL", as_index=False)
            .size().rename(columns={"size": "Count"})
            .sort_values("Count", ascending=False)
        )

    def alerts_by_pathogen(self, top_n: int = 10) -> pd.DataFrame:
        """Count alerts per pathogen and keep the requested top segment."""
        return (
            self.df.groupby("ORG_NAME", as_index=False)
            .size().rename(columns={"size": "Count"})
            .sort_values("Count", ascending=False)
            .head(top_n)
        )

    def severity_distribution(self) -> pd.DataFrame:
        """Summarise alerts by categorical risk level."""
        return self.df.groupby("RISK", as_index=False).size().rename(columns={"size": "Count"})

    def timeline(self, ward: str) -> pd.DataFrame:
        """Return the alert timeline for all wards or one selected ward."""
        df = self.df if ward == "All" else self.df[self.df["WARD_LABEL"] == ward]
        return df.groupby(["START_TIME", "WARD_LABEL"], as_index=False)["ALERT_ID"].count().rename(columns={"ALERT_ID": "Alerts"})

    def ward_pathogen_heatmap(self) -> pd.DataFrame:
        """Return ward-pathogen counts for the heatmap."""
        return self.df.groupby(["WARD_LABEL", "ORG_NAME"], as_index=False).size().rename(columns={"size": "Count"})

    def wards(self) -> list[str]:
        """Return the ordered ward choices used by the filter control."""
        return ["All"] + sorted(self.df["WARD_LABEL"].unique().tolist())


# ── Visualiser ────────────────────────────────────────────────────────────────

class DashboardVisualizer:
    """Convert prepared alert summaries into Plotly figures."""

    RAG_MAP = {"HIGH": "#e74c3c", "MEDIUM": "#f39c12", "LOW": "#27ae60"}

    def to_html(self, fig: go.Figure) -> str:
        """Serialize a Plotly figure for embedding in a Shiny UI output."""
        return pio.to_html(fig, include_plotlyjs="cdn", full_html=False)

    def alerts_by_ward(self, data: pd.DataFrame) -> go.Figure:
        """Build the ward-level alert count chart."""
        return px.bar(
            data, x="WARD_LABEL", y="Count",
            title="Total alerts per ward",
            labels={"WARD_LABEL": "Ward"},
            color="Count", color_continuous_scale="Reds",
        )

    def alerts_by_pathogen(self, data: pd.DataFrame) -> go.Figure:
        """Build the ranked pathogen count chart."""
        return px.bar(
            data.sort_values("Count"),
            x="Count", y="ORG_NAME", orientation="h",
            title="Top pathogens by alert count",
            labels={"ORG_NAME": "Pathogen"},
            color="Count", color_continuous_scale="Oranges",
        )

    def severity_distribution(self, data: pd.DataFrame) -> go.Figure:
        """Build the severity composition pie chart."""
        order = ["HIGH", "MEDIUM", "LOW"]
        data = data.set_index("RISK").reindex(order).reset_index().dropna()
        return px.pie(
            data, names="RISK", values="Count",
            title="Alert severity distribution",
            color="RISK",
            color_discrete_map=self.RAG_MAP,
        )

    def timeline(self, data: pd.DataFrame) -> go.Figure:
        """Build the time-series chart for alert activity."""
        return px.line(
            data, x="START_TIME", y="Alerts", color="WARD_LABEL",
            markers=True,
            title="Alert timeline by ward",
            labels={"START_TIME": "Date", "WARD_LABEL": "Ward"},
        )

    def heatmap(self, data: pd.DataFrame) -> go.Figure:
        """Build the pathogen-by-ward heatmap."""
        pivot = data.pivot_table(index="ORG_NAME", columns="WARD_LABEL", values="Count", fill_value=0)
        return px.imshow(
            pivot,
            title="Pathogen × Ward alert heatmap",
            color_continuous_scale="YlOrRd",
            labels={"x": "Ward", "y": "Pathogen", "color": "Alerts"},
            aspect="auto",
        )


# ── UI builder ────────────────────────────────────────────────────────────────

class DashboardUI:
    """Build the Shiny page layout and controls."""

    def __init__(self, analyzer: AlertsAnalyzer):
        self.analyzer = analyzer

    def build(self):
        """Create the full dashboard UI from analyzer-derived inputs."""
        metrics = self.analyzer.summary_metrics()
        wards = self.analyzer.wards()

        return ui.page_fluid(
            ui.h1("MIMIC-III Pathogen Alert Dashboard"),
            ui.p(
                "Interactive companion to the OOP hospital alert system project. "
                "Built from microbiology events in the MIMIC-III ICU dataset, this dashboard "
                "visualises pathogen alerts raised by the automated ward monitoring pipeline."
            ),
            ui.layout_columns(
                *[ui.value_box(value=v, title=k, theme="primary") for k, v in metrics.items()],
                col_widths=[3, 3, 3, 3],
            ),
            ui.hr(),
            ui.layout_sidebar(
                ui.sidebar(
                    ui.input_select("ward", "Ward filter", choices=wards, selected="All"),
                    ui.input_numeric("top_n", "Top pathogens to show", value=10, min=5, max=18),
                ),
                ui.navset_tab(
                    ui.nav_panel("Alerts by Ward",     ui.output_ui("ward_plot")),
                    ui.nav_panel("Top Pathogens",      ui.output_ui("pathogen_plot")),
                    ui.nav_panel("Severity Split",     ui.output_ui("severity_plot")),
                    ui.nav_panel("Alert Timeline",     ui.output_ui("timeline_plot")),
                    ui.nav_panel("Heatmap",            ui.output_ui("heatmap_plot")),
                    ui.nav_panel("Data Table",         ui.output_data_frame("data_table")),
                ),
            ),
        )


# ── App orchestrator ──────────────────────────────────────────────────────────

class MimicDashboardApp:
    """Compose repository, analysis, visualization, and server logic."""

    def __init__(self):
        """Load the alert dataset and construct the collaborating objects."""
        data_dir = Path(__file__).resolve().parent / "data"
        repo = MimicRepository(data_dir)
        self.analyzer = AlertsAnalyzer(repo.load_alerts())
        self.visualizer = DashboardVisualizer()
        self.ui_builder = DashboardUI(self.analyzer)

    def build_ui(self):
        """Expose the assembled UI for the Shiny app instance."""
        return self.ui_builder.build()

    def build_server(self, input, output, session):
        """Attach reactive outputs for each dashboard tab."""
        @reactive.Calc
        def selected_ward() -> str:
            return input.ward()

        @reactive.Calc
        def top_n() -> int:
            return int(input.top_n())

        @reactive.Calc
        def filtered_df():
            df = self.analyzer.df
            if selected_ward() != "All":
                df = df[df["WARD_LABEL"] == selected_ward()]
            return df

        @output
        @render.ui
        def ward_plot():
            data = self.analyzer.alerts_by_ward()
            if selected_ward() != "All":
                data = data[data["WARD_LABEL"] == selected_ward()]
            return ui.HTML(self.visualizer.to_html(self.visualizer.alerts_by_ward(data)))

        @output
        @render.ui
        def pathogen_plot():
            df = filtered_df()
            data = (
                df.groupby("ORG_NAME", as_index=False)
                .size().rename(columns={"size": "Count"})
                .sort_values("Count", ascending=False)
                .head(top_n())
            )
            return ui.HTML(self.visualizer.to_html(self.visualizer.alerts_by_pathogen(data)))

        @output
        @render.ui
        def severity_plot():
            df = filtered_df()
            data = df.groupby("RISK", as_index=False).size().rename(columns={"size": "Count"})
            return ui.HTML(self.visualizer.to_html(self.visualizer.severity_distribution(data)))

        @output
        @render.ui
        def timeline_plot():
            data = self.analyzer.timeline(selected_ward())
            return ui.HTML(self.visualizer.to_html(self.visualizer.timeline(data)))

        @output
        @render.ui
        def heatmap_plot():
            df = filtered_df()
            data = df.groupby(["WARD_LABEL", "ORG_NAME"], as_index=False).size().rename(columns={"size": "Count"})
            return ui.HTML(self.visualizer.to_html(self.visualizer.heatmap(data)))

        @output
        @render.data_frame
        def data_table():
            cols = ["ALERT_ID", "WARD_LABEL", "ORG_NAME", "NUM_PATIENTS", "SEVERITY", "RISK", "START_TIME", "THRESHOLD"]
            return render.DataGrid(filtered_df()[cols].reset_index(drop=True), width="100%")


dashboard = MimicDashboardApp()
app_ui = dashboard.build_ui()
server = dashboard.build_server
app = App(app_ui, server)
