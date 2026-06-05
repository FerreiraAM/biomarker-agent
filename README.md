# Biomarker Evidence Pipeline

A lightweight Python pipeline to search PubMed for biomarker-disease literature, retrieve abstracts, extract structured evidence fields using rule-based methods, and generate a human-readable summary report. Includes an interactive Streamlit web interface.

---

## Purpose

This project demonstrates a lightweight biomedical text-mining pipeline for:

- Biomarker evidence aggregation
- Translational literature synthesis
- Structured extraction from PubMed abstracts
- Reproducible, interpretable bioinformatics workflows

---

## What it does

### 1. `fetch_pubmed.py` — Search & extract
- Queries PubMed for papers matching a biomarker and disease term
- Retrieves PMID, title, publication year, and abstract
- Applies rule-based extraction to each abstract:
  - **study_type** — e.g. cohort, clinical trial, review, in vitro
  - **biomarker_classification** — diagnostic, prognostic, predictive, pharmacodynamic, or unclear
  - **directionality** — increased, decreased, mixed, or not reported (negation-aware)
  - **key_finding** — the last sentence of the abstract (typically the conclusion)
- Saves all fields to a CSV file

### 2. `summarize_evidence.py` — Evidence summary
- Reads a CSV produced by `fetch_pubmed.py`
- For each biomarker, computes:
  - Total number of studies
  - Breakdown of study types
  - Breakdown of biomarker classifications
  - Top 3 associated diseases
  - A short synthesis paragraph assembled from the statistics
- Prints a clean human-readable report to the terminal

### 3. `app.py` — Streamlit web interface
- Interactive UI to run the full pipeline from a browser
- Text inputs for biomarker and disease, number input for result count
- Displays extracted results in a sortable dataframe
- Displays the evidence summary report below the table

---

## Requirements

- Python 3.9+
- [Biopython](https://biopython.org/), [Streamlit](https://streamlit.io/), [pandas](https://pandas.pydata.org/)

Install dependencies:
```bash
pip3 install -r requirements.txt
```

---

## Usage

### Command-line

**Step 1 — Fetch papers and extract evidence:**
```bash
python3 fetch_pubmed.py "BRCA1" "breast cancer"
```
Output: `BRCA1_breast_cancer.csv`

**Step 2 — Generate evidence summary:**
```bash
python3 summarize_evidence.py BRCA1_breast_cancer.csv
```

### Streamlit app

```bash
python3 -m streamlit run app.py
```

A browser window opens at `http://localhost:8501`. Enter a biomarker, disease, and number of results, then click **Search PubMed**.

---

## Output CSV columns

| Column | Description |
|---|---|
| `pmid` | PubMed identifier |
| `title` | Article title |
| `year` | Publication year |
| `abstract` | Full abstract text |
| `biomarker` | Biomarker search term |
| `disease` | Disease search term |
| `study_type` | Detected study design |
| `key_finding` | Last sentence of the abstract |
| `biomarker_classification` | Role of the biomarker |
| `directionality` | Direction of expression change |

---

## Development approach

This project was built using an AI-assisted development workflow (Claude Code) to accelerate Python implementation and refactoring.

All biomarker extraction logic remains rule-based and fully interpretable, with no dependency on external LLMs or black-box models.

---

## Notes

- No API key required — the pipeline uses NCBI's public Entrez API via Biopython
- Extraction is fully rule-based (keyword matching + regex); no LLM or external AI service is used
- CSV files are excluded from version control (see `.gitignore`)
