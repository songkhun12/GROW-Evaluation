#!/usr/bin/env python3
"""Score financial literacy Part A/B pre/post tests from Excel workbooks."""
from __future__ import annotations

import csv
import re
from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET

NS = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
BASE = Path(__file__).resolve().parent


def colnum(ref: str) -> int:
    m = re.match(r"([A-Z]+)", ref)
    n = 0
    for ch in m.group(1):
        n = n * 26 + ord(ch) - 64
    return n


def load_xlsx(path: Path, sheet_index: int = 0):
    """Return rows as values plus parallel rows of bold substrings for each cell."""
    with ZipFile(path) as z:
        shared: list[tuple[str, list[str]]] = []
        if "xl/sharedStrings.xml" in z.namelist():
            root = ET.fromstring(z.read("xl/sharedStrings.xml"))
            for si in root.findall("a:si", NS):
                pieces, bold_pieces = [], []
                runs = si.findall("a:r", NS)
                if runs:
                    for run in runs:
                        text_el = run.find("a:t", NS)
                        text = text_el.text or "" if text_el is not None else ""
                        pieces.append(text)
                        rpr = run.find("a:rPr", NS)
                        if rpr is not None and rpr.find("a:b", NS) is not None:
                            bold_pieces.append(text)
                else:
                    text_el = si.find("a:t", NS)
                    pieces.append(text_el.text or "" if text_el is not None else "")
                shared.append(("".join(pieces), bold_pieces))

        sheet_name = f"xl/worksheets/sheet{sheet_index + 1}.xml"
        root = ET.fromstring(z.read(sheet_name))
        rows, bold_rows = [], []
        for row in root.findall(".//a:row", NS):
            vals, bolds = {}, {}
            for cell in row.findall("a:c", NS):
                cn = colnum(cell.attrib["r"])
                typ = cell.attrib.get("t")
                value, bold = "", []
                if typ == "s":
                    v = cell.find("a:v", NS)
                    if v is not None and v.text is not None:
                        value, bold = shared[int(v.text)]
                elif typ == "inlineStr":
                    is_el = cell.find("a:is", NS)
                    if is_el is not None:
                        value = "".join(t.text or "" for t in is_el.findall(".//a:t", NS))
                else:
                    v = cell.find("a:v", NS)
                    value = v.text or "" if v is not None else ""
                vals[cn], bolds[cn] = value, bold
            if vals:
                mx = max(vals)
                rows.append([vals.get(i, "") for i in range(1, mx + 1)])
                bold_rows.append([bolds.get(i, []) for i in range(1, mx + 1)])
        return rows, bold_rows


def cell(row, idx):
    return row[idx - 1] if idx - 1 < len(row) else ""


def norm_answer(value: str) -> str:
    value = str(value).strip()
    if not value:
        return ""
    try:
        return str(int(float(value)))
    except ValueError:
        m = re.match(r"\s*(\d+)", value)
        return m.group(1) if m else value


def normalize_student_id(value: str) -> str:
    value = str(value).strip()
    if not value:
        return ""
    try:
        return str(int(float(value)))
    except ValueError:
        return re.sub(r"\D", "", value)


def clean_header(value: str) -> str:
    value = re.sub(r"[^0-9A-Za-z]+", "_", str(value).strip().lower()).strip("_")
    return value or "unnamed"


def load_at_risk_report():
    report_path = BASE.parent / "JMTES At Risk Report_Updated 6.15.26 (PW_ #MTE2026).xlsx"
    rows, _ = load_xlsx(report_path, 0)
    header = [str(x).strip() for x in rows[1]]
    safe_headers = [f"at_risk_{clean_header(x)}" for x in header]
    id_idx = header.index("Student Id")
    info_by_id = {}
    for row in rows[2:]:
        student_id = normalize_student_id(cell(row, id_idx + 1))
        if not student_id:
            continue
        info_by_id[student_id] = {
            safe_headers[i]: str(cell(row, i + 1)).strip()
            for i in range(len(header))
            if i != id_idx
        }
    personal_fields = [safe_headers[i] for i in range(len(header)) if i != id_idx]
    return info_by_id, personal_fields


def answers_from_bold(bold_parts: list[str]) -> set[str]:
    text = "\n".join(bold_parts)
    answers = set(re.findall(r"(?m)^\s*(\d+)\s*=", text))
    if not answers:
        raise ValueError(f"Could not identify bold correct answer from {bold_parts!r}")
    return answers


def dont_know_answers(option_text: str) -> set[str]:
    answers = set()
    for line in str(option_text).splitlines():
        if re.search(r"don[’']?t know|not sure", line, flags=re.IGNORECASE):
            m = re.match(r"\s*(\d+)\s*=", line)
            if m:
                answers.add(m.group(1))
    return answers


def get_key(grade: int):
    rows, bolds = load_xlsx(BASE / f"Grade {grade} Codebook.xlsx", 0)
    key = {}
    for row, brow in zip(rows, bolds):
        q = str(cell(row, 2)).strip()
        bold_answer = cell(brow, 4)
        option_text = cell(row, 4)
        if re.fullmatch(r"Q\d+", q) and bold_answer:
            key[q] = {
                "correct": answers_from_bold(bold_answer),
                "dont_know": dont_know_answers(option_text),
            }
    return key


