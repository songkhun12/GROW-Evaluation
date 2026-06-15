#!/usr/bin/env python3
"""Merge updated at-risk data into grade-level Atlas Excel reports."""
from __future__ import annotations

import html
import posixpath
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

NS_MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
NS_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS_PKG_REL = "http://schemas.openxmlformats.org/package/2006/relationships"
NS = {"a": NS_MAIN, "r": NS_REL, "pr": NS_PKG_REL}

ROOT = Path(__file__).resolve().parent
AT_RISK_FILES = {
    "JES": ROOT / "JES At Risk Report_Updated 6.15.26 (PW_ #JES2026).xlsx",
    "JMTES": ROOT / "JMTES At Risk Report_Updated 6.15.26 (PW_ #MTE2026).xlsx",
}
GRADE_DIRS = ["Kindergarten", "Grade 1", "Grade 2", "Grade 3", "Grade 4", "Grade 5"]


def col_to_idx(cell_ref: str) -> int:
    letters = re.match(r"[A-Z]+", cell_ref or "A").group(0)
    n = 0
    for ch in letters:
        n = n * 26 + ord(ch) - 64
    return n - 1


def shared_strings(zf: zipfile.ZipFile) -> list[str]:
    try:
        root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
    except KeyError:
        return []
    return ["".join(t.text or "" for t in si.findall(".//a:t", NS)) for si in root.findall("a:si", NS)]


def first_sheet_path(zf: zipfile.ZipFile) -> str:
    workbook = ET.fromstring(zf.read("xl/workbook.xml"))
    sheet = workbook.find("a:sheets/a:sheet", NS)
    rid = sheet.attrib[f"{{{NS_REL}}}id"]
    rels = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
    for rel in rels:
        if rel.attrib["Id"] == rid:
            target = rel.attrib["Target"]
            return posixpath.normpath("xl/" + target.lstrip("/"))
    raise ValueError("First worksheet relationship not found")


def read_xlsx(path: Path) -> list[list[str]]:
    with zipfile.ZipFile(path) as zf:
        strings = shared_strings(zf)
        root = ET.fromstring(zf.read(first_sheet_path(zf)))
        rows: list[list[str]] = []
        for row in root.findall(".//a:sheetData/a:row", NS):
            values: list[str] = []
            for cell in row.findall("a:c", NS):
                idx = col_to_idx(cell.attrib.get("r", "A1"))
                while len(values) <= idx:
                    values.append("")
                cell_type = cell.attrib.get("t")
                value_node = cell.find("a:v", NS)
                value = "" if value_node is None else (value_node.text or "")
                if cell_type == "s" and value:
                    value = strings[int(value)]
                elif cell_type == "inlineStr":
                    value = "".join(t.text or "" for t in cell.findall(".//a:t", NS))
                if value.endswith(".0") and value[:-2].isdigit():
                    value = value[:-2]
                values[idx] = value.strip()
            rows.append(values)
        return rows


def find_header(rows: list[list[str]], candidates: set[str]) -> int:
    lowered = {c.lower() for c in candidates}
    for i, row in enumerate(rows[:10]):
        if any(str(cell).strip().lower() in lowered for cell in row):
            return i
    raise ValueError(f"No header found for {candidates}")


def rectangular(rows: list[list[str]]) -> list[list[str]]:
    width = max(len(r) for r in rows) if rows else 0
    return [r + [""] * (width - len(r)) for r in rows]


def table_from_rows(rows: list[list[str]], header_idx: int) -> tuple[list[str], list[list[str]]]:
    rows = rectangular(rows[header_idx:])
    headers = [h.strip() or f"Column {i+1}" for i, h in enumerate(rows[0])]
    return headers, [r for r in rows[1:] if any(str(c).strip() for c in r)]


def build_at_risk_lookup(path: Path) -> tuple[list[str], dict[str, list[str]]]:
    rows = read_xlsx(path)
    header_idx = find_header(rows, {"State Report Id"})
    headers, data = table_from_rows(rows, header_idx)
    id_idx = next(i for i, h in enumerate(headers) if h.lower() == "state report id")
    lookup: dict[str, list[str]] = {}
    for row in data:
        key = row[id_idx].strip()
        if key and key not in lookup:
            lookup[key] = row
    prefixed = [f"At Risk - {h}" for h in headers]
    return prefixed, lookup


def write_xlsx(path: Path, rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    sheet_rows = []
    for r_idx, row in enumerate(rows, start=1):
        cells = []
        for c_idx, value in enumerate(row, start=1):
            col = ""
            n = c_idx
            while n:
                n, rem = divmod(n - 1, 26)
                col = chr(65 + rem) + col
            text = html.escape(str(value), quote=False)
            cells.append(f'<c r="{col}{r_idx}" t="inlineStr"><is><t>{text}</t></is></c>')
        sheet_rows.append(f'<row r="{r_idx}">{"".join(cells)}</row>')
    sheet = f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><worksheet xmlns="{NS_MAIN}" xmlns:r="{NS_REL}"><sheetData>{"".join(sheet_rows)}</sheetData></worksheet>'
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>')
        zf.writestr("_rels/.rels", f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="{NS_PKG_REL}"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>')
        zf.writestr("xl/workbook.xml", f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><workbook xmlns="{NS_MAIN}" xmlns:r="{NS_REL}"><sheets><sheet name="Merged" sheetId="1" r:id="rId1"/></sheets></workbook>')
        zf.writestr("xl/_rels/workbook.xml.rels", f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="{NS_PKG_REL}"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>')
        zf.writestr("xl/worksheets/sheet1.xml", sheet)


def merge_file(atlas_path: Path, at_headers: list[str], at_lookup: dict[str, list[str]]) -> Path:
    rows = read_xlsx(atlas_path)
    header_idx = find_header(rows, {"ID Number", "Student IDs", "Student ID"})
    preamble = rectangular(rows[:header_idx])
    headers, data = table_from_rows(rows, header_idx)
    id_idx = next(i for i, h in enumerate(headers) if h.strip().lower() in {"id number", "student ids", "student id"})
    merged = preamble + [headers + at_headers]
    blanks = [""] * len(at_headers)
    for row in data:
        match = at_lookup.get(row[id_idx].strip())
        merged.append(row + (match if match else blanks))
    out = atlas_path.with_name(atlas_path.stem + " - Merged At Risk.xlsx")
    write_xlsx(out, merged)
    return out


def main() -> None:
    lookups = {school: build_at_risk_lookup(path) for school, path in AT_RISK_FILES.items()}
    outputs = []
    for grade in GRADE_DIRS:
        for atlas_path in sorted((ROOT / grade).glob("*Atlas Report*.xlsx")):
            if "Merged At Risk" in atlas_path.name:
                continue
            school = "JMTES" if atlas_path.name.upper().startswith("JMTES") else "JES"
            outputs.append(merge_file(atlas_path, *lookups[school]))
    print("Created merged files:")
    for out in outputs:
        print(f"- {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
