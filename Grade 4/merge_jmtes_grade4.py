#!/usr/bin/env python3
"""Merge JMTES Grade 4 current-year and previous-year ATLAS sheets by student ID.

This script reads the root workbook ``JMTES ATLAS Report_Updated 5.22.26 (PW_ ATLAS).xlsx``
and performs a full outer join between sheets ``24-25 3rd grade`` and
``25-26 4th grade``. Students present in only one sheet are retained. The merged output is written as CSV so the PR contains no new binary files.
"""
from __future__ import annotations

import csv
import re
import zipfile
from collections import OrderedDict
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "JMTES ATLAS Report_Updated 5.22.26 (PW_ ATLAS).xlsx"
OUT_CSV = Path(__file__).resolve().parent / "JMTES Grade 4 Previous Current Merged.csv"

NS_MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
NS_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS = {"a": NS_MAIN, "r": NS_REL}


def _column_index(cell_ref: str) -> int:
    match = re.match(r"([A-Z]+)", cell_ref)
    if not match:
        return 0
    idx = 0
    for char in match.group(1):
        idx = idx * 26 + ord(char) - 64
    return idx - 1


def _read_xlsx_sheet(path: Path, sheet_name: str) -> list[list[str]]:
    with zipfile.ZipFile(path) as archive:
        shared_strings: list[str] = []
        if "xl/sharedStrings.xml" in archive.namelist():
            shared_root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            for item in shared_root.findall("a:si", NS):
                shared_strings.append("".join(t.text or "" for t in item.findall(".//a:t", NS)))

        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        rels = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        rel_map = {rel.attrib["Id"]: rel.attrib["Target"] for rel in rels}

        sheet_path = None
        for sheet in workbook.findall("a:sheets/a:sheet", NS):
            if sheet.attrib["name"] == sheet_name:
                rid = sheet.attrib[f"{{{NS_REL}}}id"]
                target = rel_map[rid]
                sheet_path = "xl/" + target.lstrip("/") if not target.startswith("xl/") else target
                break
        if sheet_path is None:
            raise ValueError(f"Sheet not found: {sheet_name}")

        sheet_root = ET.fromstring(archive.read(sheet_path))
        rows: list[list[str]] = []
        for row in sheet_root.findall("a:sheetData/a:row", NS):
            values: list[str] = []
            for cell in row.findall("a:c", NS):
                col_idx = _column_index(cell.attrib.get("r", "A1"))
                while len(values) <= col_idx:
                    values.append("")
                value_node = cell.find("a:v", NS)
                value = ""
                if value_node is not None:
                    value = value_node.text or ""
                    if cell.attrib.get("t") == "s":
                        value = shared_strings[int(value)]
                values[col_idx] = value.strip() if isinstance(value, str) else value
            rows.append(values)
        return rows


def _clean_id(raw: str) -> str:
    text = str(raw).strip()
    if not text:
        return ""
    # Excel sometimes stores IDs in scientific notation; this workbook stores IDs as strings,
    # but this guard keeps the merge key stable if the source format changes.
    try:
        if "E" in text.upper() or text.endswith(".0"):
            return str(int(float(text)))
    except ValueError:
        pass
    return re.sub(r"\D", "", text) or text


def _clean_header(text: str) -> str:
    text = re.sub(r"\s+", " ", text.replace("\n", " ")).strip()
    text = text.replace("Student IDs", "Student ID")
    return text


def _make_headers(rows: list[list[str]], subject_row_idx: int, header_row_idx: int, prefix: str) -> list[str]:
    subject_row = rows[subject_row_idx]
    header_row = rows[header_row_idx]
    headers: list[str] = []
    active_subject = ""
    max_cols = max(len(subject_row), len(header_row))
    for idx in range(max_cols):
        subject = _clean_header(subject_row[idx]) if idx < len(subject_row) else ""
        field = _clean_header(header_row[idx]) if idx < len(header_row) else ""
        if subject:
            active_subject = subject
        if not field:
            headers.append("")
        elif field in {"Grade", "Teacher", "Student ID"}:
            headers.append(field)
        elif active_subject:
            headers.append(f"{prefix} {active_subject} {field}")
        else:
            headers.append(f"{prefix} {field}")
    return headers


def _extract_dataset(sheet_name: str, subject_row_idx: int, header_row_idx: int, data_start_idx: int, prefix: str) -> OrderedDict[str, dict[str, str]]:
    rows = _read_xlsx_sheet(SOURCE, sheet_name)
    headers = _make_headers(rows, subject_row_idx, header_row_idx, prefix)
    id_idx = headers.index("Student ID")
    dataset: OrderedDict[str, dict[str, str]] = OrderedDict()
    for row in rows[data_start_idx:]:
        if id_idx >= len(row):
            continue
        student_id = _clean_id(row[id_idx])
        if not student_id:
            continue
        record: dict[str, str] = {"Student ID": student_id}
        for idx, header in enumerate(headers):
            if not header or header == "Student ID":
                continue
            value = row[idx].strip() if idx < len(row) and isinstance(row[idx], str) else (row[idx] if idx < len(row) else "")
            if header in {"Grade", "Teacher"}:
                header = f"{prefix} {header}"
            record[header] = value
        if student_id in dataset:
            raise ValueError(f"Duplicate Student ID {student_id} in {sheet_name}")
        dataset[student_id] = record
    return dataset


def main() -> None:
    previous = _extract_dataset("24-25 3rd grade", subject_row_idx=1, header_row_idx=2, data_start_idx=3, prefix="Previous Year")
    current = _extract_dataset("25-26 4th grade", subject_row_idx=0, header_row_idx=1, data_start_idx=2, prefix="Current Year")

    all_ids = list(OrderedDict.fromkeys([*previous.keys(), *current.keys()]))
    previous_cols = [col for col in next(iter(previous.values())).keys() if col != "Student ID"]
    current_cols = [col for col in next(iter(current.values())).keys() if col != "Student ID"]
    headers = ["Student ID", "Merge Status", *previous_cols, *current_cols]

    merged_rows: list[dict[str, str]] = []
    for student_id in all_ids:
        in_previous = student_id in previous
        in_current = student_id in current
        if in_previous and in_current:
            status = "Both years"
        elif in_previous:
            status = "Previous year only"
        else:
            status = "Current year only"
        row = {"Student ID": student_id, "Merge Status": status}
        row.update(previous.get(student_id, {}))
        row.update(current.get(student_id, {}))
        merged_rows.append(row)

    with OUT_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        writer.writerows(merged_rows)

    status_counts = OrderedDict((status, 0) for status in ("Both years", "Previous year only", "Current year only"))
    for row in merged_rows:
        status_counts[row["Merge Status"]] += 1
    print(f"Wrote {OUT_CSV.relative_to(ROOT)}")
    print(f"Previous rows: {len(previous)}")
    print(f"Current rows: {len(current)}")
    print(f"Merged rows: {len(merged_rows)}")
    for status, count in status_counts.items():
        print(f"{status}: {count}")


if __name__ == "__main__":
    main()
