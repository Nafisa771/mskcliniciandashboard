import pandas as pd
import streamlit as st
import plotly.express as px
import plost
from pathlib import Path

st.set_page_config(page_title="MSK Clinician Dashboard", layout="wide")
left,right = st.columns([7,3])
with left:  
    st.title("MSK Clinician Dashboard")
with right:
      st.markdown(
        "<div style='text-align:right; font-weight:600;'>👤 Clinician X</div>",
        unsafe_allow_html=True
    )  
st.write ("Welcome to your dashboard")

alertfactors=pd.read_csv("data_alertfactors.csv")
demographics=pd.read_csv("data_demographics.csv")
overallalerts=pd.read_csv("data_overallalerts.csv")
timeseries=pd.read_csv("data_timeseries.csv")

#home page 
st.markdown("""
<style>
/* target each st.metric box */
div[data-testid="stMetric"] > div {
  border: 2px solid #005EB8;      /* blue border */
  border-radius: 14px;
  padding: 12px 10px;
}

/* center the value text */
div[data-testid="stMetric"] [data-testid="stMetricValue"] {
  width: 100%;
  text-align: center;
}

/* center the label text */
div[data-testid="stMetric"] label p {
  width: 100%;
  text-align: center !important;
  margin-bottom: 6px;
}
</style>
""", unsafe_allow_html=True)

col1,col2,col3=st.columns(3)
col1.metric("**Total Patients registered in app**",600)
col2.metric("**Patients in my caseload**",20)
col3.metric("**Patients with high alerts**",6)

charts = st.container()
with charts:
      c1,c2,c3=st.columns(3)

with c1:
    day_col = "day number"
    metric_col = [c for c in timeseries.columns if c.strip().lower()=="logged in"][0]

    if day_col not in timeseries.columns or metric_col not in timeseries.columns:
        st.error("Timeseries must contain 'day number' and 'logged in'."); st.stop()
    timeseries[day_col]    = pd.to_numeric(timeseries[day_col], errors="coerce")
    timeseries[metric_col] = pd.to_numeric(timeseries[metric_col], errors="coerce").fillna(0)
    timeseries = timeseries.dropna(subset=[day_col])

    # aggregate for totals
    week_end_days = [7, 14, 21, 30]
    weekly_totals = (
        timeseries[timeseries[day_col].isin(week_end_days)]
          .groupby(day_col, as_index=False)[metric_col]
          .sum()
          .rename(columns={metric_col: "total_logins"})
          .sort_values(day_col)
    )

    full = pd.DataFrame({day_col: week_end_days})
    weekly_totals = full.merge(weekly_totals, on=day_col, how="left").fillna({"total_logins": 0})

    week_map = {7: "W1", 14: "W2", 21: "W3", 30: "W4"}
    weekly_totals["Week"] = pd.Categorical(
        weekly_totals[day_col].map(week_map),
        ["W1", "W2", "W3", "W4"],
        ordered=True
    )
    # chart only
    fig = px.line(
        weekly_totals, x="Week", y="total_logins",
        markers=True,
        title="Weekly Logins (All Patients)",
        labels={"Week": "Week", "total_logins": "Total logins"},
    )
    
    st.plotly_chart(fig, use_container_width=True)

with c2:
    day_col="day number"
    ex_col="exercises completed"
    if day_col not in timeseries.columns or ex_col not in timeseries.columns:
        st.error("Expected columns 'day number' and 'exercises completed' in timeseries."); st.stop()
        timeseries[day_col] = pd.to_numeric(timeseries[day_col], errors="coerce")
        timeseries[ex_col]  = pd.to_numeric(timeseries[ex_col], errors="coerce").fillna(0)
        timeseries = timeseries.dropna(subset=[day_col])
    # Aggregate 
    week_end_days = [7, 14, 21, 30]
    weekly = (timeseries[timeseries[day_col].isin(week_end_days)]
              .groupby(day_col, as_index=False)[ex_col]
              .sum()
              .rename(columns={ex_col: "weekly_total"})
              .sort_values(day_col))
    full = pd.DataFrame({day_col: week_end_days})
    weekly = (full.merge(weekly, on=day_col, how="left")
                  .fillna({"weekly_total": 0})
                  .sort_values(day_col))
    # 30-day avg and weekly per-day avgs
    total_30 = weekly["weekly_total"].sum()
    avg_per_day_30 = total_30 / 30.0
    weekly["avg_per_day"] = weekly["weekly_total"] / 7.0
    week_map = {7: "W1", 14: "W2", 21: "W3", 30: "W4"}
    weekly["Week"] = weekly[day_col].map(week_map)
    weekly["Week"] = pd.Categorical(weekly["Week"], categories=["W1", "W2", "W3", "W4"], ordered=True)
    
    fig = px.bar(
        weekly,
        x="Week", y="avg_per_day",
        title="Weekly Average Exercises(All Patients)",
        labels={"Week": "Week", "avg_per_day": "Avg exercises per day"},
        )
    st.plotly_chart(fig, use_container_width=True)

