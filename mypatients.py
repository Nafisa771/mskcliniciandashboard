import streamlit as st
import pandas as pd
import plotly.express as px                                 
import plost
from pathlib import Path
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode


st.set_page_config(page_title="My Patients", layout="wide")

left, right = st.columns([7, 3])
with left:
    st.title("My Patients")
with right:
    st.markdown(
        "<div style='text-align:right; font-weight:600;'>👤 Clinician X</div>",
        unsafe_allow_html=True
    )
    
demographics  = pd.read_csv("data_demographics.csv")
timeseries    = pd.read_csv("data_timeseries.csv")
overallalerts = pd.read_csv("data_overallalerts.csv")
#overview of all patients

st.subheader("Patient List")

demo_view = demographics.copy()
q = st.text_input("Search Patient ID", "", placeholder="Type to filter…")

gob = GridOptionsBuilder.from_dataframe(demo_view)
gob.configure_default_column(sortable=True, filter=False, resizable=True, floatingFilter=False)
gob.configure_pagination(paginationAutoPageSize=False, paginationPageSize=12)
gob.configure_selection(selection_mode="single", use_checkbox=False) 

norm = {c.strip().lower(): c for c in demo_view.columns}
Initial_col = norm.get("Initial score")
if Initial_col:
    gob.configure_column(Initial_col, filter=False, floatingFilter=False, suppressMenu=True, menuTabs=[])
         
# disbabling filter & filter menu for specific columns
gob.configure_column("Age", filter=False, floatingFilter=False,
                     suppressMenu=True)

grid_options = gob.build()

if q:
    grid_options["quickFilterText"] = q

grid_resp = AgGrid(
    demo_view,
    gridOptions=grid_options,
    update_mode=GridUpdateMode.SELECTION_CHANGED,
    allow_unsafe_jscode=True,
    height=420,
    theme="balham",   
)



# Patient drill-down (ANY selected patient) 


import re
import pandas as pd
import plotly.express as px
import streamlit as st

# Normalise AgGrid selection 
def _to_records(x):
    if x is None: return []
    if isinstance(x, list): return x
    if isinstance(x, pd.DataFrame): return x.to_dict("records")
    if isinstance(x, pd.Series): return [x.to_dict()]
    if isinstance(x, dict): return [x]
    return []

grid_resp = grid_resp or {}
sel_rows = _to_records(grid_resp.get("selected_rows"))

if not sel_rows:
    st.info("Select a patient in the table to view their weekly charts (days 7, 14, 21, 30).")
    st.stop()

#  Helpers: column resolver 
def _find_col(df, *aliases):
    cols = {c.strip().lower(): c for c in df.columns}
    for a in aliases:
        k = a.strip().lower()
        if k in cols:
            return cols[k]
    return None

def _norm_name(s: str) -> str:
    s = str(s or "").lower().strip()
    return re.sub(r"[^a-z0-9]+", "", s) 

# Demographics columns
demo_name_col   = _find_col(demographics, "patient name", "patient name (synthetic)", "patient name ", "name")
demo_id_col     = _find_col(demographics, "patient id", "patient id ", "nhs no", "id")
demo_age_col    = _find_col(demographics, "age")
demo_gender_col = _find_col(demographics, "gender", "sex")
demo_cond_col   = _find_col(demographics, "condition", "msk condition")

# Timeseries columns
ts_name_col = _find_col(timeseries, "patient name", "patient name (synthetic)", "patient name ", "name")
ts_id_col   = _find_col(timeseries, "patient id", "patient id ", "nhs no", "id")
day_col     = _find_col(timeseries, "day number", "day", "day_no")
ex_col      = _find_col(timeseries, "exercises completed (weekly)", "exercises completed", "weekly exercises")
rec_col     = _find_col(timeseries, "recovery score", "recovery_score", "score")
login_col   = _find_col(timeseries, "logged in (weekly)", "logged in", "weekly logged in", "logged_in", "login flag", "login", "logins")

# Read selected patient identifiers
sel = pd.Series(sel_rows[0])
sel_name_display = str(sel.get(demo_name_col, "")).strip() if demo_name_col else ""
sel_id_display   = str(sel.get(demo_id_col, "")).strip() if demo_id_col else ""
sel_key          = _norm_name(sel_name_display)

# build normalised key on timeseries & demographics
if not ts_name_col:
    st.error("Couldn't find a 'Patient Name' column in timeseries.")
    st.stop()

ts = timeseries.copy()
ts["_name_key"] = ts[ts_name_col].astype(str).map(_norm_name)

demo = demographics.copy()
if demo_name_col:
    demo["_name_key"] = demo[demo_name_col].astype(str).map(_norm_name)
else:
    demo["_name_key"] = ""

# Prefer NAME 
ts_slice = ts[ts["_name_key"] == sel_key].copy()
if ts_slice.empty and ts_id_col and sel_id_display:
    ts_slice = ts[ts[ts_id_col].astype(str).str.strip() == sel_id_display].copy()

# Keep ONLY weekly checkpoints
if ts_slice.empty or not day_col:
    st.warning("No matching weekly rows (7, 14, 21, 30) found for the selected patient.")
    st.stop()

