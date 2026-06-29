#!/usr/bin/env python3
"""Recode and merge student incentive tracker files.

The script converts exact check marks (✔) to 1 and exact X values to 0,
exports recoded CSV copies of each source, then performs an outer merge on a
normalized Student ID.
"""

from __future__ import annotations

import csv
import re
import zipfile
import xml.etree.ElementTree as ET
from decimal import Decimal, InvalidOperation
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
XLSX_SOURCE = BASE_DIR / "2025-26 Student Incentive Tracker (1).xlsx"
CSV_SOURCE = BASE_DIR / "Jan-May 2026 Student Incentive Tracker.csv"
XLSX_RECODED = BASE_DIR / "2025-26 Student Incentive Tracker (1) recoded.csv"
CSV_RECODED = BASE_DIR / "Jan-May 2026 Student Incentive Tracker recoded.csv"
MERGED_OUTPUT = BASE_DIR / "student_incentive_tracker_2025_26_jan_may_merged_by_student_id.csv"
LONG_DID_OUTPUT = BASE_DIR / "financial_literacy_did_long.csv"

GRADE_RECODED_FILES = [
    BASE_DIR / "grade_3_financial_literacy_recoded.csv",
    BASE_DIR / "grade_4_financial_literacy_recoded.csv",
    BASE_DIR / "grade_5_financial_literacy_recoded.csv",
]
INCENTIVE_1_PARTICIPATION_COLUMN = "incentive_1_ea_lesson_activities_participation"
INCENTIVE_2_PARTICIPATION_COLUMN = "incentive_2_fin_literacy_module_online_participation"

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def recode_value(value: object) -> str:
    text = "" if value is None else str(value)
    stripped = text.strip()
    if stripped == "✔":
        return "1"
    if stripped == "X":
        return "0"
    return text


def normalize_student_id(value: object) -> str:
    text = "" if value is None else str(value).strip()
    if not text:
        return ""
    try:
        number = Decimal(text)
    except InvalidOperation:
        return re.sub(r"\D", "", text)
    if number == number.to_integral_value():
        return str(int(number))
    return format(number, "f").rstrip("0").rstrip(".")


def column_index(cell_reference: str) -> int:
    letters = re.match(r"[A-Z]+", cell_reference).group(0)
    index = 0
    for letter in letters:
        index = index * 26 + ord(letter) - ord("A") + 1
    return index - 1


def read_xlsx_first_sheet(path: Path) -> list[list[str]]:
    with zipfile.ZipFile(path) as archive:
        shared_strings: list[str] = []
        if "xl/sharedStrings.xml" in archive.namelist():
            root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            for shared_item in root.findall("m:si", NS):
                shared_strings.append(
                    "".join(
                        text_node.text or ""
                        for text_node in shared_item.iter(
                            "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t"
                        )
                    )
                )

        sheet = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))
        rows: list[list[str]] = []
        for row in sheet.findall(".//m:row", NS):
            values: list[str] = []
            for cell in row.findall("m:c", NS):
                idx = column_index(cell.attrib["r"])
                while len(values) <= idx:
                    values.append("")
                value_node = cell.find("m:v", NS)
                value = "" if value_node is None else value_node.text or ""
                if cell.attrib.get("t") == "s" and value:
                    value = shared_strings[int(value)]
                values[idx] = recode_value(value)
            rows.append(values)
    width = max(len(row) for row in rows)
    return [row + [""] * (width - len(row)) for row in rows]


