"""
Streamlit interface for the biomarker evidence pipeline.
Usage:
    streamlit run app.py
"""

import pandas as pd
import streamlit as st

from fetch_pubmed import build_query, search_pubmed, fetch_details, extract_evidence
from summarize_evidence import generate_report

st.set_page_config(page_title="Biomarker Evidence Pipeline", layout="wide")
st.title("Biomarker Evidence Pipeline")
st.caption("Search PubMed and extract structured biomarker evidence.")

# ── Inputs ────────────────────────────────────────────────────────────────────
col1, col2, col3 = st.columns([2, 2, 1])
with col1:
    biomarker = st.text_input("Biomarker", placeholder="e.g. BRCA1")
with col2:
    disease = st.text_input("Disease", placeholder="e.g. breast cancer")
with col3:
    max_results = st.number_input("Max results", min_value=1, max_value=50, value=10)

search = st.button("Search PubMed", type="primary")

# ── Pipeline ──────────────────────────────────────────────────────────────────
if search:
    if not biomarker or not disease:
        st.warning("Please enter both a biomarker and a disease.")
        st.stop()

    with st.spinner("Searching PubMed..."):
        query = build_query(biomarker, disease)
        pmids = search_pubmed(query, max_results=int(max_results))

    if not pmids:
        st.error("No results found. Try different search terms.")
        st.stop()

    with st.spinner(f"Fetching {len(pmids)} abstract(s)..."):
        papers = fetch_details(pmids)

    with st.spinner("Extracting structured evidence..."):
        for paper in papers:
            paper.update(extract_evidence(paper, biomarker, disease))

    # ── Results dataframe ─────────────────────────────────────────────────────
    st.subheader(f"Results — {len(papers)} paper(s)")
    df = pd.DataFrame(papers)[[
        "pmid", "title", "year",
        "study_type", "biomarker_classification", "directionality",
        "key_finding", "abstract",
    ]]
    st.dataframe(df, use_container_width=True, hide_index=True)

    # ── Evidence summary ──────────────────────────────────────────────────────
    st.subheader("Evidence Summary")
    report = generate_report(papers)
    st.text(report)
