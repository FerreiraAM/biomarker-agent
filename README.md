# Biomarker Evidence Pipeline

A lightweight Python pipeline to search PubMed for biomarker-disease literature, retrieve abstracts, extract structured evidence fields using rule-based methods, and generate a human-readable summary report.

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
- Retrieves PMID, title, publication year, and abstract for the top 10 results
- Applies rule-based extraction to each abstract:
  - **study_type** — e.g. cohort, clinical trial, review, in vitro
  - **biomarker_classification** — diagnostic, prognostic, predictive, pharmacodynamic, or unclear
  - **directionality** — increased, decreased, mixed, or not reported
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

---

## Requirements

- Python 3.9+
- [Biopython](https://biopython.org/)

Install dependencies:
```bash
pip install -r requirements.txt
```

---

## Usage

**Step 1 — Fetch papers and extract evidence:**
```bash
python fetch_pubmed.py "BRCA1" "breast cancer"
```
Output: `BRCA1_breast_cancer.csv`

**Step 2 — Generate evidence summary:**
```bash
python summarize_evidence.py BRCA1_breast_cancer.csv
```

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

## Notes

- No API key required — the pipeline uses NCBI's public Entrez API via Biopython
- Extraction is fully rule-based (keyword matching + regex); no LLM or external AI service is used
- CSV files are excluded from version control (see `.gitignore`)
