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
                    classifications: Counter, top_diseases: list[tuple[str, int]],
                    directionalities: Counter = None) -> str:
    """
    Build a translational synthesis sentence from the computed statistics.
    No values are invented or inferred beyond what the counters contain.
    """
    disease = top_diseases[0][0] if top_diseases else "the studied disease"
    top_type = study_types.most_common(1)[0][0] if study_types else None

    top_class, top_class_n = classifications.most_common(1)[0] if classifications else (None, 0)
    dominant_class = top_class and (top_class_n / total) >= 0.5 and top_class != "unclear"

    # Directionality signal
    top_dir = directionalities.most_common(1)[0][0] if directionalities else None
    mixed_dir = top_dir == "mixed"
    clear_dir = top_dir and top_dir not in ("none detected", "mixed")

    study_part = f"with evidence derived mainly from {top_type} studies" if top_type else ""
    dir_part = f"showing {top_dir} expression" if clear_dir else ""

    if dominant_class and not mixed_dir:
        sentence = (
            f"The literature primarily supports {biomarker} as a {top_class} biomarker "
            f"in {disease}"
        )
        parts = [p for p in [study_part, dir_part] if p]
        if parts:
            sentence += ", " + " and ".join(parts) + "."
        else:
            sentence += "."
    else:
        heterogeneous_reason = "mixed directionality" if mixed_dir else "no dominant biomarker role"
        sentence = (
            f"The literature on {biomarker} in {disease} is heterogeneous, "
            f"with {heterogeneous_reason} emerging from the current evidence set"
        )
        if study_part:
            sentence += f" ({study_part})."
        else:
            sentence += "."

    return sentence


def summarize_biomarker(biomarker: str, rows: list[dict]) -> str:
    total = len(rows)
    study_types = count_field(rows, "study_type")
    classifications = count_field(rows, "biomarker_classification")
    diseases = count_field(rows, "disease")
    top_diseases = top_n(diseases, 3)

    synthesis = build_synthesis(biomarker, total, study_types, classifications, top_diseases, directionalities)
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
