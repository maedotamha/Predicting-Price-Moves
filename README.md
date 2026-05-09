# Predicting Price Moves with News Sentiment

Task 1 builds a reproducible exploratory analysis workflow for Nova Financial Solutions. The project analyzes the Financial News and Stock Price Integration Dataset (FNSPID), focusing on headline sentiment, publication behavior, publisher activity, and early topic signals that can later be linked to daily market returns.

## Project Structure

```text
news-sentiment-analysis/
├── .github/workflows/unittests.yml
├── .vscode/settings.json
├── data/raw/
├── data/processed/
├── notebooks/
├── reports/figures/
├── scripts/
├── src/
└── tests/
```

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Place the FNSPID news dataset in `data/raw/`. The Task 1 notebook expects a CSV with these columns:

- `headline`
- `url`
- `publisher`
- `date`
- `stock`

The loader accepts common CSV filenames and can also be pointed at a custom path from the notebook.

## Task 1 Deliverables

- Professional repository scaffold with CI.
- `task-1` branch for EDA work.
- Reproducible notebook: [notebooks/task_1_eda.ipynb](notebooks/task_1_eda.ipynb).
- Tested helper functions in `src/`.

## Analysis Covered

- Headline length descriptive statistics.
- Article counts by publisher and stock symbol.
- Publication date trends and time-of-day behavior.
- Keyword and phrase extraction with TF-IDF.
- Lightweight topic modeling with LDA.
- Publisher domain extraction when publisher names are email addresses.

## Testing

```powershell
pytest
```
