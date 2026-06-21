# Installation Guide

1. Create a Python 3.13 environment.
2. Install the package in editable mode with the project dependencies.
3. Initialize the database with `dip init-db`.
4. Run the dashboard with `dip ui` or `streamlit run src/drive_intelligence_platform/app.py`.

Recommended environment variables:

- `DIP_DATABASE_URL`
- `DIP_LOG_LEVEL`
- `DIP_OPENAI_API_KEY`
- `DIP_MODE`