# Lister Sorter

A Streamlit application to parse, sort, and export lists of scholars from a CSV file.

## Description

This tool provides a web-based interface to process a CSV file containing scholar information. It automatically categorizes scholars into "Rizal," "Chancellor," and "Dean" listers, stores the data in a local SQLite database, and allows for both manual and automated batch exporting of the sorted lists.

## Screenshot

<img width="1657" height="961" alt="Screenshot" src="https://github.com/user-attachments/assets/85e9de63-a1ee-45a8-aded-779cdee37fb7" />

## Features

- **CSV Parsing:** Ingests a CSV file and extracts scholar data.
- **Automatic Categorization:** Sorts scholars into award types based on keywords found in the source file.
- **Database Storage:** Saves processed data into a SQLite database for persistence and querying.
- **Interactive UI:** A user-friendly interface built with Streamlit.
- **Manual Filtering with Dynamic Naming:** A "Single List Generator" to filter scholars by year level, course, and award type. The exported CSV is automatically named based on the selected filters (e.g., `Y1-2_BSIT_Dean.csv`).
- **Fully Automated Batch Export:** An "Auto-Generator" that automates the creation of CSVs for every possible combination of year, course, and award (48 files total), then bundles them into a single downloadable ZIP file.
- **Data Verification:** A "Raw Data Inspector" to view the original uploaded CSV for verification.

## How to Use

1.  **Install dependencies:**
    ```bash
    pip install streamlit pandas
    ```

2.  **Run the application:**
    ```bash
    streamlit run app.py
    ```

3.  Open your web browser and navigate to the provided local URL.
4.  Upload your CSV file via the sidebar.
5.  Click "Process CSV Data."
6.  Use the tabs to filter, inspect, and download the scholar lists.

## File Descriptions

- **`app.py`**: The main Streamlit application script.
- **`ccs_scholars.db`**: The SQLite database file where scholar data is stored.
- **`.venv/`**: The Python virtual environment directory.
