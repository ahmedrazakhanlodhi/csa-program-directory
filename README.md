# CSA Program Directory

A reference web tool for state Children's Savings Account (CSA) programs, built
for The 529 Network. It lets anyone browse every program in full, compare
programs side by side, and see the shape of the field at a glance. Programs are
presented factually and are never scored or ranked.

Live structure: a Streamlit app that reads from a single source workbook. The
data firm maintains the workbook; the app is the display layer.

## What it does

- **Browse programs.** Every program as a card with key facts and a lifecycle
  ribbon. Filter by enrollment type, eligibility, funding trigger, and whether a
  529 account is required. Open any card for the full profile across all six
  field categories.
- **Compare programs.** Pick two or three programs and see their full design side
  by side, grouped by category, with lifecycle ribbons stacked for visual
  comparison.
- **The landscape.** A descriptive snapshot: how programs enroll, where they
  operate, and how they fund the account. Descriptive only, never a ranking.
- **About.** What a CSA is, where the data comes from, and how the directory
  stays current.

## The signature element: the lifecycle ribbon

Every CSA is built around a child's timeline. The ribbon shows three anchors for
each program on a single age scale from 0 to 30: when the account is seeded
(birth, kindergarten, or 529 account opening), when it can be used, and when it
forfeits if unclaimed. It is descriptive, not evaluative.

## Architecture

```
app.py                     Main app: navigation and the four views
utils/loader.py            Reads and normalizes the source workbook
utils/lifecycle.py         Lifecycle extraction and the ribbon renderer
utils/theme.py             Brand palette and CSS
data/CSA_Database.xlsx     The single source of truth (maintained by the firm)
requirements.txt
```

The loader auto-detects the header row and category band inside the workbook's
Data sheet, so a future delivery from the firm can be dropped in without code
changes as long as the column layout holds.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy (Streamlit Community Cloud)

1. Push this folder to a GitHub repository.
2. On Streamlit Community Cloud, create a new app pointing at `app.py`.
3. No secrets or API keys are required.

## Update the data

1. Replace `data/CSA_Database.xlsx` with the firm's latest delivery.
2. Reboot the app. The cache clears on reboot and the new data loads.

That is the whole process. The app reads the "as of" date, the field list,
the six categories, and every program from the workbook itself, so a new
annual file with added columns needs no code change. The loader auto-detects
the header row and category band, and new fields appear in each program's
profile automatically. (The 2026 file added ~11 fields — annual report links,
legislation year, distribution detail, investment option, and research links —
with no edits to the app.)

## Notes for collaborators

- All user-facing strings describe the data as submitted by programs and
  consolidated by The 529 Network.
- Branding (title, colors, attribution) lives entirely in the app, so the data
  file can keep whatever internal naming the firm uses.
- Neutrality is intentional and structural: programs are listed alphabetically,
  comparisons never imply ranking, and the landscape view is labeled as
  descriptive.
