"""
CSA Program Directory
Built for The 529 Network

A reference tool for state Children's Savings Account (CSA) programs. It lets a
user browse every program, read its full design, and compare programs side by
side. Programs are presented factually and never ranked.

Architecture: the workbook in data/ is the single source of truth. The data
firm maintains it; this app reads from it. To publish an update, replace the
file and reboot.
"""

import re
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.loader import load_programs
from utils.lifecycle import ribbon_html, RIBBON_CSS, extract_lifecycle
from utils import theme

st.set_page_config(
    page_title="CSA Program Directory | The 529 Network",
    page_icon="🌱",
    layout="wide",
)

st.markdown(theme.page_css(), unsafe_allow_html=True)
st.markdown(RIBBON_CSS, unsafe_allow_html=True)

DATA_AS_OF = "March 28, 2025"  # date the underlying data reflects
STATE_ABBR = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR",
    "California": "CA", "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE",
    "Florida": "FL", "Georgia": "GA", "Hawaii": "HI", "Idaho": "ID",
    "Illinois": "IL", "Indiana": "IN", "Iowa": "IA", "Kansas": "KS",
    "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME", "Maryland": "MD",
    "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN", "Mississippi": "MS",
    "Missouri": "MO", "Montana": "MT", "Nebraska": "NE", "Nevada": "NV",
    "New Hampshire": "NH", "New Jersey": "NJ", "New Mexico": "NM", "New York": "NY",
    "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK",
    "Oregon": "OR", "Pennsylvania": "PA", "Rhode Island": "RI",
    "South Carolina": "SC", "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX",
    "Utah": "UT", "Vermont": "VT", "Virginia": "VA", "Washington": "WA",
    "West Virginia": "WV", "Wisconsin": "WI", "Wyoming": "WY",
    "District of Columbia": "DC",
}


@st.cache_data(show_spinner=False)
def get_data():
    return load_programs()


DATA = get_data()
PROGRAMS = DATA["programs"]
FIELDS = DATA["fields"]
CATEGORIES = DATA["categories"]

# Data currency is read from the workbook's own "compiled as of" line, so an
# annual refresh needs no code change. Falls back to a constant if absent.
DATA_AS_OF = DATA.get("source_date") or "the latest program submissions"

URL_RE = re.compile(r"(https?://[^\s]+)")
WWW_RE = re.compile(r"\b(www\.[^\s]+\.[^\s]+)")
EMAIL_RE = re.compile(r"([\w.\-+]+@[\w.\-]+\.\w+)")
# Conservative bare-domain match (e.g. "aboutchet.com", "pa529.com/keystone"):
# a host on a common TLD, optionally with a path. Not preceded by @ (email).
BARE_RE = re.compile(
    r"(?<![@\w])((?:[a-z0-9][a-z0-9\-]*\.)+(?:com|org|gov|edu|net)(?:/[^\s]*)?)",
    flags=re.IGNORECASE,
)


def first_url(v):
    """Pull the first real URL out of a value that may mix prose and a link."""
    if is_empty(v):
        return None
    text = str(v)
    m = URL_RE.search(text)
    if m:
        return m.group(1).rstrip(".,);")
    m = WWW_RE.search(text)
    if m:
        return "https://" + m.group(1).rstrip(".,);")
    m = BARE_RE.search(text)
    if m:
        return "https://" + m.group(1).rstrip(".,);")
    return None


def launch_display(p) -> str:
    """
    A compact launch year for the card chip.

    The clean data sometimes gives a two-line value (e.g. a pilot year and a
    statewide year). Prefer the statewide year, else the latest 4-digit year.
    The full value still appears in the program profile.
    """
    raw = p.get("Launch Year")
    if is_empty(raw):
        return ""
    s = str(raw)
    years = re.findall(r"(19|20)\d{2}", s)
    years = [m.group(0) if hasattr(m, "group") else m for m in re.finditer(r"(?:19|20)\d{2}", s)]
    if "statewide" in s.lower():
        m = re.search(r"statewide[^0-9]*((?:19|20)\d{2})", s, flags=re.IGNORECASE)
        if m:
            return m.group(1)
    if years:
        return max(years)
    return s.splitlines()[0].strip()


def has_research(p) -> bool:
    """True when the program reports a research study or evaluation."""
    rc = p.get("Research Conducted")
    if is_empty(rc):
        return False
    s = str(rc).strip().lower()
    if s in {"no", "none", "not yet", "pending"}:
        return False
    # Substantive: a link or a real description, not a bare "no".
    return bool(first_url(rc)) or len(s) > 12


