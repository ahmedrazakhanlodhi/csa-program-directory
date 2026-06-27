"""
The lifecycle ribbon: the directory's signature element.

Every CSA program is built around a child's timeline. An account is seeded at a
trigger event (birth, kindergarten, or 529 account opening), becomes available
to use around college age, and forfeits if unclaimed by a set age. This module
reads those three anchors from a program record and renders them as a clean
horizontal ribbon spanning ages 0 to 30.

The ribbon is descriptive, never evaluative. It shows how a program is shaped
over a child's life, not whether one program is better than another.
"""

from __future__ import annotations

import re

# Brand palette (The 529 Network).
GREEN = "#3A8916"
GREEN_DARK = "#2B650B"
GRAY = "#708686"
ACCENT = "#C6DDBB"
INK = "#22311a"

RIBBON_MAX_AGE = 30


HS_GRAD_AGE = 18  # standard age at high school graduation, used for relative phrasing


def _explicit_age(text) -> int | None:
    """Pull an explicit 'Age N' value from a field."""
    if text is None:
        return None
    m = re.search(r"age\s*(\d{1,2})", str(text), flags=re.IGNORECASE)
    return int(m.group(1)) if m else None


def _resolve_age(text) -> int | None:
    """
    Resolve a distribution or forfeiture age from free text.

    Handles explicit ages ("Age 26"), relative phrasing
    ("6 years after high school graduation" -> 18 + 6), and the
    "after high school" shorthand. Returns None when no age gate applies
    (for example, "at account owner's discretion").
    """
    if text is None:
        return None
    s = str(text).lower()

    explicit = _explicit_age(s)
    if explicit is not None:
        return explicit

    m = re.search(r"(\d{1,2})\s*years?\s*after\s*high\s*school", s)
    if m:
        return HS_GRAD_AGE + int(m.group(1))

    if "after high school" in s or "high school graduation" in s:
        return HS_GRAD_AGE

    return None


def extract_lifecycle(program: dict) -> dict:
    """Return the three timeline anchors plus human-readable labels."""
    funded_when = program.get("When is CSA funded for beneficiary?") or ""
    dist_start = program.get("When can beneficiary start taking Distributions?") or ""
    forfeit = program.get("When do CSA assets become forfeited if not claimed?") or ""
    opt_timing = program.get("Opt-In Timing") or ""

    funded_when_l = str(funded_when).lower()
    if "birth" in funded_when_l:
        fund_age, fund_label = 0, "Seeded at birth"
    elif "kindergarten" in funded_when_l:
        fund_age, fund_label = 5, "Seeded at kindergarten"
    elif "529" in funded_when_l:
        # Event-based: anchor at the opt-in deadline if one is given.
        opt_age = _explicit_age(opt_timing)
        if opt_age is None and "age 1" in str(opt_timing).lower():
            opt_age = 1
        fund_age = opt_age
        fund_label = "Seeded when 529 is opened"
    else:
        fund_age, fund_label = None, str(funded_when) or "Funding varies"

    # Distribution: None means usable without an age gate (owner's discretion).
    dl = str(dist_start).lower()
    if "discretion" in dl or "any age" in dl:
        dist_age = None
    else:
        dist_age = _resolve_age(dist_start)
    dist_label = str(dist_start) if dist_start else "Not specified"

    forfeit_l = str(forfeit).lower()
    if "never" in forfeit_l:
        forfeit_age, forfeit_label = None, "No forfeiture"
        never_forfeit = True
    else:
        forfeit_age = _resolve_age(forfeit)
        forfeit_label = str(forfeit) if forfeit else "Not specified"
        never_forfeit = False

    return {
        "fund_age": fund_age,
        "fund_label": fund_label,
        "dist_age": dist_age,
        "dist_label": dist_label,
        "forfeit_age": forfeit_age,
        "forfeit_label": forfeit_label,
        "never_forfeit": never_forfeit,
    }


def _pct(age: int) -> float:
    return max(0.0, min(100.0, (age / RIBBON_MAX_AGE) * 100.0))


