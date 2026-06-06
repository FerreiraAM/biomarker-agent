# Biomarker Evidence Pipeline — Project Context

## What this project is

A lightweight, fully rule-based biomarker evidence synthesis tool. It searches PubMed, retrieves abstracts, extracts structured evidence fields using keyword/regex methods, generates a human-readable summary report, and exposes a Streamlit web interface.

**No LLM, no Anthropic API, no OpenAI API — rule-based extraction only. This must never change.**

---

## User profile

Bioinformatics scientist, limited Python experience. Builds step by step. Uses macOS with Python 3.9.
- Use `python3` / `pip3`, never `python` / `pip`
- Run Streamlit via `python3 -m streamlit run app.py` (streamlit not on PATH)

---

## Files

| File | Purpose |
|---|---|
| `fetch_pubmed.py` | PubMed search + abstract retrieval + rule-based extraction → CSV |
| `summarize_evidence.py` | Aggregates CSV rows into a human-readable evidence report |
| `app.py` | Streamlit web interface over the pipeline |
| `requirements.txt` | `biopython`, `streamlit`, `pandas`, `streamlit-aggrid` |
| `.gitignore` | Excludes `__pycache__/`, `*.pyc`, `.env`, `*.csv` |
| `README.md` | Full documentation |

---

## Architecture

### `fetch_pubmed.py`
- `build_query(biomarker, disease)` → PubMed query string
- `search_pubmed(query, max_results)` → list of PMIDs (Entrez esearch)
- `fetch_details(pmids)` → list of dicts with `pmid`, `title`, `year`, `abstract`
- `extract_evidence(paper, biomarker, disease)` → adds 6 fields:
  - `biomarker`, `disease` — from user input
  - `study_type` — keyword match (meta-analysis, cohort, clinical trial, in vitro, …)
  - `biomarker_classification` — negation-aware regex (diagnostic, prognostic, predictive, pharmacodynamic, unclear)
  - `directionality` — negation-aware, biomarker-scoped sentences (increased, decreased, mixed, not reported)
  - `key_finding` — last substantive sentence of the abstract
- `save_csv(papers, filepath)` — writes 10-column CSV
- `Entrez.email = "anne-maud.ferreira@epfedu.fr"`

### `summarize_evidence.py`
- `generate_report(rows: list[dict]) -> str` — used by Streamlit app (no CSV file needed)
- `main()` — CLI entrypoint: `python3 summarize_evidence.py <csv_file>`

### `app.py`
- `st.form` with Enter key support
- Comma-separated multiple biomarkers (one PubMed query per biomarker)
- AgGrid table with `wrapText=True`, `autoHeight=True`, `resizable=True`
- Evidence summary rendered below the table via `generate_report()`

---

## Git / GitHub

- Remote: `git@github.com:FerreiraAM/biomarker-agent.git` (SSH)
- All changes committed and pushed. Latest commit: "replace st.dataframe with AgGrid for text wrapping support"

---

## Completed features (in order)

1. PubMed search + abstract retrieval
2. CSV export
3. Rule-based study type detection
4. Rule-based biomarker classification (negation-aware)
5. Directionality detection (negation-aware, biomarker-scoped)
6. Key finding extraction (three-step: labelled section → conclusion cues → last substantive sentence, skipping funding lines)
7. Evidence summary report (`summarize_evidence.py`)
8. Git repository + GitHub push (SSH)
9. README with all sections
10. Streamlit interface (`app.py`)
11. Enter key support via `st.form`
12. Multiple biomarkers (comma-separated)
13. AgGrid text wrapping (replaced `st.dataframe`)
14. Abstract on row click (session state to persist results across reruns)
15. First author extraction (LastName Initials) shown in abstract panel
16. Journal name extraction from PubMed XML
17. HTML tag stripping (`<i>`, `<sup>`, etc.) from title and abstract
18. BibTeX export for all results (single `references.bib` download)
19. PubMed link in abstract panel
20. Author credit on page (Anne-Maud Ferreira · Claude)
21. App renamed to 🧬 Biomarker Evidence Explorer
22. Rule-based info banner on page
23. Evidence Summary Report: biomarker as subtitle, inline breakdowns, directionality added
24. Evidence summary aesthetics: compact card layout with emojis
25. Deployed to Streamlit Community Cloud

---

## Pending / possible next steps

None explicitly requested. Potential enhancements to discuss with user:
- CSV download button in the Streamlit app
- Confidence scores for extracted fields
- Filter/sort controls in the AgGrid table
- NCBI API key support to raise rate limits beyond 3 req/s
