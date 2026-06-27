"""
Visual theme for the CSA Program Directory.

Grounded in The 529 Network brand palette. The look is institutional but warm,
matching a tool whose subject is families saving for a child's future. The
display face is a humanist serif (Newsreader) used for headings; the body and
data faces are a clean grotesque (Inter). Everything else stays quiet so the
lifecycle ribbon can be the one memorable element.
"""

# Brand palette
GREEN = "#3A8916"
GREEN_DARK = "#2B650B"
GRAY = "#708686"
ACCENT = "#C6DDBB"
PAPER = "#FBFAF6"
INK = "#22311a"
LINE = "#E4E7DF"


def page_css() -> str:
    return f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;1,6..72,400&family=Inter:wght@400;500;600;700&display=swap');

:root {{
  --green: {GREEN};
  --green-dark: {GREEN_DARK};
  --gray: {GRAY};
  --accent: {ACCENT};
  --paper: {PAPER};
  --ink: {INK};
  --line: {LINE};
}}

html, body, [class*="css"] {{ font-family: 'Inter', system-ui, sans-serif; }}
.stApp {{ background: var(--paper); }}
.block-container {{ padding-top: 2.2rem; max-width: 1180px; }}

h1, h2, h3, .lead {{ font-family: 'Newsreader', Georgia, serif; color: var(--ink); }}
h1 {{ font-weight: 600; letter-spacing: -0.01em; }}
h2 {{ font-weight: 600; }}

/* Masthead */
.masthead {{
  border-bottom: 2px solid var(--green-dark);
  padding-bottom: 14px; margin-bottom: 8px;
}}
.masthead .eyebrow {{
  font-family: 'Inter', sans-serif; font-size: 12px; font-weight: 600;
  letter-spacing: 0.14em; text-transform: uppercase; color: var(--green-dark);
}}
.masthead h1 {{ font-size: 34px; margin: 4px 0 2px 0; }}
.masthead .sub {{ color: var(--gray); font-size: 14.5px; max-width: 720px; }}
.masthead .meta {{
  margin-top: 8px; font-size: 12px; color: var(--gray);
}}
.masthead .meta b {{ color: var(--ink); font-weight: 600; }}

/* Program card */
.card {{
  background: #fff; border: 1px solid var(--line); border-radius: 12px;
  padding: 18px 20px 14px 20px; margin-bottom: 14px;
  box-shadow: 0 1px 2px rgba(34,49,26,0.04);
}}
.card .state {{
  font-family: 'Inter', sans-serif; font-size: 11.5px; font-weight: 700;
  letter-spacing: 0.08em; text-transform: uppercase; color: var(--green-dark);
}}
.card h3 {{ font-size: 22px; margin: 2px 0 6px 0; line-height: 1.1; }}
.card .facts {{ display: flex; flex-wrap: wrap; gap: 8px; margin: 6px 0 12px 0; }}

.chip {{
  display: inline-flex; align-items: center; gap: 5px;
  font-size: 12px; font-weight: 500; color: var(--ink);
  background: #fff; border: 1px solid var(--line);
  border-radius: 999px; padding: 4px 11px;
}}
.chip.solid {{ background: var(--accent); border-color: var(--accent); color: var(--green-dark); font-weight: 600; }}
.chip .k {{ color: var(--gray); }}

.ribbon-title {{
  font-size: 11px; font-weight: 600; letter-spacing: 0.08em;
  text-transform: uppercase; color: var(--gray); margin: 10px 0 18px 0;
}}

/* Profile field rows */
.fieldrow {{ padding: 9px 0; border-bottom: 1px solid var(--line); }}
.fieldrow:last-child {{ border-bottom: none; }}
.fieldrow .label {{
  font-size: 12.5px; font-weight: 600; color: var(--green-dark);
  margin-bottom: 2px;
}}
.fieldrow .value {{ font-size: 14px; color: var(--ink); line-height: 1.45; white-space: pre-line; }}
.fieldrow .value a {{ color: var(--green); word-break: break-word; }}
.fieldrow .empty {{ color: #b3bdb4; font-style: italic; }}

.cat-head {{
  font-family: 'Newsreader', serif; font-size: 18px; font-weight: 600;
  color: var(--ink); margin: 18px 0 2px 0;
  display: flex; align-items: baseline; gap: 10px;
}}
.cat-head .rule {{ flex: 1; height: 1px; background: var(--line); }}

/* Landscape stat tiles */
.tile {{
  background: #fff; border: 1px solid var(--line); border-radius: 12px;
  padding: 16px 18px; height: 100%;
}}
.tile .n {{ font-family: 'Newsreader', serif; font-size: 30px; font-weight: 600; color: var(--green-dark); }}
.tile .l {{ font-size: 12.5px; color: var(--gray); margin-top: 2px; }}

.note {{
  background: #fff; border-left: 3px solid var(--accent);
  padding: 10px 14px; font-size: 13px; color: var(--gray);
  border-radius: 0 8px 8px 0; margin: 6px 0 16px 0;
}}

/* Compare table */
.cmp-section {{
  font-family: 'Newsreader', serif; font-size: 16px; font-weight: 600;
  color: var(--green-dark); margin: 16px 0 4px 0;
}}

a {{ text-decoration: none; }}
.stButton button {{
  background: #fff; border: 1px solid var(--green); color: var(--green-dark);
  border-radius: 8px; font-weight: 600; font-size: 13px;
}}
.stButton button:hover {{ background: var(--accent); border-color: var(--green-dark); color: var(--green-dark); }}

[data-testid="stSidebar"] {{ background: #fff; border-right: 1px solid var(--line); }}
[data-testid="stSidebar"] h2 {{ font-size: 15px; }}
footer {{ visibility: hidden; }}
#MainMenu {{ visibility: hidden; }}
</style>
"""
