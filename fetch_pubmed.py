"""
Fetch the first 10 PubMed papers matching a biomarker + disease query,
then extract structured evidence fields from each abstract using rule-based methods.
Usage:
    python fetch_pubmed.py "BRCA1" "breast cancer"
"""

import csv
import re
import sys
from Bio import Entrez


def strip_html(text: str) -> str:
    """Remove HTML tags (e.g. <i>, <sup>, <b>) from a string."""
    return re.sub(r"<[^>]+>", "", text)

Entrez.email = "anne-maud.ferreira@epfedu.fr"

MAX_RESULTS = 10

# ── Rule-based extraction keyword maps ────────────────────────────────────────

STUDY_TYPE_KEYWORDS = {
    "meta-analysis":   ["meta-analysis", "meta analysis", "systematic review and meta"],
    "review":          ["review", "literature review", "narrative review"],
    "clinical trial":  ["randomized", "randomised", "clinical trial", "rct", "placebo-controlled",
                        "double-blind", "phase ii", "phase iii"],
    "cohort":          ["cohort", "longitudinal", "prospective study", "retrospective study",
                        "follow-up study"],
    "case-control":    ["case-control", "case control", "cases and controls"],
    "in vitro":        ["in vitro", "cell line", "cell culture", "in vivo", "mouse model",
                        "animal model", "xenograft"],
    "observational":   ["observational", "cross-sectional", "prevalence study", "epidemiological"],
}

CLASSIFICATION_KEYWORDS = {
    "diagnostic":      ["diagnos", "detection", "sensitivity", "specificity", "auc", "roc",
                        "screening", "biomarker for diagnos"],
    "prognostic":      ["prognos", "survival", "overall survival", "disease-free survival",
                        "progression", "recurrence", "outcome", "mortality"],
    "predictive":      ["predict", "response to", "treatment response", "predict.*therapy",
                        "predict.*treatment", "predictive"],
    "pharmacodynamic": ["pharmacodynamic", "drug response", "pharmacokinetic", "metabolism",
                        "clearance", "drug level"],
}

DIRECTIONALITY_PATTERNS = {
    "increased": [
        r"\bincreas\w*\b", r"\bupregulat\w*\b", r"\boverexpres\w*\b",
        r"\belevat\w*\b", r"\bhigher\b", r"\bhigh expression\b",
        r"\bup-regulat\w*\b", r"\bamplifi\w*\b", r"\baccumulat\w*\b",
        r"\benrich\w*\b", r"\bactivat\w*\b",
    ],
    "decreased": [
        r"\bdecreas\w*\b", r"\bdownregulat\w*\b", r"\bunderexpres\w*\b",
        r"\breduced?\b", r"\blower\b", r"\blow expression\b",
        r"\bdown-regulat\w*\b", r"\bloss of\b", r"\bdeplet\w*\b",
        r"\bsilenc\w*\b", r"\bsuppress\w*\b", r"\babsen\w*\b",
    ],
}

# Words/phrases that, when found within the same sentence as a classification
# keyword, indicate the finding is negated and should not trigger a match.
NEGATION_CUES = [
    "no significant", "not significant", "no association", "no significant association",
    "was not", "were not", "did not", "does not", "do not",
    "failed to", "no evidence", "no difference", "no effect",
    "absence of", "not associated", "not predict", "not diagnos",
    "not correlat", "no correlat", "non-significant", "ns ",
    "could not", "cannot", "could not be", "not be",
]


def build_query(biomarker: str, disease: str) -> str:
    return f"{biomarker}[Title/Abstract] AND {disease}[Title/Abstract]"


def search_pubmed(query: str, max_results: int = MAX_RESULTS) -> list[str]:
    handle = Entrez.esearch(db="pubmed", term=query, retmax=max_results)
    record = Entrez.read(handle)
    handle.close()
    return record["IdList"]


