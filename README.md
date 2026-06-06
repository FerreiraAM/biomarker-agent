# Biomarker Evidence Pipeline

A lightweight Python pipeline to search PubMed for biomarker-disease literature, retrieve abstracts, extract structured evidence fields using rule-based methods, and generate a human-readable summary report. Includes an interactive Streamlit web interface.

**Author:** Anne-Maud Ferreira · **Co-developed with:** Claude (Anthropic)

---

## Purpose

This project demonstrates a lightweight biomedical text-mining pipeline for:

- Biomarker evidence aggregation
- Translational literature synthesis
- Structured extraction from PubMed abstracts
- Reproducible, interpretable bioinformatics workflows

---

## Development approach

This project was built using an AI-assisted development workflow (Claude Code) to accelerate Python implementation and refactoring.

All biomarker extraction logic remains rule-based and fully interpretable, with no dependency on external LLMs or black-box models.

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
- Displays extracted results in an interactive AgGrid table (sortable, resizable, with text wrapping)
- Click any row to reveal the full abstract with first author, year, and a link to PubMed
- Export all references as a BibTeX file with one click
- Displays the evidence summary report below the table

---

## Requirements

- Python 3.9+
- [Biopython](https://biopython.org/), [Streamlit](https://streamlit.io/), [pandas](https://pandas.pydata.org/), [streamlit-aggrid](https://github.com/PablocFonseca/streamlit-aggrid)

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
| `first_author` | First author name and initials (e.g. Smith JA) |
| `journal` | Journal name |
| `directionality` | Direction of expression change |

---

## BibTeX export

After running a search, click **📄 Export all references as BibTeX** to download a `references.bib` file containing one entry per paper. Each entry includes:

```bibtex
@article{Smith2023,
  author  = {Smith JA et al.},
  title   = {BRCA1 mutations in breast cancer...},
  journal = {Nature Genetics},
  year    = {2023},
  note    = {PMID: 12345678},
  url     = {https://pubmed.ncbi.nlm.nih.gov/12345678/}
}
```

The citation key is formatted as `LastNameYear` (e.g. `Smith2023`). The file can be imported directly into reference managers such as Zotero, Mendeley, or EndNote.

---

## Limitations

- **Biomarkers** — multiple biomarkers are supported (comma-separated), but NCBI limits unauthenticated requests to 3 per second; searches slow down noticeably above ~10 biomarkers
- **Disease** — only one disease term per search session
- **Papers** — capped at 50 results per biomarker in the UI; fetching large numbers of abstracts in a single call may be slow

---

## Notes

- No API key required — the pipeline uses NCBI's public Entrez API via Biopython
- Extraction is fully rule-based (keyword matching + regex); no LLM or external AI service is used
- CSV files are excluded from version control (see `.gitignore`)
