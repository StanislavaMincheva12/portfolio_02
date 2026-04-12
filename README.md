# Stanislava Mincheva Portfolio

Quarto-based personal portfolio, combining static portfolio pages with embedded Shiny for Python applications deployed on Posit Connect Cloud.

## Live links

- Shiny app: https://connect.posit.cloud/stanislavamincheva12/content/019d6d99-e4ec-3ef6-4076-7c5457291dbb
- MIMIC-III app: https://connect.posit.cloud/stanislavamincheva12/content/019d7c6d-43eb-cc64-b3f7-2de7c0b3ca86
- Quarto website: https://connect.posit.cloud/stanislavamincheva12/content/019d6d9d-c370-b7eb-a12c-18abe1304626

- A Quarto website provides the public-facing portfolio shell.
- Shiny for Python apps provide the required interactive analysis layer that GitHub Pages cannot execute directly.
- The application code uses object-oriented structure to separate data loading, repositories, analysis logic, visualization, UI composition, and app orchestration.


## Repository structure

- `index.qmd`, `about.qmd`, and `projects/*.qmd` define the Quarto website content.
- `assets/styles.css` contains the site-wide visual styling.
- `projects/data/app.py` implements the Food System Emissions Explorer.
- `projects/mimic/app.py` implements the MIMIC-III Pathogen Alert Dashboard.
- `_site/` contains the rendered site output that can be published directly.

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

## Data files

The food-emissions dashboard reads these CSV files from `projects/data/data/`:

- `EDGARfood.csv`
- `Food_Product_Emissions.csv`
- `GLEAM_LivestockEmissions.csv`

The MIMIC dashboard reads alert data from `projects/mimic/data/microalerts.csv`.

## OOP architecture

Both apps use a class-based architecture rather than a single procedural script.

- `DatasetLoader` and concrete CSV loaders encapsulate data access.
- Repository classes centralize dataset retrieval.
- Analyzer classes transform raw data into dashboard-ready summaries.
- Visualizer classes convert prepared data into Plotly figures.
- UI builder classes define the Shiny layout.
- App orchestrator classes wire dependencies together and expose the final Shiny app.
