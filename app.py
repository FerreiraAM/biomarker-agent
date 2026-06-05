"""
Streamlit interface for the biomarker evidence pipeline.
Usage:
    streamlit run app.py
"""

import pandas as pd
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

from fetch_pubmed import build_query, search_pubmed, fetch_details, extract_evidence
from summarize_evidence import generate_report

st.set_page_config(page_title="Biomarker Evidence Pipeline", layout="wide")
st.title("Biomarker Evidence Pipeline")
st.caption("Search PubMed and extract structured biomarker evidence.")

# ── Session state ─────────────────────────────────────────────────────────────
if "papers" not in st.session_state:
    st.session_state.papers = []
if "df" not in st.session_state:
    st.session_state.df = None
if "report" not in st.session_state:
    st.session_state.report = ""
if "biomarkers" not in st.session_state:
    st.session_state.biomarkers = []

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

    # Store results in session state so they survive reruns triggered by row clicks
    st.session_state.papers = all_papers
    st.session_state.biomarkers = biomarkers
    st.session_state.df = pd.DataFrame(all_papers)[[
        "pmid", "title", "year",
        "study_type", "biomarker_classification", "directionality",
        "key_finding", "abstract", "first_author",
    ]].rename(columns={
        "pmid":                     "PMID",
        "title":                    "Title",
        "year":                     "Year",
        "study_type":               "Study Type",
        "biomarker_classification": "Classification",
        "directionality":           "Directionality",
        "key_finding":              "Key Finding",
        "abstract":                 "Abstract",
        "first_author":             "First Author",
    })
    st.session_state.report = generate_report(all_papers)

# ── Display results (persists across reruns) ──────────────────────────────────
if st.session_state.df is not None:
    df = st.session_state.df
    papers = st.session_state.papers
    biomarkers = st.session_state.biomarkers

    st.subheader(f"Results — {len(papers)} paper(s) across {len(biomarkers)} biomarker(s)")

    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(wrapText=True, autoHeight=True, resizable=True)
    gb.configure_column("PMID",           width=100)
    gb.configure_column("Year",           width=80)
    gb.configure_column("First Author",   hide=True)
    gb.configure_column("Study Type",     width=130)
    gb.configure_column("Classification", width=140)
    gb.configure_column("Directionality", width=130)
    gb.configure_column("Title",          width=280)
    gb.configure_column("Key Finding",    width=300)
    gb.configure_column("Abstract",       hide=True)
    gb.configure_selection(selection_mode="single", use_checkbox=False)

    grid_response = AgGrid(
        df,
        gridOptions=gb.build(),
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        use_container_width=True,
        height=650,
    )

    # ── Abstract on row click ─────────────────────────────────────────────────
    selected = grid_response.get("selected_rows")
    if selected is not None and len(selected) > 0:
        row = selected[0] if isinstance(selected, list) else selected.iloc[0]
        st.subheader("Abstract")
        st.info(f"**{row['Title']}**\n{row['First Author']} et al. ({row['Year']})\n\n{row['Abstract']}")

    # ── Evidence summary ──────────────────────────────────────────────────────
    st.subheader("Evidence Summary")
    st.text(st.session_state.report)
