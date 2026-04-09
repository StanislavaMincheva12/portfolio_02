from abc import ABC, abstractmethod
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from pycountry_convert import (
    country_alpha2_to_continent_code,
    country_name_to_country_alpha2,
)
from shiny import App, reactive, render, ui


class DatasetLoader(ABC):
    """Abstract loader for local datasets."""

    @abstractmethod
    def load(self) -> pd.DataFrame:
        """Return a dataframe."""


class CsvLoader(DatasetLoader):
    """Load a CSV file from the app data directory."""

    def __init__(self, file_path: Path):
        self.file_path = file_path

    def load(self) -> pd.DataFrame:
        if not self.file_path.exists():
            raise FileNotFoundError(f"Missing dataset: {self.file_path}")
        return pd.read_csv(self.file_path)


class PortfolioRepository:
    """Provide access to all project datasets."""

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir

    def load_edgar(self) -> pd.DataFrame:
        return CsvLoader(self.data_dir / "EDGARfood.csv").load()

    def load_foods(self) -> pd.DataFrame:
        return CsvLoader(self.data_dir / "Food_Product_Emissions.csv").load()

    def load_gleam(self) -> pd.DataFrame:
        return CsvLoader(self.data_dir / "GLEAM_LivestockEmissions.csv").load()


