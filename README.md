# Stanislava Mincheva Portfolio

Quarto-based personal portfolio site for the CEU Data Science Project course, combining static portfolio pages with embedded Shiny for Python applications deployed on Posit Connect Cloud.

## Live links

- Shiny app: https://connect.posit.cloud/stanislavamincheva12/content/019d6d99-e4ec-3ef6-4076-7c5457291dbb
- MIMIC-III app: https://connect.posit.cloud/stanislavamincheva12/content/019d7c6d-43eb-cc64-b3f7-2de7c0b3ca86
- Quarto website: https://connect.posit.cloud/stanislavamincheva12/content/019d6d9d-c370-b7eb-a12c-18abe1304626

## Assignment fit

This submission is designed to satisfy the portfolio brief in three ways:

- A Quarto website provides the public-facing portfolio shell.
- Shiny for Python apps provide the required interactive analysis layer that GitHub Pages cannot execute directly.
- The application code uses object-oriented structure to separate data loading, repositories, analysis logic, visualization, UI composition, and app orchestration.

## Local development

1. Install Quarto.
2. Render the site:

```bash
quarto render
```

3. Preview locally:

```bash
quarto preview
```

## Interactive app

The repository contains two interactive Shiny applications:

- `projects/data/app.py` for the Food System Emissions Explorer
- `projects/mimic/app.py` for the MIMIC-III Pathogen Alert Dashboard

Install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r projects/data/requirements.txt
pip install -r projects/mimic/requirements.txt
```

Run the food-emissions dashboard locally:

```bash
cd projects/data
../../.venv/bin/python -m shiny run app.py --port 8000
```

Then open `http://127.0.0.1:8000`.

Run the MIMIC-III dashboard locally:

```bash
cd projects/mimic
../../.venv/bin/python -m shiny run app.py --port 8001
```

Then open `http://127.0.0.1:8001`.

## Data files

The food-emissions dashboard reads these CSV files from `projects/data/data/`:

- `EDGARfood.csv`
- `Food_Product_Emissions.csv`
- `GLEAM_LivestockEmissions.csv`

The MIMIC dashboard reads alert data from `projects/mimic/data/microalerts.csv`.

## Testing

Check the website shell:

```bash
quarto render
```

Check the food-emissions app:

```bash
cd projects/data
../../.venv/bin/python -m shiny run app.py --port 8000
```

Then visit `http://127.0.0.1:8000` and confirm that:

- the dashboard loads without import errors
- the region selector updates the regional and top-country charts
- the food-products chart changes when you adjust the top-products input
- the data preview table appears below the charts

Check the MIMIC dashboard:

```bash
cd projects/mimic
../../.venv/bin/python -m shiny run app.py --port 8001
```

Then confirm that:

- the dashboard loads without import or file-path errors
- the ward filter updates the charts and data table
- the top-pathogens input changes the ranking view
- the heatmap and timeline render correctly

## OOP architecture

Both apps use a class-based architecture rather than a single procedural script.

- `DatasetLoader` and concrete CSV loaders encapsulate data access.
- Repository classes centralize dataset retrieval.
- Analyzer classes transform raw data into dashboard-ready summaries.
- Visualizer classes convert prepared data into Plotly figures.
- UI builder classes define the Shiny layout.
- App orchestrator classes wire dependencies together and expose the final Shiny app.
