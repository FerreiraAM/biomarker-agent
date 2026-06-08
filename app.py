"""
Streamlit interface for the biomarker evidence pipeline.
Usage:
    streamlit run app.py
"""

import pandas as pd
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

from fetch_pubmed import build_query, search_pubmed, fetch_details, extract_evidence
from summarize_evidence import generate_report, summarize_biomarker

st.set_page_config(page_title="Biomarker Evidence Explorer", layout="wide")
st.title("🧬 Biomarker Evidence Explorer")
st.caption("Search PubMed and extract structured biomarker evidence.")
st.markdown(
    "<div style='text-align: right; color: grey; font-size: 0.8em;'>"
    "Built by <strong>Anne-Maud Ferreira</strong> · "
    "Co-developed with <strong>Claude (Anthropic)</strong>"
    "</div>",
    unsafe_allow_html=True,
)

with st.expander("ℹ️ How it works"):
    st.markdown("""
This tool searches PubMed and extracts structured evidence fields using rule-based methods
(keyword matching + regex). No LLM or external AI service is used — all extraction is transparent and reproducible.

---

**Study type**
Keywords matched against title + abstract (case-insensitive). Priority order of the labels:
`meta-analysis` → `review` → `clinical trial` → `cohort` → `case-control` → `in vitro` → `observational` → `other`

**Classification**
Sentence-level keyword/regex matching (negation-aware).
Negated sentences (e.g. "no significant association") are skipped.
Labels: `diagnostic` · `prognostic` · `predictive` · `pharmacodynamic` · `unclear`

**Directionality**
Only sentences mentioning the biomarker are examined. Negated sentences are skipped.
Labels: `increased` · `decreased` · `mixed` · `not reported`
""")

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
    search = st.form_submit_button("Search PubMed", type="primary", use_container_width=False)

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
        "key_finding", "abstract", "first_author", "journal",
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
        "journal":                  "Journal",
    })
    st.session_state.report = generate_report(all_papers)

# ── Display results (persists across reruns) ──────────────────────────────────
if st.session_state.df is not None:
    df = st.session_state.df
    papers = st.session_state.papers
    biomarkers = st.session_state.biomarkers

    st.subheader(f"Results — {len(papers)} paper(s) across {len(biomarkers)} biomarker(s)")
    st.caption("💡 Tip: Click on any cell in a row to display the full abstract below the table.")

    # ── BibTeX export for all results ─────────────────────────────────────────
    def build_bibtex_all(dataframe: pd.DataFrame) -> str:
        entries = []
        for _, row in dataframe.iterrows():
            last_name = row["First Author"].split()[0] if row["First Author"] != "Unknown" else "Unknown"
            cite_key = f"{last_name}{row['Year']}"
            pubmed_url = f"https://pubmed.ncbi.nlm.nih.gov/{row['PMID']}/"
            entry = (
                f"@article{{{cite_key},\n"
                f"  author  = {{{row['First Author']} et al.}},\n"
                f"  title   = {{{row['Title']}}},\n"
                f"  journal = {{{row['Journal']}}},\n"
                f"  year    = {{{row['Year']}}},\n"
                f"  note    = {{PMID: {row['PMID']}}},\n"
                f"  url     = {{{pubmed_url}}}\n"
                f"}}"
            )
            entries.append(entry)
        return "\n\n".join(entries)

    st.download_button(
        label="📄 Export all references as BibTeX",
        data=build_bibtex_all(df),
        file_name="references.bib",
        mime="text/plain",
        key="bibtex_download",
    )

    gb = GridOptionsBuilder.from_dataframe(df.reset_index(drop=True))
    gb.configure_default_column(wrapText=True, autoHeight=True, resizable=True)
    gb.configure_column("PMID",           width=100)
    gb.configure_column("Year",           width=80)
    gb.configure_column("First Author",   hide=True)
    gb.configure_column("Journal",        hide=True)
    gb.configure_column("Study Type",     width=130)
    gb.configure_column("Classification", width=140)
    gb.configure_column("Directionality", width=130)
    gb.configure_column("Title",          width=280)
    gb.configure_column("Key Finding",    width=300)
    gb.configure_column("Abstract",       hide=True)
    gb.configure_selection(selection_mode="single", use_checkbox=False)

    grid_response = AgGrid(
        df.reset_index(drop=True),
        gridOptions=gb.build(),
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        use_container_width=True,
        height=450,
        allow_unsafe_jscode=True,
    )

    # ── Abstract on row click ─────────────────────────────────────────────────
    selected = grid_response.get("selected_rows")
    if selected is not None and len(selected) > 0:
        row = selected[0] if isinstance(selected, list) else selected.iloc[0]
        st.subheader("Abstract")
        pubmed_url = f"https://pubmed.ncbi.nlm.nih.gov/{row['PMID']}/"
        st.info(f"**{row['Title']}**\n{row['First Author']} et al. ({row['Year']})\n\n{row['Abstract']}")

        st.markdown(f"🔗 [View on PubMed]({pubmed_url})")

    # ── Evidence summary ──────────────────────────────────────────────────────
    st.subheader("Evidence Summary Report")
    st.text(f"{len(papers)} biomarker(s) found" if len(st.session_state.biomarkers) > 1 else "1 biomarker found")
    for biomarker, biomarker_rows in sorted(
        {b: [p for p in papers if p.get("biomarker") == b] for b in st.session_state.biomarkers}.items()
    ):
        st.subheader(biomarker)
        # Strip the biomarker title line (first 2 lines) since we render it as subheader
        section = summarize_biomarker(biomarker, biomarker_rows)
        body = "\n".join(section.strip().splitlines()[2:])
        st.text(body)