def read_csv(path: Path) -> list[list[str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return [[recode_value(value) for value in row] for row in csv.reader(handle)]


def write_csv(path: Path, rows: list[list[str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        csv.writer(handle).writerows(rows)


def make_unique_headers(header_rows: list[list[str]], source_label: str) -> list[str]:
    section = header_rows[0]
    fields = header_rows[1]
    headers: list[str] = []
    current_section = ""
    counts: dict[str, int] = {}
    for idx, field in enumerate(fields):
        section_text = section[idx].strip() if idx < len(section) else ""
        if section_text:
            current_section = section_text
        field_text = field.strip() or f"Column {idx + 1}"
        header = field_text if idx < 4 or not current_section else f"{current_section} {field_text}"
        header = " ".join(header.split())
        counts[header] = counts.get(header, 0) + 1
        if counts[header] > 1:
            header = f"{header} ({counts[header]})"
        headers.append(header)
    headers.append(f"{source_label} source row")
    return headers


def rows_as_records(rows: list[list[str]], source_label: str) -> tuple[list[str], list[dict[str, str]]]:
    headers = make_unique_headers(rows[:2], source_label)
    records: list[dict[str, str]] = []
    for source_row_number, row in enumerate(rows[2:], start=3):
        if not any(cell.strip() for cell in row):
            continue
        record = {headers[idx]: row[idx] if idx < len(row) else "" for idx in range(len(headers) - 1)}
        record[headers[-1]] = str(source_row_number)
        record["Student ID"] = normalize_student_id(record.get("Student ID", ""))
        if record["Student ID"]:
            records.append(record)
    return headers, records



def incentive_participation_lookup(rows: list[list[str]]) -> dict[str, tuple[str, str]]:
    lookup: dict[str, tuple[str, str]] = {}
    for row in rows[2:]:
        if len(row) < 15:
            continue
        student_id = normalize_student_id(row[2])
        if not student_id:
            continue
        # Source columns are zero-indexed here: E/F are Aug-Dec incentives 1/2,
        # and N/O are Jan-May incentives 1/2.
        incentive_1_values = [row[4].strip(), row[13].strip()]
        incentive_2_values = [row[5].strip(), row[14].strip()]
        lookup[student_id] = (
            "1" if "1" in incentive_1_values else "0",
            "1" if "1" in incentive_2_values else "0",
        )
    return lookup


def update_grade_financial_literacy_files(lookup: dict[str, tuple[str, str]]) -> None:
    for path in GRADE_RECODED_FILES:
        rows = read_csv(path)
        if not rows:
            continue
        header = rows[0]
        for column_name in [INCENTIVE_1_PARTICIPATION_COLUMN, INCENTIVE_2_PARTICIPATION_COLUMN]:
            if column_name not in header:
                header.append(column_name)
        incentive_1_idx = header.index(INCENTIVE_1_PARTICIPATION_COLUMN)
        incentive_2_idx = header.index(INCENTIVE_2_PARTICIPATION_COLUMN)
        student_id_idx = header.index("student_id")

        for row in rows[1:]:
            while len(row) < len(header):
                row.append("")
            student_id = normalize_student_id(row[student_id_idx])
            incentive_1, incentive_2 = lookup.get(student_id, ("0", "0"))
            row[incentive_1_idx] = incentive_1
            row[incentive_2_idx] = incentive_2
        write_csv(path, rows)
        print(f"Updated {path.name}: {len(rows) - 1} retained grade-file students")


def score_summary(record: dict[str, str], prefix: str) -> tuple[str, str, str]:
    recode_values = [
        value.strip()
        for key, value in record.items()
        if key.startswith(f"{prefix}_") and key.endswith("_recode")
    ]
    if not recode_values:
        return "", "", ""
    correct = sum(value == "1" for value in recode_values)
    denominator = len(recode_values)
    return str(correct), str(denominator), f"{100 * correct / denominator:.6f}"


def long_file_columns() -> tuple[list[str], list[str]]:
    control_columns: list[str] = []
    assessment_columns: list[str] = []
    for path in GRADE_RECODED_FILES:
        rows = read_csv(path)
        if not rows:
            continue
        for column in rows[0]:
            if column in {
                "grade",
                "student_id",
                INCENTIVE_1_PARTICIPATION_COLUMN,
                INCENTIVE_2_PARTICIPATION_COLUMN,
            }:
                continue
            if column.startswith("pre_") or column.startswith("post_"):
                generic_column = column.split("_", 1)[1]
                if generic_column not in assessment_columns:
                    assessment_columns.append(generic_column)
            elif column not in control_columns:
                control_columns.append(column)
    return control_columns, assessment_columns


def write_difference_in_differences_long_file() -> None:
    control_columns, assessment_columns = long_file_columns()
    output_header = [
        "Student",
        "student_id_original",
        "Time",
        "Score %",
        "Score correct",
        "Score denominator",
        "Online module",
        "Activities",
        "Grade",
    ] + control_columns + assessment_columns
    output_rows = [output_header]

    for path in GRADE_RECODED_FILES:
        rows = read_csv(path)
        if len(rows) < 2:
            continue
        header = rows[0]
        for row in rows[1:]:
            record = {header[idx]: row[idx] if idx < len(row) else "" for idx in range(len(header))}
            student_id = normalize_student_id(record["student_id"])
            grade = record["grade"]
            online_module = record.get(INCENTIVE_2_PARTICIPATION_COLUMN, "0") or "0"
            activities = record.get(INCENTIVE_1_PARTICIPATION_COLUMN, "0") or "0"
            control_values = [record.get(column, "") for column in control_columns]

            for prefix, time_label in [("pre", "Pre"), ("post", "Post")]:
                correct, denominator, pct = score_summary(record, prefix)
                assessment_values = [record.get(f"{prefix}_{column}", "") for column in assessment_columns]
                output_rows.append([
                    student_id,
                    record["student_id"],
                    time_label,
                    pct,
                    correct,
                    denominator,
                    online_module,
                    activities,
                    grade,
                    *control_values,
                    *assessment_values,
                ])
    write_csv(LONG_DID_OUTPUT, output_rows)
    print(f"Wrote {LONG_DID_OUTPUT.name}: {len(output_rows) - 1} student-time rows")

def merge_records(
    left_headers: list[str],
    left_records: list[dict[str, str]],
    right_headers: list[str],
    right_records: list[dict[str, str]],
) -> list[list[str]]:
    left_lookup = {record["Student ID"]: record for record in left_records}
    right_lookup = {record["Student ID"]: record for record in right_records}
    left_prefixed = ["Student ID"] + [f"2025-26 tracker {h}" for h in left_headers if h != "Student ID"]
    right_prefixed = [f"Jan-May 2026 tracker {h}" for h in right_headers if h != "Student ID"]
    output = [left_prefixed + right_prefixed]
    for student_id in sorted(set(left_lookup) | set(right_lookup), key=lambda x: int(x) if x.isdigit() else x):
        left = left_lookup.get(student_id, {})
        right = right_lookup.get(student_id, {})
        row = [student_id]
        row.extend(left.get(h, "") for h in left_headers if h != "Student ID")
        row.extend(right.get(h, "") for h in right_headers if h != "Student ID")
        output.append(row)
    return output


def main() -> None:
    xlsx_rows = read_xlsx_first_sheet(XLSX_SOURCE)
    csv_rows = read_csv(CSV_SOURCE)
    write_csv(XLSX_RECODED, xlsx_rows)
    write_csv(CSV_RECODED, csv_rows)

    left_headers, left_records = rows_as_records(xlsx_rows, "2025-26 tracker")
    right_headers, right_records = rows_as_records(csv_rows, "Jan-May 2026 tracker")
    write_csv(MERGED_OUTPUT, merge_records(left_headers, left_records, right_headers, right_records))
    update_grade_financial_literacy_files(incentive_participation_lookup(xlsx_rows))
    write_difference_in_differences_long_file()

    print(f"Wrote {XLSX_RECODED.name}: {len(xlsx_rows) - 2} data rows")
    print(f"Wrote {CSV_RECODED.name}: {len(csv_rows) - 2} data rows")
    print(f"Wrote {MERGED_OUTPUT.name}: {len(set(r['Student ID'] for r in left_records) | set(r['Student ID'] for r in right_records))} merged students")


if __name__ == "__main__":
    main()
