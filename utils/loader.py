"""
Data loader for the CSA Program Directory.

Reads the source workbook delivered by the data firm and normalizes it into a
clean structure the app can render. The workbook is the single source of truth.
To update the directory, replace the file in data/ and reboot. No code changes
are needed as long as the column structure holds.

The loader auto-detects the header row (the row containing both "State" and
"Program Name") and the category band directly above it, so small layout shifts
in future deliveries will not break it.
"""

from __future__ import annotations

import datetime
from pathlib import Path

import openpyxl

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "CSA_Database.xlsx"

# The data sheet inside the workbook. The firm's file names it "Data".
DATA_SHEET = "Data"

# Identity fields that are never grouped under a thematic category.
IDENTITY_FIELDS = {"State", "Program Name"}

# Category band labels as the firm wrote them, mapped to clean display names.
CATEGORY_DISPLAY = {
    "Program Mechanics": "Program Mechanics",
    "Administration": "Administration",
    "Funding and Engagement": "Funding and Engagement",
    "Distribution Phase": "Distribution Phase",
    "Program Statistics": "Program Statistics",
    "Other": "Other",
}


def _clean(value):
    """Normalize a single cell value for display."""
    if value is None:
        return None
    if isinstance(value, datetime.datetime):
        return value.strftime("%B %d, %Y")
    if isinstance(value, float):
        # Keep whole numbers clean (Launch Year, counts) but preserve cents.
        if value.is_integer():
            return int(value)
        return value
    if isinstance(value, str):
        text = value.strip()
        return text if text else None
    return value


def _find_header_row(ws, max_scan: int = 30):
    """Locate the row that holds the field names."""
    for r in range(1, max_scan + 1):
        values = {
            str(ws.cell(row=r, column=c).value).strip()
            for c in range(1, ws.max_column + 1)
            if ws.cell(row=r, column=c).value is not None
        }
        if "State" in values and "Program Name" in values:
            return r
    raise ValueError("Could not locate the header row in the data sheet.")


def _build_category_map(ws, header_row: int):
    """
    Map each column to its category using the band row above the header.

    The band row holds a label only at the first column of each category block;
    every column inherits the most recent label to its left.
    """
    band_row = header_row - 2  # firm places the band two rows above the header
    anchors = {}
    for c in range(1, ws.max_column + 1):
        v = ws.cell(row=band_row, column=c).value
        if v:
            anchors[c] = str(v).strip()
    sorted_cols = sorted(anchors)

    def category_for(col: int):
        chosen = None
        for anchor in sorted_cols:
            if col >= anchor:
                chosen = anchors[anchor]
        return CATEGORY_DISPLAY.get(chosen, chosen)

    return category_for


def load_programs(path: Path | None = None) -> dict:
    """
    Load the directory.

    Returns a dict with:
      - "programs": list of program dicts (ordered fields preserved)
      - "fields":   list of {field, category} in workbook order
      - "categories": ordered list of category names (excluding Identity)
      - "source_date": the firm's compile date string if present, else None
    """
    path = Path(path) if path else DATA_FILE
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb[DATA_SHEET] if DATA_SHEET in wb.sheetnames else wb.worksheets[0]

    header_row = _find_header_row(ws)
    category_for = _build_category_map(ws, header_row)

    # Read field names and their categories, in column order.
    fields = []
    col_for_field = {}
    for c in range(1, ws.max_column + 1):
        name = ws.cell(row=header_row, column=c).value
        if name is None:
            continue
        name = str(name).strip()
        if not name or name in {"Definitions"}:
            continue
        category = "Identity" if name in IDENTITY_FIELDS else category_for(c)
        fields.append({"field": name, "category": category})
        col_for_field[name] = c

    # Read program rows until we hit a row with no State value.
    programs = []
    r = header_row + 1
    # Skip an embedded "definitions" row if the firm placed one right below.
    first_cell = ws.cell(row=r, column=col_for_field["State"]).value
    if isinstance(first_cell, str) and first_cell.strip().lower().startswith("definition"):
        r += 1

    while r <= ws.max_row:
        state_val = ws.cell(row=r, column=col_for_field["State"]).value
        if state_val is None or str(state_val).strip() == "":
            r += 1
            # Stop once we pass the contiguous block of programs.
            if r > header_row + 60:
                break
            continue
        record = {}
        for f in fields:
            record[f["field"]] = _clean(ws.cell(row=r, column=col_for_field[f["field"]]).value)
        programs.append(record)
        r += 1

    categories = []
    for f in fields:
        if f["category"] not in categories and f["category"] != "Identity":
            categories.append(f["category"])

    # Pull the firm's compile date from the title block if present.
    source_date = None
    for rr in range(1, header_row):
        for cc in range(1, 4):
            v = ws.cell(row=rr, column=cc).value
            if isinstance(v, str) and "as of" in v.lower():
                source_date = v.split("as of")[-1].strip().rstrip(".")
                break

    return {
        "programs": programs,
        "fields": fields,
        "categories": categories,
        "source_date": source_date,
    }
