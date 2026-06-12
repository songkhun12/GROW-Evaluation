#!/usr/bin/env python3
"""Merge the two JMTES Grade 4 source workbooks in this folder by student ID.

Place the previous-year and current-year JMTES Excel files in this ``Grade 4``
folder, then run this script from anywhere in the repo. The script discovers the
source files from their names, reads the worksheet that contains a Student ID
column, and writes one CSV that keeps every student from either file.
"""
from __future__ import annotations

import csv
import re
import zipfile
from collections import OrderedDict
from pathlib import Path
from xml.etree import ElementTree as ET

GRADE_DIR = Path(__file__).resolve().parent
OUT_CSV = GRADE_DIR / "JMTES Grade 4 Previous Current Merged.csv"

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


def _cell_text(cell: ET.Element, shared_strings: list[str]) -> str:
    if cell.attrib.get("t") == "inlineStr":
        return "".join(t.text or "" for t in cell.findall(".//a:t", NS)).strip()

    value_node = cell.find("a:v", NS)
    if value_node is None:
        return ""

    value = value_node.text or ""
    if cell.attrib.get("t") == "s":
        value = shared_strings[int(value)]
    return value.strip()


def _workbook_sheet_paths(archive: zipfile.ZipFile) -> OrderedDict[str, str]:
    workbook = ET.fromstring(archive.read("xl/workbook.xml"))
    rels = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
    rel_map = {rel.attrib["Id"]: rel.attrib["Target"] for rel in rels}

    sheet_paths: OrderedDict[str, str] = OrderedDict()
    for sheet in workbook.findall("a:sheets/a:sheet", NS):
        rid = sheet.attrib[f"{{{NS_REL}}}id"]
        target = rel_map[rid]
        sheet_paths[sheet.attrib["name"]] = "xl/" + target.lstrip("/") if not target.startswith("xl/") else target
    return sheet_paths


def _read_xlsx_sheet(path: Path, sheet_name: str) -> list[list[str]]:
    with zipfile.ZipFile(path) as archive:
        shared_strings: list[str] = []
        if "xl/sharedStrings.xml" in archive.namelist():
            shared_root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            for item in shared_root.findall("a:si", NS):
                shared_strings.append("".join(t.text or "" for t in item.findall(".//a:t", NS)))

        sheet_paths = _workbook_sheet_paths(archive)
        if sheet_name not in sheet_paths:
            raise ValueError(f"Sheet not found in {path.name}: {sheet_name}")

        sheet_root = ET.fromstring(archive.read(sheet_paths[sheet_name]))
        rows: list[list[str]] = []
        for row in sheet_root.findall("a:sheetData/a:row", NS):
            values: list[str] = []
            for cell in row.findall("a:c", NS):
                col_idx = _column_index(cell.attrib.get("r", "A1"))
                while len(values) <= col_idx:
                    values.append("")
                values[col_idx] = _cell_text(cell, shared_strings)
            rows.append(values)
        return rows


def _sheet_names(path: Path) -> list[str]:
    with zipfile.ZipFile(path) as archive:
        return list(_workbook_sheet_paths(archive).keys())


def _clean_id(raw: str) -> str:
    text = str(raw).strip()
    if not text:
        return ""
    try:
        if "E" in text.upper() or text.endswith(".0"):
            return str(int(float(text)))
    except ValueError:
        pass
    return re.sub(r"\D", "", text) or text


def _clean_header(text: str) -> str:
    text = re.sub(r"\s+", " ", text.replace("\n", " ")).strip()
    return text.replace("Student IDs", "Student ID")


def _student_id_index(row: list[str]) -> int | None:
    for idx, value in enumerate(row):
        if _clean_header(value).lower() == "student id":
            return idx
    return None


def _find_source_files() -> tuple[Path, Path]:
    candidates = [path for path in GRADE_DIR.glob("*.xlsx") if "jmtes" in path.name.lower() and "merged" not in path.name.lower()]
    previous = [path for path in candidates if re.search(r"previous|prev|24-25|2024", path.name, re.IGNORECASE)]
    current = [path for path in candidates if re.search(r"current|curr|25-26|2025", path.name, re.IGNORECASE)]

    if len(previous) == 1 and len(current) == 1 and previous[0] != current[0]:
        return previous[0], current[0]

    found = "\n".join(f"- {path.name}" for path in candidates) or "- none"
    raise FileNotFoundError(
        "Expected exactly one previous-year and one current-year JMTES .xlsx file in Grade 4. "
        "Name them with 'Previous'/'Current' or year markers like '24-25'/'25-26'.\n"
        f"Found JMTES .xlsx candidates in {GRADE_DIR}:\n{found}"
    )


def _make_headers(rows: list[list[str]], header_row_idx: int, prefix: str) -> list[str]:
    subject_row = rows[header_row_idx - 1] if header_row_idx > 0 else []
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


def _extract_dataset(path: Path, prefix: str) -> OrderedDict[str, dict[str, str]]:
    for sheet_name in _sheet_names(path):
        rows = _read_xlsx_sheet(path, sheet_name)
        header_row_idx = next((idx for idx, row in enumerate(rows) if _student_id_index(row) is not None), None)
        if header_row_idx is None:
            continue

        headers = _make_headers(rows, header_row_idx, prefix)
        id_idx = headers.index("Student ID")
        dataset: OrderedDict[str, dict[str, str]] = OrderedDict()
        for row in rows[header_row_idx + 1 :]:
            if id_idx >= len(row):
                continue
            student_id = _clean_id(row[id_idx])
            if not student_id:
                continue
            record: dict[str, str] = {"Student ID": student_id}
            for idx, header in enumerate(headers):
                if not header or header == "Student ID":
                    continue
                value = row[idx].strip() if idx < len(row) else ""
                if header in {"Grade", "Teacher"}:
                    header = f"{prefix} {header}"
                record[header] = value
            if student_id in dataset:
                raise ValueError(f"Duplicate Student ID {student_id} in {path.name} / {sheet_name}")
            dataset[student_id] = record
        if dataset:
            return dataset

    raise ValueError(f"No worksheet with student IDs was found in {path.name}")


def main() -> None:
    previous_file, current_file = _find_source_files()
    previous = _extract_dataset(previous_file, "Previous Year")
    current = _extract_dataset(current_file, "Current Year")

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

    print(f"Previous file: {previous_file.name}")
    print(f"Current file: {current_file.name}")
    print(f"Wrote {OUT_CSV.relative_to(GRADE_DIR.parent)}")
    print(f"Previous rows: {len(previous)}")
    print(f"Current rows: {len(current)}")
    print(f"Merged rows: {len(merged_rows)}")
    for status in ("Both years", "Previous year only", "Current year only"):
        print(f"{status}: {sum(row['Merge Status'] == status for row in merged_rows)}")


if __name__ == "__main__":
    main()