def H(s: str) -> str:
    """
    Normalize an HTML payload for st.markdown.

    Streamlit runs HTML through a markdown parser, which treats any line
    indented four or more spaces as a code block and stops rendering tags.
    Stripping leading whitespace per line keeps the HTML intact. Data values
    that need preserved line breaks use white-space:pre-line in CSS, and their
    newlines live inside a single source line, so this is safe.
    """
    return "\n".join(line.lstrip() for line in s.splitlines() if line.strip() != "")


def base_state(label: str) -> str:
    return str(label).split("(")[0].strip()


def is_empty(v) -> bool:
    return v is None or (isinstance(v, str) and v.strip().lower() in {"", "n/a", "na", "none"})


def fmt_money(v) -> str:
    try:
        return f"${float(v):,.0f}"
    except (TypeError, ValueError):
        return str(v)


def _short_url(u: str) -> str:
    short = u.replace("https://", "").replace("http://", "")
    return short[:54] + "…" if len(short) > 55 else short


# Fields whose numeric values should render as currency in the profile.
MONEY_FIELDS = {
    "Initial Program Deposit",
    "CSA Assets",
    "Amount of Linked 529 Assets",
}


def fmt_value(field: str, v):
    """
    Render a value as display HTML, turning any embedded URLs into links and
    any embedded emails into mailto links. Works whether the value is a bare
    URL, a URL mixed into prose ("STATUTE\nhttps://…"), or plain text.
    """
    if is_empty(v):
        return '<span class="empty">Not provided</span>'
    # Currency fields: show a bare number as $N, but leave explanatory text alone.
    if field in MONEY_FIELDS and isinstance(v, (int, float)):
        return fmt_money(v)
    text = str(v)

    urls = URL_RE.findall(text)
    if not urls:
        m = WWW_RE.search(text)
        if m:
            urls = [m.group(1)]

    if urls:
        # If the value is essentially just the link(s), show clean link chips.
        stripped = text
        for u in urls:
            stripped = stripped.replace(u, "")
        label_fields = ("Link", "Website", "Statute", "Annual Report", "Rules", "Research")
        mostly_link = len(stripped.strip()) <= 12 or any(k in field for k in label_fields)
        if mostly_link:
            parts = []
            for u in urls:
                href = u if u.startswith("http") else f"https://{u}"
                parts.append(f'<a href="{href}" target="_blank" rel="noopener">{_short_url(u)}</a>')
            lead = stripped.strip()
            prefix = f"{lead}<br>" if lead else ""
            return prefix + "<br>".join(parts)
        # URL embedded in longer prose: inline-link it in place.
        for u in urls:
            href = u if u.startswith("http") else f"https://{u}"
            text = text.replace(u, f'<a href="{href}" target="_blank" rel="noopener">{_short_url(u)}</a>')

    text = EMAIL_RE.sub(r'<a href="mailto:\1">\1</a>', text)
    return text


def seed_label(p) -> str:
    dep = p.get("Initial Program Deposit")
    if is_empty(dep):
        return "Seed varies"
    return f"{fmt_money(dep)} seed"