with c3:
     day_col = "day number"
     rec_col = "recovery score"
     if day_col not in timeseries.columns or rec_col not in timeseries.columns:
        st.error("Expected columns 'day number' and 'recovery score' in timeseries."); st.stop()
    
     timeseries[day_col] = pd.to_numeric(timeseries[day_col], errors="coerce")
     timeseries[rec_col] = pd.to_numeric(timeseries[rec_col], errors="coerce")
     timeseries = timeseries.dropna(subset=[day_col, rec_col])
     week_end_days = [7, 14, 21, 30]
     avg_recovery = (
    timeseries[timeseries[day_col].isin(week_end_days)]
    .groupby(day_col, as_index=False)[rec_col]
    .mean()
    .rename(columns={rec_col: "avg_recovery"})
    .sort_values(day_col)
    )
     full = pd.DataFrame({day_col: week_end_days})
     avg_recovery = full.merge(avg_recovery, on=day_col, how="left").fillna({"avg_recovery": 0})

     week_map = {7: "W1", 14: "W2", 21: "W3", 30: "W4"}
     avg_recovery["Week"] = avg_recovery[day_col].map(week_map)
     avg_recovery["Week"] = pd.Categorical(avg_recovery["Week"], categories=["W1", "W2", "W3", "W4"], ordered=True)

     fig = px.line(
        avg_recovery,
        x="Week", y="avg_recovery",
        markers=True,
        title="Average Recovery Score Over 30 Days",
        labels={"Week": "Week", "avg_recovery": "Average recovery score"},
    )
   
     st.plotly_chart(fig, use_container_width=True)


# Alerts table (colour-coded)

st.subheader("Alerts — All Patients")

def _load_df(default_df, candidates):
    if 'default_df' in locals() and isinstance(default_df, pd.DataFrame):
        return default_df
    for p in [Path(c) for c in candidates]:
        if p.exists():
            return pd.read_excel(p) if p.suffix.lower()==".xlsx" else pd.read_csv(p)
    return None

try:
    overall_df = overallalerts
except NameError:
    overall_df = _load_df(None, ["data_overallalerts.csv","data/data_overallalerts.csv",
                                 "data_overallalerts.xlsx","data/data_overallalerts.xlsx"])
try:
    demo_df = demographics
except NameError:
    demo_df = _load_df(None, ["data_demographics.csv","data/data_demographics.csv",
                              "data_demographics.xlsx","data/data_demographics.xlsx"])

if overall_df is None:
    st.error("Could not find overall alerts file (data_overallalerts.csv/xlsx).")
    st.stop()

# Normalize headers
alerts = overall_df.copy()
alerts.columns = [c.strip() for c in alerts.columns]
a_norm = {c: c.strip().lower() for c in alerts.columns}
a_inv  = {v: k for k, v in a_norm.items()}

def pick_a(*names, contains=None):
    for n in names:
        if n in a_inv: return a_inv[n]
    if contains:
        for orig, n in a_norm.items():
            if all(s in n for s in contains): return orig
    return None

col_pid   = pick_a("patient id",contains=["patient","id"])
col_name  = pick_a("patient name",contains=["name"])
col_alert = pick_a("overall alert",contains=["alert"])
col_reason= pick_a("overall reason",contains=["reason"])


col_cond = pick_a("condition", contains=["cond"])
if col_cond is None and demo_df is not None:
    demo = demo_df.copy()
    demo.columns = [c.strip() for c in demo.columns]
    d_norm = {c: c.strip().lower() for c in demo.columns}
    d_inv  = {v: k for k, v in d_norm.items()}
    def pick_d(*names, contains=None):
        for n in names:
            if n in d_inv: return d_inv[n]
        if contains:
            for orig, n in d_norm.items():
                if all(s in n for s in contains): return orig
        return None
    d_pid  = pick_d("patient id","patient_id", contains=["patient","id"])
    d_cond = pick_d("condition","msk condition","msk_condition", contains=["cond"])
    if d_pid and d_cond and col_pid:
        alerts = alerts.merge(
            demo[[d_pid, d_cond]].drop_duplicates(),
            left_on=col_pid, right_on=d_pid, how="left"
        )
        col_cond = d_cond

#  Validate required columns
missing = [x for x in [col_name, col_pid, col_cond, col_alert, col_reason] if x is None]
if missing:
    st.error("Missing required columns for the alerts table. "
             "Needed: Patient name, Patient ID, Condition, Overall alert, Overall reason.")
    st.stop()

# Tidy values 
alerts[col_alert] = alerts[col_alert].astype(str).str.strip().str.title() 


table = alerts[[col_name, col_pid, col_cond, col_alert, col_reason]].rename(columns={
    col_name:  "patient name",
    col_pid:   "patient ID",
    col_cond:  "condition",
    col_alert: "alert",
    col_reason:"reason",
}).reset_index(drop=True)


#  add coloured dot to the display text
dot_map = {"Low": "🟢", "Medium": "🟡", "High": "🔴"}
table["alert"] = (
    table["alert"]
      .astype(str).str.strip().str.title()              
      .map(lambda x: f"{dot_map.get(x, '•')} {x}")      
)

# style: bold headers + hide index (no row colouring)
styled = (
    table.style
    .hide(axis="index") 
    .set_table_styles([
        {"selector": "th.col_heading", "props": [("font-weight", "700")]},  # bold headers
    ]
    )
)

# legend
st.markdown("""
<span style="display:inline-block;width:14px;height:14px;background:rgba(16,185,129,.20);border:1px solid #10B981;"></span> Low
&nbsp;&nbsp;
<span style="display:inline-block;width:14px;height:14px;background:rgba(234,179,8,.20);border:1px solid #EAB308;"></span> Medium
&nbsp;&nbsp;
<span style="display:inline-block;width:14px;height:14px;background:rgba(239,68,68,.18);border:1px solid #EF4444;"></span> High
""", unsafe_allow_html=True)

styled = (
    table.style
    .hide(axis="index") 
    .set_table_styles([
        {"selector": "th.col_heading", "props": [("font-weight", "700")]} 
    ])
)


#  Show table
st.dataframe(table, use_container_width=True, height=480, hide_index=True)
