# AgriMitra – Farmer Market Price Assistant

A Streamlit prototype for agricultural market-price comparison, historical trends and estimated selling value.

## Features
- Crop, state, district, market and date filters
- Dashboard KPIs and data-status summary
- Market-wise minimum, maximum and modal price comparison
- Historical modal-price trend chart
- Selling-value calculator with transport and other expenses
- CSV import/export
- SQLite local database

## Important data notice
The included `data/sample_prices.csv` contains **illustrative sample records only**. It is not live or verified mandi data. Do not use these sample values to make a real selling decision. Replace them with a properly sourced dataset and preserve its reporting date, unit, source and update frequency.

## Run locally

```bash
python -m venv .venv
```

Activate the environment:

**Windows PowerShell**
```powershell
.venv\Scripts\Activate.ps1
```

**macOS/Linux**
```bash
source .venv/bin/activate
```

Install dependencies and run:

```bash
pip install -r requirements.txt
streamlit run app.py
```

The app opens in your browser, usually at `http://localhost:8501`.

## CSV format
Your CSV must contain these exact columns:

`State, District, Market, Commodity, Variety, Date, Minimum Price, Maximum Price, Modal Price, Unit, Source, Data_Status`

- Date format: `YYYY-MM-DD` is recommended.
- `Data_Status` should be `Sample` or `Verified`.
- Keep all prices in the same unit when comparing them.
- `Modal Price` must be between `Minimum Price` and `Maximum Price`.

## Upload to GitHub

1. Create a new GitHub repository named `agrimitra-farmer-market-assistant`.
2. Extract this project ZIP.
3. Open a terminal in the extracted project folder.
4. Run:

```bash
git init
git add .
git commit -m "Initial AgriMitra Streamlit dashboard"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/agrimitra-farmer-market-assistant.git
git push -u origin main
```

Replace `YOUR-USERNAME` with your GitHub username.

## Deploy with Streamlit Community Cloud

1. Push the repository to GitHub.
2. Open https://share.streamlit.io/ and sign in with GitHub.
3. Select the repository, branch `main`, and main file `app.py`.
4. Click Deploy.

Note: Streamlit Community Cloud's local filesystem is not a durable production database. SQLite is suitable for this local/student prototype. For persistent multi-user deployment, move the database to a hosted database service.