class EmissionsAnalyzer:
    """Prepare notebook-derived summaries for the dashboard."""

    MANUAL_REGION_MAPPING = {
        "Cote d'Ivoire": "Africa",
        "Korea, Democratic People's Republic": "Asia",
        "Congo, Democratic Republic of the": "Africa",
        "Reunion": "Africa",
        "Serbia and Montenegro": "Europe",
        "Sudan (former)": "Africa",
        "Timor-Leste": "Asia",
        "Wallis and Futuna Islands": "Oceania",
        "Int. Shipping": "Other",
        "Netherlands Antilles": "Caribbean",
        "Saint Helena": "Africa",
        "Western Sahara": "Africa",
        "Int. Aviation": "Other",
    }

    CONTINENTS = {
        "AF": "Africa",
        "AS": "Asia",
        "EU": "Europe",
        "NA": "North America",
        "SA": "South America",
        "OC": "Oceania",
    }

    def __init__(self, edgar: pd.DataFrame, foods: pd.DataFrame, gleam: pd.DataFrame):
        self.edgar = self._prepare_edgar(edgar)
        self.foods = foods.copy()
        self.gleam = gleam.copy()

    def _country_to_region(self, country: str) -> str:
        if country in self.MANUAL_REGION_MAPPING:
            return self.MANUAL_REGION_MAPPING[country]
        try:
            code = country_name_to_country_alpha2(country)
            continent_code = country_alpha2_to_continent_code(code)
            return self.CONTINENTS.get(continent_code, "Other")
        except Exception:
            return "Other"

    def _prepare_edgar(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        filtered = dataframe.copy()
        filtered = filtered.drop_duplicates(keep="first")
        filtered = filtered[filtered["GHG Emissions"] >= 0]
        filtered = filtered[(filtered["Year"] >= 1990) & (filtered["Year"] <= 2015)]
        filtered["Region"] = filtered["Country"].apply(self._country_to_region)
        return filtered

    def global_totals(self) -> pd.DataFrame:
        return self.edgar.groupby("Year", as_index=False)["GHG Emissions"].sum()

    def regional_totals(self) -> pd.DataFrame:
        return self.edgar.groupby(["Year", "Region"], as_index=False)["GHG Emissions"].sum()

    def asia_totals(self) -> pd.DataFrame:
        asia = self.edgar[self.edgar["Region"] == "Asia"]
        return asia.groupby("Year", as_index=False)["GHG Emissions"].sum()

    def top_asia_country_name(self) -> str:
        asia = self.edgar[self.edgar["Region"] == "Asia"]
        grouped = asia.groupby("Country", as_index=False)["GHG Emissions"].sum()
        return grouped.sort_values("GHG Emissions", ascending=False).iloc[0]["Country"]

    def top_country_timeseries(self, region: str) -> pd.DataFrame:
        frame = self.edgar if region == "All" else self.edgar[self.edgar["Region"] == region]
        grouped = frame.groupby(["Country", "Year"], as_index=False)["GHG Emissions"].sum()
        totals = grouped.groupby("Country", as_index=False)["GHG Emissions"].sum()
        top_country = totals.sort_values("GHG Emissions", ascending=False).iloc[0]["Country"]
        result = grouped[grouped["Country"] == top_country].copy()
        result["Top Country"] = top_country
        return result

    def top_foods(self, limit: int = 10) -> pd.DataFrame:
        return self.foods.sort_values(
            "Total from Land to Retail", ascending=False
        ).head(limit)

    def gleam_emission_types(self) -> pd.DataFrame:
        columns = [
            "Total CO2 emissions (kg CO2e)",
            "Total CH4 emissions (kg CO2e)",
            "Total N2O emissions (kg CO2e)",
        ]
        return self.gleam.groupby("Region", as_index=False)[columns].sum()

    def summary_metrics(self) -> dict[str, str]:
        global_totals = self.global_totals()
        asia = self.asia_totals()
        top_food = self.top_foods(1).iloc[0]
        top_country = self.top_asia_country_name()
        return {
            "Global records": f"{len(self.edgar):,}",
            "Peak global year": str(global_totals.loc[global_totals['GHG Emissions'].idxmax(), 'Year']),
            "Peak Asia year": str(asia.loc[asia['GHG Emissions'].idxmax(), 'Year']),
            "Top Asia emitter": top_country,
            "Top food product": str(top_food["Food product"]),
        }


class DashboardVisualizer:
    """Create plotly charts for the app."""

    def to_html(self, figure: go.Figure) -> str:
        return pio.to_html(figure, include_plotlyjs="cdn", full_html=False)

    def global_trend(self, data: pd.DataFrame) -> go.Figure:
        return px.line(
            data,
            x="Year",
            y="GHG Emissions",
            markers=True,
            title="Global food system emissions, 1990-2015",
        )

    def regional_trend(self, data: pd.DataFrame, region: str) -> go.Figure:
        frame = data if region == "All" else data[data["Region"] == region]
        color = None if region != "All" else "Region"
        title = "Food system emissions by region" if region == "All" else f"Food system emissions in {region}"
        return px.line(frame, x="Year", y="GHG Emissions", color=color, markers=True, title=title)

    def top_country_trend(self, data: pd.DataFrame, region: str) -> go.Figure:
        title_country = data["Top Country"].iloc[0]
        title = f"Top emitting country in {region}" if region != "All" else "Top emitting country overall"
        return px.line(
            data,
            x="Year",
            y="GHG Emissions",
            markers=True,
            title=f"{title}: {title_country}",
        )

    def top_foods_bar(self, data: pd.DataFrame) -> go.Figure:
        return px.bar(
            data,
            x="Food product",
            y="Total from Land to Retail",
            title="Top food products by emissions from land to retail",
        )

    def gleam_region_bar(self, data: pd.DataFrame) -> go.Figure:
        melted = data.melt(id_vars="Region", var_name="Emission Type", value_name="Emissions")
        return px.bar(
            melted,
            x="Region",
            y="Emissions",
            color="Emission Type",
            barmode="group",
            title="Livestock emissions by region and gas type",
        )


class DashboardUI:
    """Build the Shiny dashboard UI."""

    def __init__(self, analyzer: EmissionsAnalyzer):
        self.analyzer = analyzer

    def build(self):
        metrics = self.analyzer.summary_metrics()
        regions = ["All"] + sorted(self.analyzer.regional_totals()["Region"].dropna().unique().tolist())
        return ui.page_fluid(
            ui.h1("Food System Emissions Explorer"),
            ui.p(
                "Interactive companion to the DSS portfolio project, built from the EDGAR, food product, and GLEAM datasets used in the notebook analysis."
            ),
            ui.layout_columns(
                *[
                    ui.value_box(value=value, title=label, theme="primary")
                    for label, value in metrics.items()
                ],
                col_widths=[4, 4, 4, 6, 6],
            ),
            ui.hr(),
            ui.layout_sidebar(
                ui.sidebar(
                    ui.input_select("region", "Region", choices=regions, selected="Asia"),
                    ui.input_numeric("food_count", "Top food products", value=10, min=5, max=20),
                ),
                ui.navset_tab(
                    ui.nav_panel("Regional Trend", ui.output_ui("regional_trend_plot")),
                    ui.nav_panel("Top Country", ui.output_ui("top_country_plot")),
                    ui.nav_panel("Food Products", ui.output_ui("top_foods_plot")),
                    ui.nav_panel("GLEAM Overview", ui.output_ui("gleam_plot")),
                    ui.nav_panel("Data Preview", ui.output_data_frame("data_preview")),
                ),
            ),
        )


class EmissionsDashboardApp:
    """Coordinate repository, analysis, UI, and server logic."""

    def __init__(self):
        data_dir = Path(__file__).resolve().parent / "data"
        repository = PortfolioRepository(data_dir)
        self.analyzer = EmissionsAnalyzer(
            repository.load_edgar(),
            repository.load_foods(),
            repository.load_gleam(),
        )
        self.visualizer = DashboardVisualizer()
        self.ui_builder = DashboardUI(self.analyzer)

    def build_ui(self):
        return self.ui_builder.build()

    def build_server(self, input, output, session):
        @reactive.Calc
        def selected_region() -> str:
            return input.region()

        @reactive.Calc
        def food_count() -> int:
            return int(input.food_count())

        @output
        @render.ui
        def regional_trend_plot():
            figure = self.visualizer.regional_trend(self.analyzer.regional_totals(), selected_region())
            return ui.HTML(self.visualizer.to_html(figure))

        @output
        @render.ui
        def top_country_plot():
            figure = self.visualizer.top_country_trend(
                self.analyzer.top_country_timeseries(selected_region()),
                selected_region(),
            )
            return ui.HTML(self.visualizer.to_html(figure))

        @output
        @render.ui
        def top_foods_plot():
            figure = self.visualizer.top_foods_bar(self.analyzer.top_foods(food_count()))
            return ui.HTML(self.visualizer.to_html(figure))

        @output
        @render.ui
        def gleam_plot():
            figure = self.visualizer.gleam_region_bar(self.analyzer.gleam_emission_types())
            return ui.HTML(self.visualizer.to_html(figure))

        @output
        @render.data_frame
        def data_preview():
            preview = self.analyzer.edgar[["Country", "Region", "Year", "GHG", "GHG Emissions"]].head(15)
            return render.DataGrid(preview, width="100%")


dashboard = EmissionsDashboardApp()
app_ui = dashboard.build_ui()
server = dashboard.build_server
app = App(app_ui, server)
