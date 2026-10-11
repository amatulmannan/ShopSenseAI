# Build verification record

Verification date: 2026-10-11

## Executed successfully

- `python -m compileall -q .` — passed.
- `python -m pytest -q` — **38 passed, 0 failed, 0 skipped**.
- Sample CSV integration check — sales CSV: 36/36 rows loaded; products CSV: 5/5 rows loaded; no rejected rows. Deterministic summary returned revenue `8430.00`, units sold `102`, gross profit `2760.00`; inventory produced one low-stock and one out-of-stock alert.
- Static UI-path test confirms `app.py` avoids `st.dataframe`, `st.table`, and `st.line_chart`, and uses Plotly chart rendering plus escaped HTML tables.
- ZIP contents are intended to exclude `.env`, virtual environments, caches, and machine-specific files.

## Environment and limits

- Python used for executed checks: **CPython 3.13.5** on Linux, not Windows.
- The execution image already had pandas 2.2.3, python-dotenv 1.2.2, pytest 9.0.2, Plotly 6.5.2, and typing_extensions 4.16.0. Streamlit, Altair, PyArrow, and the OpenAI SDK were not installed in the image.
- A clean virtual environment was created, but installing the pinned requirements could not complete because the environment could not resolve the package index host (network/DNS unavailable). Therefore, the exact pinned dependency set was **not installed or verified as a clean environment** here.
- `streamlit run app.py` was attempted but could not launch because Streamlit is not installed in this execution image. No pages were visually verified in a browser.
- API integration is implemented using the official OpenAI Python SDK interface and tested with mocked SDK responses. No live provider request was made, and no API key was available in this environment.
- The Windows Application Control restriction cannot be reproduced in this Linux environment. The app avoids Streamlit's Arrow-backed dataframe/table and built-in line-chart renderers, but Streamlit still declares PyArrow as a dependency. If the operating-system policy blocks an import at startup, an administrator-approved runtime/package allowlisting decision may still be required.

Do not treat the unexecuted Windows install, browser launch, or live API call as verified. Use the README commands on a network-enabled Windows machine with approved Python 3.12 packages to complete those checks.
