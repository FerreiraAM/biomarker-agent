"""
Generate a structured evidence summary per biomarker from a CSV produced by fetch_pubmed.py.
Usage:
    python summarize_evidence.py BRCA1_breast_cancer.csv
"""

import csv
import sys
from collections import Counter


def load_csv(filepath: str) -> list[dict]:
    with open(filepath, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def count_field(rows: list[dict], field: str) -> Counter:
    """Count non-empty values for a given field across rows."""
    return Counter(
        r[field].strip()
        for r in rows
        if r.get(field, "").strip()
    )


def top_n(counter: Counter, n: int) -> list[tuple[str, int]]:
    return counter.most_common(n)


def format_inline(counter: Counter) -> str:
    if not counter:
        return "(no data)"
    return " · ".join(
        f"{value} ({count})"
        for value, count in sorted(counter.items(), key=lambda x: -x[1])
    )


def build_synthesis(biomarker: str, total: int, study_types: Counter,
                    classifications: Counter, top_diseases: list[tuple[str, int]]) -> str:
    """
    Build a 2–3 sentence synthesis strictly from the computed statistics.
    No values are invented or inferred beyond what the counters contain.
    """
    sentences = []

    # Sentence 1 — study count and top study type
    if study_types:
        top_type, top_type_n = study_types.most_common(1)[0]
        sentences.append(
            f"{total} studies were identified for {biomarker}, "
            f"with {top_type} being the most common study design ({top_type_n} of {total})."
        )
    else:
        sentences.append(f"{total} studies were identified for {biomarker}.")

    # Sentence 2 — classification
    if classifications:
        top_class, top_class_n = classifications.most_common(1)[0]
        sentences.append(
            f"The biomarker was most frequently classified as {top_class} "
            f"({top_class_n} of {total} studies)."
        )

    # Sentence 3 — top associated diseases
    if top_diseases:
        disease_list = ", ".join(d for d, _ in top_diseases)
        sentences.append(
            f"The most frequently associated disease context(s) were: {disease_list}."
        )

    return " ".join(sentences)


def summarize_biomarker(biomarker: str, rows: list[dict]) -> str:
    total = len(rows)
    study_types = count_field(rows, "study_type")
    classifications = count_field(rows, "biomarker_classification")
    diseases = count_field(rows, "disease")
    top_diseases = top_n(diseases, 3)

    synthesis = build_synthesis(biomarker, total, study_types, classifications, top_diseases)
    directionalities = count_field(rows, "directionality")

    lines = [
        f"🧬 {biomarker} · {total} studies",
        "",
        f"🔬 Study types:      {format_inline(study_types)}",
        f"🏷️  Classification:   {format_inline(classifications)}",
        f"📈 Expression change: {format_inline(directionalities)}",
        f"🦠  Diseases:         {format_inline(Counter(dict(top_diseases)))}",
        "",
        f"💡 {synthesis}",
        "",
    ]

    return "\n".join(lines)


def generate_report(rows: list[dict]) -> str:
    """
    Generate a full evidence report from a list of paper dicts.
    Callable directly without going through a CSV file — used by the Streamlit app.
    """
    groups: dict[str, list[dict]] = {}
    for row in rows:
        biomarker = row.get("biomarker", "").strip()
        if biomarker:
            groups.setdefault(biomarker, []).append(row)

    if not groups:
        return "No biomarker data found."

    sections = [f"{len(groups)} biomarker(s) found\n"]
    for biomarker, biomarker_rows in sorted(groups.items()):
        sections.append(summarize_biomarker(biomarker, biomarker_rows))
    return "\n".join(sections)


def main():
    if len(sys.argv) != 2:
        print("Usage: python summarize_evidence.py <csv_file>")
        print("Example: python summarize_evidence.py BRCA1_breast_cancer.csv")
        sys.exit(1)

    filepath = sys.argv[1]
    rows = load_csv(filepath)

    if not rows:
        print("CSV is empty.")
        sys.exit(0)

    # Group rows by biomarker
    groups: dict[str, list[dict]] = {}
    for row in rows:
        biomarker = row.get("biomarker", "").strip()
        if not biomarker:
            continue
        groups.setdefault(biomarker, []).append(row)

    if not groups:
        print("No biomarker column found or all values are empty.")
        sys.exit(1)

    print(f"\nEvidence Summary Report")
    print(f"Source: {filepath}")
    print(f"Biomarkers found: {len(groups)}\n")

    for biomarker, biomarker_rows in sorted(groups.items()):
        print(summarize_biomarker(biomarker, biomarker_rows))


if __name__ == "__main__":
    main()