ts_slice[day_col] = pd.to_numeric(ts_slice[day_col], errors="coerce")
ts_slice = ts_slice[ts_slice[day_col].isin([7, 14, 21, 30])]

value_cols = [c for c in [ex_col, rec_col, login_col] if c and c in ts_slice.columns]
if value_cols:
    ts_slice = ts_slice.groupby([day_col], as_index=False)[value_cols].mean(numeric_only=True)
ts_slice = ts_slice.sort_values(day_col)

# If login was averaged 
if login_col and login_col in ts_slice.columns:
    ts_slice[login_col] = (ts_slice[login_col] >= 0.5).astype(int)

# Header (name/id + quick facts)
demo_row = pd.DataFrame()
if demo_name_col:
    demo_row = demo[demo["_name_key"] == sel_key]

st.markdown("---")
st.subheader(f"Patient panel — {sel_name_display or 'Selected patient'} (Weekly checkpoints)")

c1, c2, c3, c4, c5 = st.columns([2, 1, 1, 2, 2])
with c1:
    st.markdown(f"### {sel_name_display or 'Patient'}")
    if demo_id_col and not demo_row.empty:
        st.caption(f"ID: `{str(demo_row.iloc[0][demo_id_col]).strip()}`")
if not demo_row.empty:
    with c2:
        if demo_age_col in demo_row.columns:
            st.metric("Age", f"{demo_row.iloc[0][demo_age_col]}")
    with c3:
        if demo_gender_col in demo_row.columns:
            st.metric("Gender", f"{demo_row.iloc[0][demo_gender_col]}")
    with c4:
        if demo_cond_col in demo_row.columns:
            st.metric("Condition", f"{demo_row.iloc[0][demo_cond_col]}")
with c5:
    if login_col and login_col in ts_slice.columns:
        weeks_total  = int(ts_slice[day_col].nunique())
        weeks_logged = int(ts_slice[login_col].sum())
        pct = (weeks_logged / weeks_total * 100) if weeks_total else 0
        st.metric("Weekly logins", f"{weeks_logged}/{weeks_total} weeks", f"{pct:.0f}%")

# -- 7) Charts
def _line_weekly(df, y_col, title):
    if not y_col or y_col not in df.columns:
        st.warning(f"Missing column for: {title}")
        return
    fig = px.line(
        df, x=day_col, y=y_col, markers=True,
        labels={day_col: "Day", y_col: title},
        title=title
    )
    fig.update_layout(
        height=320, margin=dict(l=10, r=10, t=40, b=10),
        xaxis=dict(tickmode="array", tickvals=[7, 14, 21, 30], title="Day")
    )
    st.plotly_chart(fig, use_container_width=True)

def _bar_login(df, y_col, title="Weekly login (1=Yes, 0=No)"):
    if not y_col or y_col not in df.columns:
        st.warning("Missing column for weekly login.")
        return
    fig = px.bar(
        df, x=day_col, y=y_col, text=y_col,
        labels={day_col: "Day", y_col: "Logged in (0/1)"},
        title=title
    )
    fig.update_layout(
        height=300, margin=dict(l=10, r=10, t=40, b=10),
        xaxis=dict(tickmode="array", tickvals=[7, 14, 21, 30], title="Day"),
        yaxis=dict(range=[0, 1.1], tickmode="array", tickvals=[0, 1], ticktext=["No", "Yes"])
    )
    fig.update_traces(texttemplate="%{text}", textposition="outside")
    st.plotly_chart(fig, use_container_width=True)

# Layout: two charts on top row, one on bottom row
r1c1, r1c2 = st.columns(2)
with r1c1:
    _line_weekly(ts_slice, ex_col,  "Exercises completed (weekly)")
with r1c2:
    _line_weekly(ts_slice, rec_col, "Recovery score")

r2 = st.container()
with r2:
    _bar_login(ts_slice, login_col, "Logged in this week")

# --- Right-aligned, styled "Send message" button 
_patient_name = sel_name_display or "Selected patient"
_patient_id   = (str(demo_row.iloc[0][demo_id_col]).strip()
                 if (demo_id_col and not demo_row.empty) else "")

# 2) Button with bold black border + black text
st.markdown(f"""
<style>
  /* Scoped styles for the demo button */
  .msg-btn-wrap {{
      display: flex;
      justify-content: flex-end;   /* shove to the right */
      margin-top: .25rem;
  }}
  .msg-btn {{
      background: white;
      color: #000;
      border: 2px solid #000;      /* bold border */
      border-radius: 10px;
      padding: 8px 14px;
      font-weight: 700;
      cursor: pointer;
  }}
  .msg-btn:hover {{
      background: #000;
      color: #fff;                 /* invert on hover */
  }}
</style>
<div class="msg-btn-wrap">
  <button class="msg-btn" onclick="
    const u = new URL(window.location.href);
    u.searchParams.set('msg',  encodeURIComponent('{_patient_name}'));
    u.searchParams.set('pid',  encodeURIComponent('{_patient_id}'));
    window.location.href = u.toString();
  ">Send message to patient</button>
</div>
""", unsafe_allow_html=True)