# ---------------------------------------------------------------------------
# Masthead
# ---------------------------------------------------------------------------
def masthead():
    n_programs = len(PROGRAMS)
    n_states = len({base_state(p["State"]) for p in PROGRAMS})
    st.markdown(
        H(f"""
        <div class="masthead">
          <div class="eyebrow">The 529 Network</div>
          <h1>Children's Savings Account Directory</h1>
          <div class="sub">A reference for how state Children's Savings Account programs
          are designed, funded, and delivered to families. Browse each program in full,
          or compare programs side by side.</div>
          <div class="meta">
            <b>{n_programs}</b> programs across <b>{n_states}</b> states &nbsp;·&nbsp;
            Program design reflects data as of <b>{DATA_AS_OF}</b> &nbsp;·&nbsp;
            Submitted by programs, consolidated by The 529 Network
          </div>
        </div>
        """),
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Program card + profile
# ---------------------------------------------------------------------------
# Short, clean label for the "funded at" chip; the raw field can be a sentence.
def _fund_short(p) -> str:
    fund = str(p.get("When is CSA funded for beneficiary?", "")).lower()
    if "birth" in fund:
        return "Birth"
    if "kindergarten" in fund:
        return "Kindergarten"
    if "529" in fund or "opening" in fund:
        return "529 opening"
    return (p.get("When is CSA funded for beneficiary?") or "").split(".")[0][:24]


def program_chips(p) -> str:
    chips = []
    enroll = p.get("Opt-In or Opt-Out?")
    if not is_empty(enroll):
        chips.append(f'<span class="chip solid">{enroll}</span>')
    elig = p.get("Eligibility")
    if not is_empty(elig):
        chips.append(f'<span class="chip">{elig}</span>')
    chips.append(f'<span class="chip"><span class="k">Seed</span> {seed_label(p).replace(" seed","")}</span>')
    fs = _fund_short(p)
    if fs:
        chips.append(f'<span class="chip"><span class="k">Funded at</span> {fs}</span>')
    ly = launch_display(p)
    if ly:
        chips.append(f'<span class="chip"><span class="k">Since</span> {ly}</span>')
    plan = p.get("529 Plan Linked To")
    if not is_empty(plan):
        chips.append(f'<span class="chip"><span class="k">529</span> {plan}</span>')
    if has_research(p):
        chips.append('<span class="chip research">Research available</span>')
    return "".join(chips)


# Quick-access resource links surfaced directly on the card.
LINK_CHIPS = [
    ("Link to Program Website", "Website"),
    ("Annual Report Link", "Annual report"),
    ("Statutory Code / Link to Statute", "Statute"),
    ("Link to Program Rules", "Program rules"),
]


def program_links(p) -> str:
    chips = []
    for field, label in LINK_CHIPS:
        url = first_url(p.get(field))
        if url:
            chips.append(
                f'<a class="linkchip" href="{url}" target="_blank" rel="noopener">'
                f'{label} ↗</a>'
            )
    # Research link, when the study is published online.
    rurl = first_url(p.get("Research Conducted"))
    if rurl:
        chips.append(
            f'<a class="linkchip" href="{rurl}" target="_blank" rel="noopener">Research ↗</a>'
        )
    if not chips:
        return ""
    return '<div class="linkrow">' + "".join(chips) + "</div>"


def render_card(p, idx):
    st.markdown(
        H(f"""
        <div class="card">
          <div class="state">{p['State']}</div>
          <h3>{p.get('Program Name','')}</h3>
          <div class="facts">{program_chips(p)}</div>
          <div class="ribbon-title">Program lifecycle</div>
          {ribbon_html(p)}
          {program_links(p)}
        </div>
        """),
        unsafe_allow_html=True,
    )
    with st.expander("Open full program profile"):
        render_profile(p)


def render_profile(p):
    for cat in CATEGORIES:
        cat_fields = [f["field"] for f in FIELDS if f["category"] == cat]
        # Skip a category only if every field is empty.
        if all(is_empty(p.get(f)) for f in cat_fields):
            continue
        st.markdown(
            f'<div class="cat-head">{cat}<span class="rule"></span></div>',
            unsafe_allow_html=True,
        )
        rows = []
        for f in cat_fields:
            v = p.get(f)
            rows.append(
                f'<div class="fieldrow"><div class="label">{f}</div>'
                f'<div class="value">{fmt_value(f, v)}</div></div>'
            )
        st.markdown("".join(rows), unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------
def view_browse():
    masthead()

    with st.sidebar:
        st.markdown("## Filter programs")
        q = st.text_input("Search by state or program name", "")

        enroll_opts = sorted({p["Opt-In or Opt-Out?"] for p in PROGRAMS if not is_empty(p.get("Opt-In or Opt-Out?"))})
        elig_opts = sorted({p["Eligibility"] for p in PROGRAMS if not is_empty(p.get("Eligibility"))})
        fund_opts = sorted({p["When is CSA funded for beneficiary?"] for p in PROGRAMS if not is_empty(p.get("When is CSA funded for beneficiary?"))})

        f_enroll = st.multiselect("Enrollment", enroll_opts)
        f_elig = st.multiselect("Eligibility", elig_opts)
        f_fund = st.multiselect("Account is funded at", fund_opts)
        f_529 = st.multiselect(
            "529 account required for the seed",
            ["Yes", "No"],
        )

    results = []
    for p in PROGRAMS:
        if q:
            hay = f"{p['State']} {p.get('Program Name','')} {p.get('529 Plan Linked To','')}".lower()
            if q.lower() not in hay:
                continue
        if f_enroll and p.get("Opt-In or Opt-Out?") not in f_enroll:
            continue
        if f_elig and p.get("Eligibility") not in f_elig:
            continue
        if f_fund and p.get("When is CSA funded for beneficiary?") not in f_fund:
            continue
        if f_529:
            req = str(p.get("529 opening required to get CSA deposit?", "")).strip()
            if req not in f_529:
                continue
        results.append(p)

    st.markdown(
        f'<div style="margin:14px 0 4px 0;color:{theme.GRAY};font-size:13px;">'
        f'Showing <b style="color:{theme.INK};">{len(results)}</b> of {len(PROGRAMS)} programs, '
        f'listed alphabetically by state.</div>',
        unsafe_allow_html=True,
    )

    if not results:
        st.markdown(
            '<div class="note">No programs match these filters. Clear a filter to widen the search.</div>',
            unsafe_allow_html=True,
        )
        return

    for i, p in enumerate(results):
        render_card(p, i)


def view_compare():
    masthead()
    st.markdown("## Compare programs")
    st.markdown(
        '<div class="note">Select two or three programs to see their full design side by side. '
        'Programs are shown in the order selected, with no ranking implied.</div>',
        unsafe_allow_html=True,
    )

    labels = [f"{p['State']} — {p.get('Program Name','')}" for p in PROGRAMS]
    label_to_prog = {lab: p for lab, p in zip(labels, PROGRAMS)}
    chosen = st.multiselect("Programs to compare", labels, max_selections=3,
                            default=labels[:2])

    if len(chosen) < 2:
        st.markdown(
            '<div class="note">Pick at least two programs to begin.</div>',
            unsafe_allow_html=True,
        )
        return

    progs = [label_to_prog[c] for c in chosen]

    # Lifecycle ribbons stacked for visual comparison.
    st.markdown('<div class="cat-head">Program lifecycle<span class="rule"></span></div>',
                unsafe_allow_html=True)
    for p in progs:
        st.markdown(
            H(f'<div style="font-size:12px;font-weight:700;color:{theme.GREEN_DARK};'
              f'letter-spacing:0.06em;text-transform:uppercase;margin-top:8px;">{p["State"]}</div>'
              f'{ribbon_html(p)}'),
            unsafe_allow_html=True,
        )

    # Field-by-field table, grouped by category, skipping all-empty rows.
    for cat in CATEGORIES:
        cat_fields = [f["field"] for f in FIELDS if f["category"] == cat]
        rows = {}
        for f in cat_fields:
            vals = [p.get(f) for p in progs]
            if all(is_empty(v) for v in vals):
                continue
            rows[f] = ["Not provided" if is_empty(v) else str(v) for v in vals]
        if not rows:
            continue
        st.markdown(f'<div class="cmp-section">{cat}</div>', unsafe_allow_html=True)
        df = pd.DataFrame(rows, index=[p["State"] for p in progs]).T
        st.dataframe(df, use_container_width=True)


def view_landscape():
    masthead()
    st.markdown("## The landscape")
    st.markdown(
        '<div class="note">A descriptive snapshot of the programs in this directory. '
        'These figures describe the shape of the field. They are not a ranking and do not '
        'compare programs against one another.</div>',
        unsafe_allow_html=True,
    )

    n_programs = len(PROGRAMS)
    n_states = len({base_state(p["State"]) for p in PROGRAMS})
    n_optout = sum(1 for p in PROGRAMS if str(p.get("Opt-In or Opt-Out?", "")).strip() == "Opt-Out")
    n_optin = sum(1 for p in PROGRAMS if str(p.get("Opt-In or Opt-Out?", "")).strip() == "Opt-In")
    n_universal = sum(1 for p in PROGRAMS if str(p.get("Eligibility", "")).strip() == "Universal")
    n_research = sum(1 for p in PROGRAMS if has_research(p))

    cols = st.columns(5)
    tiles = [
        (n_programs, "Programs"),
        (n_states, "States"),
        (f"{n_optout} / {n_optin}", "Opt-out / Opt-in"),
        (n_universal, "Universal"),
        (n_research, "With research"),
    ]
    for col, (n, l) in zip(cols, tiles):
        col.markdown(f'<div class="tile"><div class="n">{n}</div><div class="l">{l}</div></div>',
                     unsafe_allow_html=True)

    # Map of states with a program.
    st.markdown('<div class="cat-head">Where programs operate<span class="rule"></span></div>',
                unsafe_allow_html=True)
    abbrs = sorted({STATE_ABBR.get(base_state(p["State"]), None) for p in PROGRAMS} - {None})
    fig = go.Figure(go.Choropleth(
        locations=abbrs,
        z=[1] * len(abbrs),
        locationmode="USA-states",
        colorscale=[[0, theme.GREEN], [1, theme.GREEN]],
        showscale=False,
        marker_line_color="#ffffff",
        marker_line_width=1.2,
        hovertext=[k for k, v in STATE_ABBR.items() if v in abbrs],
        hoverinfo="text",
    ))
    fig.update_layout(
        geo=dict(scope="usa", lakecolor="rgba(0,0,0,0)", bgcolor="rgba(0,0,0,0)",
                 landcolor="#EDEFE9"),
        margin=dict(l=0, r=0, t=0, b=0), height=340,
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    def _hbar(counts: dict, title: str):
        st.markdown(f'<div class="cat-head">{title}<span class="rule"></span></div>',
                    unsafe_allow_html=True)
        dfc = pd.DataFrame(sorted(counts.items(), key=lambda x: -x[1]),
                           columns=["k", "Programs"])
        bar = go.Figure(go.Bar(
            x=dfc["Programs"], y=dfc["k"], orientation="h",
            marker_color=theme.GREEN, text=dfc["Programs"], textposition="outside",
        ))
        bar.update_layout(
            height=max(160, 54 * len(dfc)),
            margin=dict(l=0, r=20, t=6, b=6),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=False, zeroline=False, visible=False),
            yaxis=dict(autorange="reversed"),
            font=dict(family="Inter", color=theme.INK, size=13),
        )
        st.plotly_chart(bar, use_container_width=True, config={"displayModeBar": False})

    # How programs first fund the account (normalized to the trigger event).
    fund_counts = {}
    for p in PROGRAMS:
        key = _fund_short(p) or "Other"
        fund_counts[key] = fund_counts.get(key, 0) + 1
    _hbar(fund_counts, "How the account is first funded")

    # How funds reach the beneficiary (new clean field this year).
    dist_counts = {}
    for p in PROGRAMS:
        raw = str(p.get("Distribution Method", "")).strip().lower()
        if not raw or raw in {"n/a", "na"}:
            key = "Not specified"
        elif "through 529" in raw or "withdrawal through" in raw:
            key = "Withdrawal through 529"
        elif "request" in raw or "outcome tracker" in raw:
            # Beneficiary-initiated (may also mail a check once requested).
            key = "Beneficiary request"
        elif "check" in raw:
            key = "Check to institution"
        else:
            key = "Other"
        dist_counts[key] = dist_counts.get(key, 0) + 1
    _hbar(dist_counts, "How funds reach the beneficiary")


def view_about():
    masthead()
    st.markdown("## About this directory")
    st.markdown(
        f"""
This directory documents how state Children's Savings Account (CSA) programs are
designed and delivered. It is a reference for treasury staff, program
administrators, researchers, and advocates who need to understand how each
program works, not a tool that rates or ranks programs.

**What a CSA is.** A Children's Savings Account is a savings or investment account,
typically linked to a state 529 plan, that a state opens or seeds for a child to
support future higher education. Programs differ in who is eligible, when the
account is funded, how families engage with it, and how funds are eventually used.

**The data.** Each program's information is submitted by the program and
compiled by AKF Consulting Group for The 529 Network, with funding from the
Charles Stewart Mott Foundation. The program design reflected here is current as
of **{DATA_AS_OF}**. Account and asset figures carry their own "as of" dates,
shown within each program profile.

**Research and evaluation.** Where a program has published research or an
evaluation of its work, it is linked from that program's card and profile, so
the evidence base for each program sits alongside its design.

**How it stays current.** The directory reads directly from a single source
workbook and takes its "as of" date from that file. When programs submit
updates, the workbook is refreshed and the directory reflects the new
information with no other changes needed.

**A note on neutrality.** Programs are listed alphabetically by state and are
never scored or ranked. Comparisons show programs side by side so readers can
see differences in design, not to suggest one program is better than another.
        """
    )
    st.markdown(
        f'<div class="note">Questions about a specific program should go to the contact '
        f'listed in that program\'s profile. Questions about the directory itself can go to '
        f'The 529 Network.</div>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Navigation
# ---------------------------------------------------------------------------
with st.sidebar:
    logo_path = Path(__file__).parent / "assets" / "logo.jpg"
    if logo_path.exists():
        st.image(str(logo_path), use_container_width=True)
        st.markdown(
            f'<div style="font-size:12px;color:{theme.GRAY};margin:6px 0 14px 0;">'
            f'CSA Program Directory</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<div style="font-family:Newsreader,serif;font-size:20px;font-weight:600;'
            f'color:{theme.GREEN_DARK};margin-bottom:2px;">The 529 Network</div>'
            f'<div style="font-size:12px;color:{theme.GRAY};margin-bottom:14px;">CSA Program Directory</div>',
            unsafe_allow_html=True,
        )
    page = st.radio(
        "View",
        ["Browse programs", "Compare programs", "The landscape", "About"],
        label_visibility="collapsed",
    )
    st.markdown("---")

if page == "Browse programs":
    view_browse()
elif page == "Compare programs":
    view_compare()
elif page == "The landscape":
    view_landscape()
else:
    view_about()