def build_column_map(rows):
    top, section, qs = rows[0], rows[1], rows[2]
    current_test = current_section = None
    mapping = {}
    for i in range(1, max(len(top), len(section), len(qs)) + 1):
        t, s, q = str(cell(top, i)).strip(), str(cell(section, i)).strip(), str(cell(qs, i)).strip()
        if t in {"Pre-Test", "Post-Test"}:
            current_test = "pre" if t == "Pre-Test" else "post"
        if s in {"Section A", "Section B", "Section C"}:
            current_section = s[-1]
        qm = re.match(r"Q\d+", q)
        if current_test and current_section in {"A", "B"} and qm:
            mapping[(current_test, current_section, qm.group(0))] = i
    return mapping


def recode_response(response: str, correct_answers: set[str], dont_know: set[str]) -> str:
    if response in {"", "."}:
        return "."
    if response in correct_answers:
        return "1"
    if response in dont_know:
        return "2"
    return "0"


def score_grade(grade: int, at_risk_by_id: dict[str, dict[str, str]]):
    key = get_key(grade)
    rows, _ = load_xlsx(BASE / f"Grade {grade} Pre_Post Tests (Cleaned_De-Identified).xlsx", 0)
    cmap = build_column_map(rows)
    sections = {q: part for (_test, part, q) in cmap if q in key}
    out_rows, recoded_rows, detail_lines = [], [], [f"# Grade {grade} financial literacy scoring detail", ""]
    detail_lines += ["## Answer key", "", "| Part | Question | Correct answer(s) | Don't know/not sure answer(s) |", "|---|---:|---:|---:|"]
    for q in sorted(sections, key=lambda x: int(x[1:])):
        correct = ", ".join(sorted(key[q]["correct"], key=int))
        dont_know = ", ".join(sorted(key[q]["dont_know"], key=int)) or "None"
        detail_lines.append(f"| {sections[q]} | {q} | {correct} | {dont_know} |")
    detail_lines.append("")

    for row in rows[3:]:
        sid = str(cell(row, 2)).strip()
        consent = str(cell(row, 1)).strip()
        if not sid:
            continue
        match_id = normalize_student_id(sid)
        personal_info = at_risk_by_id.get(match_id, {})
        rec = {"grade": grade, "student_id": sid, "parental_consent": consent, **personal_info}
        recoded = {"grade": grade, "student_id": sid, "parental_consent": consent, **personal_info}
        detail_lines += [f"## Student {sid}", ""]
        if personal_info:
            detail_lines += ["| At-risk report field | Value |", "|---|---|"]
            for field, value in personal_info.items():
                detail_lines.append(f"| {field} | {value} |")
            detail_lines.append("")
        detail_lines += ["| Test | Part | Question | Response | Correct answer(s) | Recode | Score |", "|---|---|---:|---:|---:|---:|---:|"]
        for test in ("pre", "post"):
            test_total = 0
            for part in ("A", "B"):
                part_total = 0
                for q in sorted([x for x, p in sections.items() if p == part], key=lambda x: int(x[1:])):
                    response = norm_answer(cell(row, cmap[(test, part, q)]))
                    correct_answers = key[q]["correct"]
                    code = recode_response(response, correct_answers, key[q]["dont_know"])
                    score = int(code == "1")
                    part_total += score
                    recoded[f"{test}_part_{part}_{q}_response"] = response or "."
                    recoded[f"{test}_part_{part}_{q}_recode"] = code
                    correct = ", ".join(sorted(correct_answers, key=int))
                    detail_lines.append(f"| {test} | {part} | {q} | {response or 'Missing'} | {correct} | {code} | {score} |")
                rec[f"{test}_part_{part}_correct"] = part_total
                test_total += part_total
            rec[f"{test}_total_correct"] = test_total
        out_rows.append(rec)
        recoded_rows.append(recoded)
        detail_lines.append("")
    return out_rows, recoded_rows, "\n".join(detail_lines)


def main():
    combined = []
    at_risk_by_id, personal_fields = load_at_risk_report()
    fields = [
        "grade", "student_id", "parental_consent", *personal_fields,
        "pre_part_A_correct", "pre_part_B_correct", "pre_total_correct",
        "post_part_A_correct", "post_part_B_correct", "post_total_correct",
    ]
    detail_documents = []
    for grade in (3, 4, 5):
        rows, recoded_rows, detail = score_grade(grade, at_risk_by_id)
        combined.extend(rows)
        detail_documents.append(detail)
        with (BASE / f"grade_{grade}_financial_literacy_scores.csv").open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader(); writer.writerows(rows)
        if recoded_rows:
            recoded_fields = list(recoded_rows[0])
            with (BASE / f"grade_{grade}_financial_literacy_recoded.csv").open("w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=recoded_fields)
                writer.writeheader(); writer.writerows(recoded_rows)
        (BASE / f"grade_{grade}_financial_literacy_scoring_detail.md").write_text(detail + "\n")
    with (BASE / "all_grades_financial_literacy_scores.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader(); writer.writerows(combined)
    (BASE / "financial_literacy_scoring_detail.md").write_text("\n".join(detail_documents) + "\n")


if __name__ == "__main__":
    main()