def ribbon_html(program: dict, compact: bool = False) -> str:
    """Render the lifecycle ribbon as a self-contained HTML block."""
    lc = extract_lifecycle(program)
    height = 64 if compact else 92
    track_y = 30 if compact else 40

    markers = []

    def add_marker(age, label, color, glyph):
        if age is None:
            return
        left = _pct(age)
        # Keep end labels from clipping the edges.
        align = "center"
        shift = "-50%"
        if left < 8:
            align, shift = "left", "0"
        elif left > 92:
            align, shift = "right", "-100%"
        label_html = "" if compact else (
            f'<div class="lc-label" style="transform:translateX({shift});text-align:{align};">'
            f'<span class="lc-age">Age {age}</span><span class="lc-cap">{label}</span></div>'
        )
        markers.append(
            f'<div class="lc-marker" style="left:{left:.2f}%;">'
            f'<div class="lc-dot" style="background:{color};">{glyph}</div>'
            f'{label_html}</div>'
        )

    # Funding point
    if lc["fund_age"] is not None:
        add_marker(lc["fund_age"], lc["fund_label"], GREEN_DARK, "")
    # Distribution-eligible point
    if lc["dist_age"] is not None:
        add_marker(lc["dist_age"], "Can be used", GREEN, "")
    # Forfeiture point
    if not lc["never_forfeit"] and lc["forfeit_age"] is not None:
        add_marker(lc["forfeit_age"], "Forfeits if unclaimed", GRAY, "")

    # The filled span runs from funding to the last meaningful anchor.
    fill_start = _pct(lc["fund_age"]) if lc["fund_age"] is not None else 0
    if lc["never_forfeit"]:
        fill_end = 100
        tail = (
            f'<div class="lc-arrow" style="left:100%;">→</div>'
            if not compact else ""
        )
    else:
        end_age = lc["forfeit_age"] or lc["dist_age"] or RIBBON_MAX_AGE
        fill_end = _pct(end_age)
        tail = ""
    fill_w = max(0, fill_end - fill_start)

    never_note = ""
    if lc["never_forfeit"] and not compact:
        never_note = '<div class="lc-never">Funds remain available with no forfeiture age</div>'

    html = f"""
    <div class="lc-wrap" style="height:{height}px;">
      <div class="lc-track" style="top:{track_y}px;">
        <div class="lc-fill" style="left:{fill_start:.2f}%;width:{fill_w:.2f}%;"></div>
        {tail}
      </div>
      {''.join(markers)}
      {never_note}
    </div>
    """
    # Strip per-line indentation so Streamlit's markdown parser does not treat
    # the block as code and render the closing tags as literal text.
    return "\n".join(line.lstrip() for line in html.splitlines() if line.strip())


RIBBON_CSS = f"""
<style>
.lc-wrap {{ position: relative; width: 100%; margin: 4px 0 2px 0; }}
.lc-track {{
  position: absolute; left: 0; right: 0; height: 6px;
  background: {ACCENT}; border-radius: 6px; opacity: 0.55;
}}
.lc-fill {{
  position: absolute; top: 0; height: 6px; border-radius: 6px;
  background: linear-gradient(90deg, {GREEN_DARK}, {GREEN});
}}
.lc-arrow {{
  position: absolute; top: -8px; color: {GREEN}; font-weight: 700; font-size: 16px;
  transform: translateX(2px);
}}
.lc-marker {{ position: absolute; top: 0; }}
.lc-dot {{
  position: absolute; top: 22px; width: 14px; height: 14px; border-radius: 50%;
  transform: translate(-50%, 0); border: 2px solid #fff;
  box-shadow: 0 1px 3px rgba(0,0,0,0.18);
}}
.lc-label {{
  position: absolute; top: 44px; left: 0; width: 150px; line-height: 1.15;
}}
.lc-age {{ display:block; font-weight: 700; font-size: 11px; color: {INK}; }}
.lc-cap {{ display:block; font-size: 10.5px; color: {GRAY}; }}
.lc-ticks {{ position: absolute; left: 0; right: 0; height: 12px; }}
.lc-tick {{
  position: absolute; transform: translateX(-50%); font-size: 9.5px;
  color: #9aa8a0; top: 0;
}}
.lc-never {{
  position: absolute; right: 0; top: 2px; font-size: 10.5px; color: {GRAY};
  font-style: italic;
}}
</style>
"""
