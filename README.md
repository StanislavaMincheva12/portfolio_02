# Stanislava Mincheva Portfolio

Quarto-based personal portfolio site with project summaries, resume content, and an interactive Shiny for Python dashboard built from a real DSS emissions project.


SHINY web: https://connect.posit.cloud/stanislavamincheva12/content/019d6d99-e4ec-3ef6-4076-7c5457291dbb
QUATTRO web: https://connect.posit.cloud/stanislavamincheva12/content/019d6d9d-c370-b7eb-a12c-18abe1304626

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

The Shiny app lives in `projects/data/app.py`.

Install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r projects/data/requirements.txt
```

Run locally:

```bash
cd projects/data
python -m shiny run app.py --port 8000
```

Then open `http://127.0.0.1:8000`.

## Data files

The dashboard reads these CSV files from `projects/data/data/`:

- `EDGARfood.csv`
- `Food_Product_Emissions.csv`
- `GLEAM_LivestockEmissions.csv`

## Testing

Check the website shell:

```bash
quarto render
```

Check the interactive app:

```bash
cd projects/data
../../.venv/bin/python -m shiny run app.py --port 8000
```

Then visit `http://127.0.0.1:8000` and confirm that:

- the dashboard loads without import errors
- the region selector updates the regional and top-country charts
- the food-products chart changes when you adjust the top-products input
- the data preview table appears below the charts
*** Add File: /Users/stanislavamincheva/Desktop/Stanislava_Mincheva_portfolio/projects/data/requirements.txt
shiny>=0.1.0
pandas>=1.5
plotly>=5.0
pycountry-convert>=0.7