def fetch_details(pmids: list[str]) -> list[dict]:
    ids = ",".join(pmids)
    handle = Entrez.efetch(db="pubmed", id=ids, rettype="xml", retmode="xml")
    records = Entrez.read(handle)
    handle.close()

    papers = []
    for article in records["PubmedArticle"]:
        medline = article["MedlineCitation"]
        art = medline["Article"]

        pmid = str(medline["PMID"])
        title = str(art.get("ArticleTitle", "No title"))

        journal_info = art.get("Journal", {})
        pub_date = journal_info.get("JournalIssue", {}).get("PubDate", {})
        year = str(pub_date.get("Year", pub_date.get("MedlineDate", "Unknown")))
        journal = str(journal_info.get("Title", ""))

        abstract_texts = art.get("Abstract", {}).get("AbstractText", [])
        if isinstance(abstract_texts, list):
            abstract = " ".join(str(t) for t in abstract_texts)
        else:
            abstract = str(abstract_texts)

        # First author: LastName Initials (e.g. "Smith JA")
        authors = art.get("AuthorList", [])
        if authors:
            first = authors[0]
            last = str(first.get("LastName", ""))
            initials = str(first.get("Initials", ""))
            first_author = f"{last} {initials}".strip() if last else "Unknown"
        else:
            first_author = "Unknown"

        papers.append({
            "pmid": pmid,
            "title": strip_html(title),
            "year": year,
            "abstract": strip_html(abstract),
            "first_author": first_author,
            "journal": journal,
        })

    return papers


def detect_study_type(text: str) -> str:
    """Return the first matching study type based on keyword presence."""
    lower = text.lower()
    for study_type, keywords in STUDY_TYPE_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            return study_type
    return "unclassified"


def _sentences(text: str) -> list[str]:
    """Split text into sentences."""
    return re.split(r"(?<=[.!?])\s+", text.strip())


def _is_negated(sentence: str) -> bool:
    """Return True if the sentence contains a negation cue."""
    lower = sentence.lower()
    return any(cue in lower for cue in NEGATION_CUES)


def detect_directionality(text: str, biomarker: str) -> str:
    """
    Return 'increased', 'decreased', 'mixed', or 'not reported'.

    Strategy: only examine sentences that mention the biomarker, then look for
    directionality patterns in those sentences. Negated sentences are skipped.
    If both directions appear across different sentences, return 'mixed'.
    """
    sentences = _sentences(text)
    biomarker_lower = biomarker.lower()

    found = set()
    for sentence in sentences:
        lower = sentence.lower()
        # Only consider sentences that mention the biomarker
        if biomarker_lower not in lower:
            continue
        if _is_negated(sentence):
            continue
        for direction, patterns in DIRECTIONALITY_PATTERNS.items():
            if any(re.search(p, lower) for p in patterns):
                found.add(direction)

    if found == {"increased", "decreased"}:
        return "mixed"
    if "increased" in found:
        return "increased"
    if "decreased" in found:
        return "decreased"
    return "not reported"


def detect_classification(text: str) -> str:
    """
    Return the first matching biomarker classification based on keyword/regex presence,
    skipping sentences that contain negation cues (e.g. 'no significant association').
    """
    sentences = _sentences(text)
    for label, patterns in CLASSIFICATION_KEYWORDS.items():
        for sentence in sentences:
            if _is_negated(sentence):
                continue
            lower = sentence.lower()
            if any(re.search(pattern, lower) for pattern in patterns):
                return label
    return "unclear"


def _is_funding_line(sentence: str) -> bool:
    """Return True if a sentence looks like a funding acknowledgment rather than a finding."""
    s = sentence.strip()
    if len(s) > 100:
        return False
    verbs = ["is", "are", "was", "were", "have", "has", "suggest", "show", "demonstrate",
             "indicate", "support", "reveal", "provide", "enable", "encourage", "conclude"]
    lower = s.lower()
    return not any(v in lower for v in verbs)


CONCLUSION_CUES = [
    r"our findings",
    r"our results",
    r"our study",
    r"our data",
    r"we conclude",
    r"we show",
    r"we demonstrate",
    r"we report",
    r"we suggest",
    r"we found",
    r"these results",
    r"these findings",
    r"this study",
    r"this case",
    r"taken together",
    r"in conclusion",
    r"in summary",
    r"altogether",
    r"collectively",
    r"thus,",
    r"therefore,",
    r"together,",
]


