# Stanislava Mincheva Portfolio

Quarto-based personal portfolio site with project summaries, resume content, and an interactive Shiny for Python demo.

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

The Shiny demo lives in `projects/data/app.py`.

Install dependencies:

```bash
pip install -r requirements.txt
```

Run locally:

```bash
cd projects/data
shiny run app.py
```