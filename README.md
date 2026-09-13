# Personal Health & Activity Engine

A Python automation project that reads lifestyle inputs from Google Sheets, validates them, retrieves reference data from public sources, calculates indicators, and writes the results back to the spreadsheet.

> This is an educational data-analysis project. It is not a medical device and does not provide medical diagnosis or treatment advice.

## What it does

- Connects to Google Sheets with a service account.
- Creates a clear input layout and applies Google Sheets data-validation rules.
- Reads age, weight, height, sleep, water intake, steps, activity days, activity duration, and activity intensity.
- Retrieves and caches reference data from public sources.
- Calculates BMI, activity duration, reference ranges, and normalized lifestyle scores.
- Writes a results table and an overall score back to Google Sheets.
- Watches the sheet for changed input and refreshes the analysis automatically.

## Architecture

```text
Google Sheets input
        |
        v
Python validation
        |
        +--> public reference sources / APIs
        |
        v
calculation engine
        |
        v
Google Sheets results and score table
```

## Tech stack

- Python 3
- Google Sheets API: `gspread` and `google-auth`
- HTTP requests: `requests`
- HTML parsing: `BeautifulSoup`
- XML parsing: Python standard library
- PDF text extraction: `pypdf`

## Project files

| File | Purpose |
| --- | --- |
| `main.py` | Clean application entry point for running the project. |
| `test_sheets.py` | Application engine: Sheets input, validation, calculations, monitoring, and results output. |
| `test_api.py` | Source-discovery helpers for physical activity and step-count reference data. |
| `requirements.txt` | Python dependencies. |

## Setup

1. Create and activate a Python virtual environment.
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Create a Google Cloud service account, enable Google Sheets API and Google Drive API, and share the target spreadsheet with the service-account email.
4. Store the service-account JSON file locally next to the script. Never commit it to Git.
5. Copy `.env.example` to a new local file named `.env`, then set the service-account filename, spreadsheet ID, and worksheet name there. `.env` is intentionally ignored by Git.
6. Run the application:

   ```bash
   python main.py
   ```

## Portfolio highlights

This project demonstrates practical Python automation skills:

- external API and web-data integration;
- data validation and error handling;
- Google Sheets automation;
- structured calculation logic;
- source filtering and caching;
- automatic spreadsheet updates.

## Reliability

Google Sheets write operations retry automatically up to three times when a temporary network timeout occurs. This prevents a short-lived connection issue from immediately stopping the workflow.

## Tests

The calculation rules can be checked without connecting to Google Sheets:

```bash
python -m unittest discover -s tests
```

## Next improvements

- Add automated tests for calculation and parsing functions.
- Move configuration to environment variables.
- Add logging and a structured error report.
- Add a small web dashboard or a Streamlit interface.
- Add an optional AI-generated plain-language summary based only on the validated calculation results.
