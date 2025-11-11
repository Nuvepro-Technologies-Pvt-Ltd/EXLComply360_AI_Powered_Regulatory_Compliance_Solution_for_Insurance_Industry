# EXLComply360 – AI-Powered Regulatory Compliance Analyzer

This project is a proof-of-concept (POC) system to analyze insurance forms and determine their compliance with pre-stored regulatory rules. It uses a simulated AI/NLP backend to detect missing clauses, visualizes compliance reports, and generates insights through an interactive Streamlit dashboard.

## Tech Stack

- **Backend**: FastAPI (Python)
- **Frontend**: Streamlit (Python)
- **Data Storage**: Local JSON files (no database)
- **AI Simulation**: Keyword matching (can be extended with spaCy for NLP)
- **PDF Handling**: PyMuPDF (`fitz`)
- **Visualization**: Plotly via Streamlit charts

## Project Structure

```
.
├── data/
│   ├── regulations.json      # Stores regulation entries
│   ├── forms.json            # Stores metadata of uploaded forms
│   ├── reports.json          # Stores detailed analysis reports
│   └── alerts.json           # Stores alerts for non-compliant forms
├── uploaded_forms/
│   └── ...                   # Stores uploaded PDF files
├── backend.py                # The FastAPI application backend
├── main.py                   # The Streamlit application frontend
├── requirements.txt          # Python dependencies
└── README.md                 # This readme file
```

## Setup and Run Instructions

### 1. Create a Virtual Environment

It is highly recommended to use a virtual environment to manage project dependencies.

```bash
python -m venv venv
```

### 2. Activate the Virtual Environment

- **On Windows**:
  ```bash
  .\venv\Scripts\activate
  ```
- **On macOS/Linux**:
  ```bash
  source venv/bin/activate
  ```

### 3. Install Dependencies

Install all required packages from the `requirements.txt` file.

```bash
pip install -r requirements.txt
```

### 4. Download spaCy Model (Optional but Recommended)

The backend is set up to use a spaCy model for more advanced NLP tasks in the future. Download the small English model:

```bash
python -m spacy download en_core_web_sm
```

### 5. Run the FastAPI Backend

Start the backend server using Uvicorn. It will typically run on `http://127.0.0.1:8000`.

```bash
uvicorn backend:app --reload
```

### 6. Run the Streamlit Frontend

In a **new terminal**, run the Streamlit application. It will open in your browser, usually at `http://localhost:8501`.

```bash
streamlit run main.py
```

## How to Use the Application

1.  **Upload Regulations**:
    -   Navigate to the **Upload & Analyze** page.
    -   Under "Step 1", upload the `data/regulations.json` file (or your own version) to populate the system with compliance rules.

2.  **Analyze a Form**:
    -   On the same page, under "Step 2", upload a sample PDF insurance form.
    -   Click "Analyze Form". The system will process the document and display an instant analysis report.

3.  **View the Dashboard**:
    -   Navigate to the **Dashboard** page to see aggregated statistics, such as the average compliance score, total alerts, and a breakdown of risks.

4.  **Review Reports**:
    -   Go to the **View Reports** page to see a list of all analyzed forms.
    -   Select a form from the dropdown to view its detailed compliance report, including which rules were matched and which were missing.