def extract_key_finding(abstract: str) -> str:
    """
    Extract the key finding from an abstract using a three-step strategy:
    1. Look for a labelled CONCLUSIONS/INTERPRETATION section (structured abstracts).
    2. Look for sentences containing conclusion-indicator phrases.
    3. Fall back to the last substantive sentence, skipping funding/acknowledgment lines.
    """
    if not abstract:
        return ""

    sentences = re.split(r"(?<=[.!?])\s+", abstract.strip())
    sentences = [s for s in sentences if len(s) > 20]

    # Step 1 — labelled conclusion section
    conclusion_labels = [
        r"conclusions?",
        r"conclusions? and relevance",
        r"interpretation",
        r"significance",
        r"clinical significance",
        r"summary",
    ]
    pattern = r"(?i)(?:" + "|".join(conclusion_labels) + r")[:\s]+(.+)"
    match = re.search(pattern, abstract)
    if match:
        conclusion_text = match.group(1).strip()
        sents = re.split(r"(?<=[.!?])\s+", conclusion_text)
        sents = [s for s in sents if len(s) > 20]
        return sents[0] if sents else conclusion_text[:300]

    # Step 2 — conclusion-indicator phrases
    for sentence in sentences:
        lower = sentence.lower()
        if any(re.search(cue, lower) for cue in CONCLUSION_CUES):
            return sentence

    # Step 3 — last substantive sentence, skipping funding lines
    for sentence in reversed(sentences):
        if not _is_funding_line(sentence):
            return sentence

    return sentences[-1] if sentences else abstract[:200]


def extract_evidence(paper: dict, biomarker_query: str, disease_query: str) -> dict:
    """
    Extract structured biomarker evidence from a paper using rule-based methods.
    Returns a dict with five fields ready to merge into the paper record.
    """
    abstract = paper.get("abstract", "")
    title = paper.get("title", "")
    full_text = f"{title} {abstract}"

    return {
        # Use the user's search terms as the biomarker/disease values.
        # They are already confirmed to appear in the abstract (PubMed matched on them).
        "biomarker": biomarker_query,
        "disease": disease_query,
        "study_type": detect_study_type(full_text),
        "key_finding": extract_key_finding(abstract),
        "biomarker_classification": detect_classification(full_text),
        "directionality": detect_directionality(full_text, biomarker_query),
    }


def print_results(papers: list[dict]) -> None:
    for i, paper in enumerate(papers, start=1):
        print(f"\n{'='*70}")
        print(f"[{i}] PMID : {paper['pmid']}")
        print(f"    Year  : {paper['year']}")
        print(f"    Title : {paper['title']}")
        print(f"    Abstract:\n    {paper['abstract'][:500]}{'...' if len(paper['abstract']) > 500 else ''}")
    print(f"\n{'='*70}")
    print(f"Total results shown: {len(papers)}")


def save_csv(papers: list[dict], filepath: str) -> None:
    fieldnames = [
        "pmid", "title", "year", "abstract", "first_author", "journal",
        "biomarker", "disease", "study_type", "key_finding",
        "biomarker_classification", "directionality",
    ]
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(papers)
    print(f"Results saved to: {filepath}")


def main():
    if len(sys.argv) != 3:
        print("Usage: python fetch_pubmed.py \"<biomarker>\" \"<disease>\"")
        print("Example: python fetch_pubmed.py \"BRCA1\" \"breast cancer\"")
        sys.exit(1)

    biomarker = sys.argv[1]
    disease = sys.argv[2]

    print(f"Searching PubMed for: {biomarker} + {disease} ...")
    query = build_query(biomarker, disease)
    pmids = search_pubmed(query)

    if not pmids:
        print("No results found. Try different search terms.")
        sys.exit(0)

    print(f"Found {len(pmids)} result(s). Fetching details ...")
    papers = fetch_details(pmids)
    print_results(papers)

    print("\nExtracting structured evidence (rule-based) ...")
    for paper in papers:
        evidence = extract_evidence(paper, biomarker, disease)
        paper.update(evidence)

    csv_filename = f"{biomarker}_{disease}.csv".replace(" ", "_")
    save_csv(papers, csv_filename)


if __name__ == "__main__":
    main()
