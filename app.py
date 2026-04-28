import streamlit as st
import pandas as pd
import plotly.express as px

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Renewable Natural Capital Dashboard",
    layout="wide"
)

# ── CSS Styling ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    .block-container { padding: 2rem 2.5rem; }
    h1 { color: #4CAF50; font-size: 2rem; font-weight: 700; }
    h2, h3 { color: #4CAF50; }
    div[data-testid="metric-container"] {
        background-color: #1e2130;
        border-left: 5px solid #4CAF50;
        border-radius: 8px;
        padding: 15px 20px;
        box-shadow: 0 1px 6px rgba(0,0,0,0.4);
    }
    section[data-testid="stSidebar"] {
        background-color: #161b27;
    }
    section[data-testid="stSidebar"] * {
        color: white !important;
    }
    hr { border: 1px solid #2e3347; margin: 1.2rem 0; }
</style>
""", unsafe_allow_html=True)

# ── Load & Process Data ───────────────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_csv("Data/Renewable Natural Capital.csv")

    # Total renewable capital per capita
    total = df[
        (df["COMP_BREAKDOWN_1_LABEL"] == "Aggregation: per capita") &
        (df["COMP_BREAKDOWN_2_LABEL"] == "Renewable capital: total")
    ][["REF_AREA_LABEL", "TIME_PERIOD", "OBS_VALUE"]].dropna()
    total.columns = ["Country", "Year", "Capital_USD"]
    total["Year"] = total["Year"].astype(int)

    # Breakdown by capital type
    breakdown = df[
        (df["COMP_BREAKDOWN_1_LABEL"] == "Aggregation: per capita") &
        (df["COMP_BREAKDOWN_2_LABEL"] != "Renewable capital: total")
    ][["REF_AREA_LABEL", "TIME_PERIOD", "COMP_BREAKDOWN_2_LABEL", "OBS_VALUE"]].dropna()
    breakdown.columns = ["Country", "Year", "Category", "Value_USD"]
    breakdown["Category"] = breakdown["Category"].str.replace("Renewable capital: ", "", regex=False)
    breakdown["Year"] = breakdown["Year"].astype(int)

    # Total (not per capita) for aggregate comparison
    total_agg = df[
        (df["COMP_BREAKDOWN_1_LABEL"] == "Aggregation: total") &
        (df["COMP_BREAKDOWN_2_LABEL"] == "Renewable capital: total")
    ][["REF_AREA_LABEL", "TIME_PERIOD", "OBS_VALUE"]].dropna()
    total_agg.columns = ["Country", "Year", "Total_Capital"]
    total_agg["Year"] = total_agg["Year"].astype(int)

    return total, breakdown, total_agg

total, breakdown, total_agg = load_data()

all_countries = sorted(total["Country"].unique())
all_years = sorted(total["Year"].unique())
all_categories = sorted(breakdown["Category"].unique())

# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.title("Dashboard Filters")
st.sidebar.markdown("---")

selected_countries = st.sidebar.multiselect(
    "Countries (Trend & Comparison)",
    options=all_countries,
    default=["United Kingdom", "China", "United States", "India", "Brazil", "Australia"]
)

year_range = st.sidebar.slider(
    "Year Range",
    min_value=1995, max_value=2020,
    value=(1995, 2020)
)

selected_year = st.sidebar.selectbox(
    "Select Year (applies to all charts)",
    options=sorted(all_years, reverse=True)
)

pie_country = st.sidebar.selectbox(
    "Country (Capital Breakdown Pie)",
    options=all_countries,
    index=all_countries.index("United Kingdom") if "United Kingdom" in all_countries else 0
)
category_filter = st.sidebar.selectbox(
    "Capital Category (Category Trend)",
    options=all_categories,
    index=all_categories.index("timber") if "timber" in all_categories else 0
)

st.sidebar.markdown("---")
st.sidebar.markdown("**Dataset:** World Bank CWON")
st.sidebar.markdown("**Module:** 5DATA004C")
st.sidebar.markdown("**Student:** Enuri Vidasunee")

# ── Page Header ───────────────────────────────────────────────────────────────
st.title("Renewable Natural Capital Dashboard")
st.markdown(
    "Exploring how renewable natural wealth (timber, fisheries, agricultural land, hydropower, and more) "
    "is distributed across 151 countries from 1995 to 2020. Data source: World Bank Changing Wealth of Nations (CWON)."
)
st.markdown("---")

# ── KPI Metrics ───────────────────────────────────────────────────────────────
latest = total[total["Year"] == 2020]
earliest = total[total["Year"] == 1995]
global_avg_2020 = latest["Capital_USD"].mean()
global_avg_1995 = earliest["Capital_USD"].mean()
top_country = latest.loc[latest["Capital_USD"].idxmax(), "Country"]
top_value = latest["Capital_USD"].max()

k1, k2, k3, k4 = st.columns(4)
k1.metric("Countries Tracked", "151")
k2.metric("Years of Data", "1995 — 2020")
k3.metric("Top Country (2020)", top_country, f"${top_value:,.0f} per capita")
k4.metric("Global Avg (2020)", f"${global_avg_2020:,.0f}", f"+${global_avg_2020 - global_avg_1995:,.0f} since 1995")

st.markdown("---")

# ── Chart 1: World Map ────────────────────────────────────────────────────────
st.subheader("Global Distribution of Renewable Natural Capital")
st.markdown(f"Showing renewable capital per capita (USD) for each country in **{map_year}**. Use the sidebar slider to change the year.")

map_data = total[total["Year"] == map_year]
fig_map = px.choropleth(
    map_data,
    locations="Country",
    locationmode="country names",
    color="Capital_USD",
    color_continuous_scale="Greens",
    labels={"Capital_USD": "USD per capita"},
    title=f"Renewable Natural Capital per Capita — {map_year}"
)
fig_map.update_layout(
    height=420,
    margin=dict(l=0, r=0, t=40, b=0),
    paper_bgcolor="#1e2130",
    geo=dict(bgcolor="#162032", showframe=False)
)
st.plotly_chart(fig_map, use_container_width=True)

st.markdown("---")

# ── Chart 2: Line Chart ───────────────────────────────────────────────────────
st.subheader("Renewable Capital Trends Over Time")
st.markdown("Compare how selected countries changed in renewable natural capital per capita over the years.")

if selected_countries:
    trend_data = total[
        total["Country"].isin(selected_countries) &
        total["Year"].between(year_range[0], year_range[1])
    ]
    fig_line = px.line(
        trend_data,
        x="Year", y="Capital_USD",
        color="Country",
        markers=True,
        labels={"Capital_USD": "USD per capita"},
        title="Renewable Capital per Capita Over Time"
    )
    fig_line.update_layout(
        height=400,
        paper_bgcolor="#1e2130",
        plot_bgcolor="#0e1117",
        legend=dict(orientation="h", yanchor="bottom", y=-0.35, x=0)
    )
    st.plotly_chart(fig_line, use_container_width=True)
else:
    st.info("Please select at least one country from the sidebar.")

st.markdown("---")

# ── Chart 3 & 4 side by side ──────────────────────────────────────────────────
st.subheader("Country Rankings and Capital Composition")
col1, col2 = st.columns(2)

with col1:
    st.markdown(f"**Top 10 Countries by Renewable Capital ({ranking_year})**")
    top10 = total[total["Year"] == ranking_year].nlargest(10, "Capital_USD")
    fig_bar = px.bar(
        top10,
        x="Capital_USD", y="Country",
        orientation="h",
        color="Capital_USD",
        color_continuous_scale="Greens",
        labels={"Capital_USD": "USD per capita", "Country": ""},
        title=f"Top 10 Countries — {ranking_year}"
    )
    fig_bar.update_layout(
        yaxis=dict(autorange="reversed"),
        height=420,
        paper_bgcolor="#1e2130",
        plot_bgcolor="#0e1117",
        showlegend=False,
        coloraxis_showscale=False
    )
    st.plotly_chart(fig_bar, use_container_width=True)

with col2:
    st.markdown(f"**Capital Type Breakdown — {pie_country} ({pie_year})**")
    pie_data = breakdown[
        (breakdown["Country"] == pie_country) &
        (breakdown["Year"] == pie_year) &
        (breakdown["Value_USD"] > 0)
    ]
    if not pie_data.empty:
        fig_pie = px.pie(
            pie_data,
            names="Category",
            values="Value_USD",
            color_discrete_sequence=px.colors.sequential.Greens,
            title=f"{pie_country} — Capital Breakdown ({pie_year})"
        )
        fig_pie.update_traces(textposition="inside", textinfo="percent+label")
        fig_pie.update_layout(
            height=420,
            paper_bgcolor="#1e2130",
            showlegend=False
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.warning("No data available for this country and year.")

st.markdown("---")

# ── Chart 5: Category Trend ───────────────────────────────────────────────────
st.subheader("Specific Capital Category Trend by Country")
st.markdown(f"Track how a specific type of renewable capital changed over time. Currently showing: **{category_filter}**")

if selected_countries:
    cat_data = breakdown[
        (breakdown["Category"] == category_filter) &
        (breakdown["Country"].isin(selected_countries)) &
        (breakdown["Year"].between(year_range[0], year_range[1]))
    ]
    if not cat_data.empty:
        fig_cat = px.line(
            cat_data,
            x="Year", y="Value_USD",
            color="Country",
            markers=True,
            labels={"Value_USD": "USD per capita", "Category": "Capital Type"},
            title=f"Trend of '{category_filter}' Capital per Capita"
        )
        fig_cat.update_layout(
            height=380,
            paper_bgcolor="#1e2130",
            plot_bgcolor="#0e1117",
            legend=dict(orientation="h", yanchor="bottom", y=-0.35, x=0)
        )
        st.plotly_chart(fig_cat, use_container_width=True)
    else:
        st.warning("No data for this category and country selection.")
else:
    st.info("Please select countries from the sidebar.")

st.markdown("---")

# ── Chart 6: Bottom 10 ────────────────────────────────────────────────────────
st.subheader("Countries with the Lowest Renewable Capital")
st.markdown(f"Identifying the 10 countries with the least renewable natural capital per capita in **{ranking_year}**.")

bottom10 = total[total["Year"] == ranking_year].nsmallest(10, "Capital_USD")
fig_bottom = px.bar(
    bottom10,
    x="Capital_USD", y="Country",
    orientation="h",
    color="Capital_USD",
    color_continuous_scale="Reds",
    labels={"Capital_USD": "USD per capita", "Country": ""},
    title=f"Bottom 10 Countries by Renewable Capital ({ranking_year})"
)
fig_bottom.update_layout(
    yaxis=dict(autorange="reversed"),
    height=380,
    paper_bgcolor="#1e2130",
    plot_bgcolor="#0e1117",
    showlegend=False,
    coloraxis_showscale=False
)
st.plotly_chart(fig_bottom, use_container_width=True)

st.markdown("---")

# ── Chart 7: Raw Data Explorer ────────────────────────────────────────────────
st.subheader("Raw Data Explorer")
st.markdown("Browse the underlying data used in this dashboard.")

view_type = st.radio(
    "Select data view",
    ["Total Renewable Capital (per capita)", "Capital Breakdown by Category"],
    horizontal=True
)

if view_type == "Total Renewable Capital (per capita)":
    country_filter = st.multiselect("Filter by Country", all_countries, default=[])
    show_df = total if not country_filter else total[total["Country"].isin(country_filter)]
else:
    show_df = breakdown

st.dataframe(show_df.reset_index(drop=True), use_container_width=True, height=300)
st.caption(f"Showing {len(show_df):,} rows")

st.markdown("---")
st.caption("5DATA004C Data Science Project Lifecycle | University of Westminster | 2025/26 | Data: World Bank Changing Wealth of Nations (CWON)")
