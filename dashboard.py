import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# ---------------------------------------------------------
# 1. Page Configuration & Setup
# ---------------------------------------------------------
st.set_page_config(
    page_title="Engineering Velocity Analytics",
    page_icon="⚡",
    layout="wide"
)

EXPORT_DIR = Path("data/export")

# ---------------------------------------------------------
# 2. Data Access Layer with Caching
# ---------------------------------------------------------
@st.cache_data(ttl=3600)
def load_data():
    """
    Connects to an in-memory DuckDB instance to query Parquet files directly.
    Joins the Fact table with Repository and Author dimensions.
    """
    con = duckdb.connect(":memory:")

    fact_path = (EXPORT_DIR / "fact_pull_requests.parquet").as_posix()
    repo_path = (EXPORT_DIR / "dim_repositories.parquet").as_posix()
    author_path = (EXPORT_DIR / "dim_authors.parquet").as_posix()

    query = f"""
    SELECT 
        f.pr_id,
        f.pr_number,
        r.repository_name,
        a.author_username,
        f.pr_state,
        f.created_at,
        f.merged_at,
        f.is_merged,
        f.cycle_time_hours,
        DAYNAME(f.created_at) AS day_created,
        EXTRACT(DOW FROM f.created_at) AS dow_index
    FROM '{fact_path}' f
    JOIN '{repo_path}' r ON f.repository_id = r.repository_id
    JOIN '{author_path}' a ON f.author_id = a.author_id
    """
    df = con.execute(query).df()
    con.close()
    return df

df_raw = load_data()

# ---------------------------------------------------------
# 3. Sidebar Filtering Controls
# ---------------------------------------------------------
st.sidebar.title("⚡ Control Panel")

# Repository selector
available_repos = list(df_raw["repository_name"].unique())
selected_repos = st.sidebar.multiselect(
    "Select Repositories",
    options=available_repos,
    default=available_repos
)

# Outlier threshold slider
max_cycle_observed = float(df_raw["cycle_time_hours"].max(skipna=True) or 200.0)
cap_outliers = st.sidebar.slider(
    "Cap Cycle Time View (Hours)",
    min_value=12.0,
    max_value=max_cycle_observed,
    value=min(max_cycle_observed, 120.0),
    step=6.0,
    help="Excludes extreme long-tail PRs to keep distribution charts interpretable."
)

# Apply reactive filters to DataFrame
df_filtered = df_raw[df_raw["repository_name"].isin(selected_repos)].copy()
df_merged = df_filtered[
    (df_filtered["is_merged"] == True) & 
    (df_filtered["cycle_time_hours"] <= cap_outliers)
].copy()

# ---------------------------------------------------------
# 4. Header & Executive KPIs
# ---------------------------------------------------------
st.title("Engineering Velocity & Contributor Analytics")
st.caption("Benchmarking throughput, code review latency, and maintenance concentration across open-source codebases.")
st.divider()

col1, col2, col3, col4 = st.columns(4)

total_prs = len(df_filtered)
merged_prs = len(df_filtered[df_filtered["is_merged"] == True])
merge_rate = (merged_prs / total_prs * 100) if total_prs > 0 else 0
median_cycle = df_merged["cycle_time_hours"].median() if not df_merged.empty else 0

# Contributor concentration: Top 3 authors' share of merges
top3_share = 0.0
if not df_merged.empty:
    author_counts = df_merged.groupby("author_username").size().sort_values(ascending=False)
    top3_share = (author_counts.head(3).sum() / len(df_merged)) * 100

col1.metric("Total PRs Analyzed", f"{total_prs:,}")
col2.metric("Merge Rate", f"{merge_rate:.1f}%")
col3.metric("Median Cycle Time", f"{median_cycle:.1f} hrs")
col4.metric("Top 3 Contributor Share", f"{top3_share:.1f}%")

st.divider()

# ---------------------------------------------------------
# 5. Visualizations
# ---------------------------------------------------------
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("⏱️ Cycle Time Distribution")
    fig_box = px.box(
        df_merged,
        x="repository_name",
        y="cycle_time_hours",
        color="repository_name",
        points="all",
        hover_data=["pr_number", "author_username"],
        labels={"cycle_time_hours": "Hours to Merge", "repository_name": "Repository"},
        title="Merge Latency Spread"
    )
    fig_box.update_layout(showlegend=False, margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig_box, use_container_width=True)

with col_right:
    st.subheader("👥 Contributor Concentration (Pareto)")
    pareto_fig = go.Figure()

    for repo in selected_repos:
        repo_data = df_merged[df_merged["repository_name"] == repo]
        if repo_data.empty:
            continue
        counts = repo_data.groupby("author_username").size().sort_values(ascending=False).reset_index(name="merges")
        counts["cumulative_pct"] = (counts["merges"].cumsum() / counts["merges"].sum()) * 100
        counts["author_rank"] = range(1, len(counts) + 1)

        pareto_fig.add_trace(go.Scatter(
            x=counts["author_rank"],
            y=counts["cumulative_pct"],
            mode="lines+markers",
            name=repo,
            hovertext=counts["author_username"]
        ))

    pareto_fig.add_hline(y=80, line_dash="dash", line_color="gray", annotation_text="80% Threshold")
    pareto_fig.update_layout(
        xaxis_title="Author Rank (Sorted by Merged PRs)",
        yaxis_title="Cumulative Merged Share (%)",
        yaxis=dict(range=[0, 105]),
        margin=dict(l=20, r=20, t=40, b=20)
    )
    st.plotly_chart(pareto_fig, use_container_width=True)

st.subheader("📅 Activity Intake by Day of Week")
dow_order = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
dow_summary = (
    df_filtered.groupby(["repository_name", "day_created", "dow_index"])
    .agg(opened=("pr_id", "count"))
    .reset_index()
    .sort_values("dow_index")
)

fig_bar = px.bar(
    dow_summary,
    x="day_created",
    y="opened",
    color="repository_name",
    barmode="group",
    category_orders={"day_created": dow_order},
    labels={"day_created": "Day PR Opened", "opened": "PRs Opened"},
    title="Intake Volume Across Weekdays"
)
fig_bar.update_layout(margin=dict(l=20, r=20, t=40, b=20))
st.plotly_chart(fig_bar, use_container_width=True)

# ---------------------------------------------------------
# 6. Audit & Data Inspection
# ---------------------------------------------------------
with st.expander("🔍 Inspect Underlying Dimensional Records"):
    st.dataframe(
        df_filtered[["pr_number", "repository_name", "author_username", "pr_state", "created_at", "merged_at", "cycle_time_hours"]],
        use_container_width=True
    )