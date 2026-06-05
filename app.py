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
with st.form("search_form"):
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        biomarker_input = st.text_input("Biomarker(s)", placeholder="e.g. BRCA1, TP53, IL6")
    with col2:
        disease = st.text_input("Disease", placeholder="e.g. breast cancer")
    with col3:
        max_results = st.number_input("Max results per biomarker", min_value=1, max_value=50, value=10)
    st.caption("Separate multiple biomarkers with a comma.")
    search = st.form_submit_button("Search PubMed", type="primary")

# ── Pipeline ──────────────────────────────────────────────────────────────────
if search:
    if not biomarker_input or not disease:
        st.warning("Please enter at least one biomarker and a disease.")
        st.stop()

    biomarkers = [b.strip() for b in biomarker_input.split(",") if b.strip()]
    all_papers = []

    for biomarker in biomarkers:
        with st.spinner(f"Searching PubMed for {biomarker}..."):
            query = build_query(biomarker, disease)
            pmids = search_pubmed(query, max_results=int(max_results))

        if not pmids:
            st.warning(f"No results found for **{biomarker}**. Skipping.")
            continue

        with st.spinner(f"Fetching {len(pmids)} abstract(s) for {biomarker}..."):
            papers = fetch_details(pmids)

        with st.spinner(f"Extracting evidence for {biomarker}..."):
            for paper in papers:
                paper.update(extract_evidence(paper, biomarker, disease))

        all_papers.extend(papers)

    if not all_papers:
        st.error("No results found for any of the biomarkers entered.")
        st.stop()

    papers = all_papers

    # ── Results dataframe ─────────────────────────────────────────────────────
    st.subheader(f"Results — {len(papers)} paper(s) across {len(biomarkers)} biomarker(s)")
    df = pd.DataFrame(papers)[[
        "pmid", "title", "year",
        "study_type", "biomarker_classification", "directionality",
        "key_finding", "abstract",
    ]]
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "pmid":                   st.column_config.TextColumn("PMID",            width="small"),
            "title":                  st.column_config.TextColumn("Title",           width="large",  wrap_text=True),
            "year":                   st.column_config.TextColumn("Year",            width="small"),
            "study_type":             st.column_config.TextColumn("Study Type",      width="medium"),
            "biomarker_classification": st.column_config.TextColumn("Classification", width="medium"),
            "directionality":         st.column_config.TextColumn("Directionality",  width="medium"),
            "key_finding":            st.column_config.TextColumn("Key Finding",     width="large",  wrap_text=True),
            "abstract":               st.column_config.TextColumn("Abstract",        width="large",  wrap_text=True),
        },
    )

    # ── Evidence summary ──────────────────────────────────────────────────────
    st.subheader("Evidence Summary")
    report = generate_report(papers)
    st.text(report)
