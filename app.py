import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Global Sustainability Dashboard",
    page_icon="🌍",
    layout="wide"
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
    <style>
        .main { background-color: #0e1117; }
        .block-container { padding-top: 1.5rem; }
        h1 { color: #4CAF50; }
        .metric-card {
            background-color: #1e2130;
            padding: 15px;
            border-radius: 10px;
            border-left: 4px solid #4CAF50;
            margin-bottom: 10px;
        }
    </style>
""", unsafe_allow_html=True)

# ── Load Data ─────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    ren = pd.read_csv("Data/Renewable Natural Capital.csv")
    n2o = pd.read_csv("Data/N2O from Wastewater.csv")
    co2 = pd.read_csv("Data/CO2 Emissions.csv")
    return ren, n2o, co2

ren_raw, n2o_raw, co2_raw = load_data()

# ── Clean / Filter Data ───────────────────────────────────────────────────────
# Renewable capital — per capita, total category only
ren = ren_raw[
    (ren_raw["COMP_BREAKDOWN_1_LABEL"] == "Aggregation: per capita") &
    (ren_raw["COMP_BREAKDOWN_2_LABEL"] == "Renewable capital: total")
][["REF_AREA_LABEL", "TIME_PERIOD", "OBS_VALUE"]].dropna()
ren.columns = ["Country", "Year", "Renewable_Capital_USD"]

# Renewable capital breakdown (all categories, per capita)
ren_breakdown = ren_raw[
    (ren_raw["COMP_BREAKDOWN_1_LABEL"] == "Aggregation: per capita") &
    (ren_raw["COMP_BREAKDOWN_2_LABEL"] != "Renewable capital: total")
][["REF_AREA_LABEL", "TIME_PERIOD", "COMP_BREAKDOWN_2_LABEL", "OBS_VALUE"]].dropna()
ren_breakdown.columns = ["Country", "Year", "Category", "Value_USD"]
ren_breakdown["Category"] = ren_breakdown["Category"].str.replace("Renewable capital: ", "", regex=False)

# N2O wastewater
n2o = n2o_raw[["REF_AREA_LABEL", "TIME_PERIOD", "OBS_VALUE"]].dropna()
n2o.columns = ["Country", "Year", "N2O_MTCO2E"]

# CO2 emissions
co2 = co2_raw[["REF_AREA_LABEL", "TIME_PERIOD", "OBS_VALUE"]].dropna()
co2.columns = ["Country", "Year", "CO2_per_person"]

# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/8/87/Color_icon_green.svg", width=50)
st.sidebar.title("🌍 Dashboard Filters")
st.sidebar.markdown("---")

all_countries = sorted(ren["Country"].unique())
selected_countries = st.sidebar.multiselect(
    "Select Countries",
    options=all_countries,
    default=["United Kingdom", "China", "United States", "India", "Brazil"]
)

year_range = st.sidebar.slider(
    "Select Year Range",
    min_value=int(ren["Year"].min()),
    max_value=int(ren["Year"].max()),
    value=(2000, 2020)
)

breakdown_categories = sorted(ren_breakdown["Category"].unique())
selected_category = st.sidebar.selectbox(
    "Renewable Capital Category (Breakdown Chart)",
    options=breakdown_categories,
    index=breakdown_categories.index("timber") if "timber" in breakdown_categories else 0
)

st.sidebar.markdown("---")
st.sidebar.markdown("**Data Sources:**")
st.sidebar.markdown("- World Bank CWON")
st.sidebar.markdown("- World Bank CLEAR Water")
st.sidebar.markdown("- World Bank SSGD")

# ── Main Title ────────────────────────────────────────────────────────────────
st.title("🌍 Global Sustainability Dashboard")
st.markdown("Exploring renewable natural capital, CO₂ emissions, and N₂O wastewater emissions across nations.")
st.markdown("---")

# ── KPI Metrics ───────────────────────────────────────────────────────────────
latest_year = ren[ren["Year"] == ren["Year"].max()]
col1, col2, col3, col4 = st.columns(4)

with col1:
    top_country = latest_year.loc[latest_year["Renewable_Capital_USD"].idxmax(), "Country"]
    st.metric("🥇 Highest Renewable Capital (2020)", top_country)

with col2:
    avg_cap = latest_year["Renewable_Capital_USD"].mean()
    st.metric("💰 Global Avg Renewable Capital", f"${avg_cap:,.0f}")

with col3:
    top_co2 = co2[co2["Year"] == co2["Year"].max()]
    if not top_co2.empty:
        worst = top_co2.loc[top_co2["CO2_per_person"].idxmax(), "Country"]
        st.metric("🏭 Highest CO₂ per Person (2020)", worst)

with col4:
    st.metric("🌐 Countries Tracked", f"{ren['Country'].nunique()}")

st.markdown("---")

# ── Row 1: World Map + Line Chart ─────────────────────────────────────────────
col_left, col_right = st.columns([1.2, 1])

with col_left:
    st.subheader("🗺️ Renewable Natural Capital by Country")
    map_year = st.slider("Select Year for Map", 1995, 2020, 2020, key="map_year")
    map_data = ren[ren["Year"] == map_year]
    fig_map = px.choropleth(
        map_data,
        locations="Country",
        locationmode="country names",
        color="Renewable_Capital_USD",
        color_continuous_scale="Greens",
        title=f"Renewable Natural Capital per Capita ({map_year})",
        labels={"Renewable_Capital_USD": "USD (per capita)"},
        template="plotly_dark"
    )
    fig_map.update_layout(margin=dict(l=0, r=0, t=40, b=0), height=380)
    st.plotly_chart(fig_map, use_container_width=True)

with col_right:
    st.subheader("📈 Renewable Capital Trend Over Time")
    if selected_countries:
        trend_data = ren[
            (ren["Country"].isin(selected_countries)) &
            (ren["Year"].between(year_range[0], year_range[1]))
        ]
        fig_line = px.line(
            trend_data,
            x="Year", y="Renewable_Capital_USD",
            color="Country",
            title="Renewable Capital per Capita Over Time",
            labels={"Renewable_Capital_USD": "USD (per capita)"},
            template="plotly_dark"
        )
        fig_line.update_layout(height=380)
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.info("Please select at least one country from the sidebar.")

st.markdown("---")

# ── Row 2: Bar Chart Top 10 + Breakdown Pie ───────────────────────────────────
col_left2, col_right2 = st.columns(2)

with col_left2:
    st.subheader("📊 Top 10 Countries — Renewable Capital")
    bar_year = st.selectbox("Select Year", sorted(ren["Year"].unique(), reverse=True), key="bar_year")
    top10 = ren[ren["Year"] == bar_year].nlargest(10, "Renewable_Capital_USD")
    fig_bar = px.bar(
        top10,
        x="Renewable_Capital_USD", y="Country",
        orientation="h",
        color="Renewable_Capital_USD",
        color_continuous_scale="Greens",
        title=f"Top 10 Countries by Renewable Capital ({bar_year})",
        labels={"Renewable_Capital_USD": "USD (per capita)"},
        template="plotly_dark"
    )
    fig_bar.update_layout(yaxis=dict(autorange="reversed"), height=400)
    st.plotly_chart(fig_bar, use_container_width=True)

with col_right2:
    st.subheader("🥧 Renewable Capital Breakdown by Category")
    pie_country = st.selectbox("Select Country", all_countries,
                                index=all_countries.index("United Kingdom") if "United Kingdom" in all_countries else 0,
                                key="pie_country")
    pie_year = st.selectbox("Select Year ", sorted(ren_breakdown["Year"].unique(), reverse=True), key="pie_year")
    pie_data = ren_breakdown[
        (ren_breakdown["Country"] == pie_country) &
        (ren_breakdown["Year"] == pie_year) &
        (ren_breakdown["Value_USD"] > 0)
    ]
    if not pie_data.empty:
        fig_pie = px.pie(
            pie_data,
            names="Category", values="Value_USD",
            title=f"Capital Breakdown — {pie_country} ({pie_year})",
            template="plotly_dark",
            color_discrete_sequence=px.colors.sequential.Greens
        )
        fig_pie.update_layout(height=400)
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("No data available for this selection.")

st.markdown("---")

# ── Row 3: CO2 Scatter + N2O Bar ──────────────────────────────────────────────
col_left3, col_right3 = st.columns(2)

with col_left3:
    st.subheader("🔵 CO₂ Emissions vs Renewable Capital")
    scatter_year = st.selectbox("Select Year  ", [2018, 2020], key="scatter_year")
    co2_sel = co2[co2["Year"] == scatter_year]
    ren_sel = ren[ren["Year"] == scatter_year]
    merged = pd.merge(co2_sel, ren_sel, on="Country")
    if not merged.empty:
        fig_scatter = px.scatter(
            merged,
            x="Renewable_Capital_USD",
            y="CO2_per_person",
            hover_name="Country",
            color="CO2_per_person",
            color_continuous_scale="RdYlGn_r",
            title=f"CO₂ per Person vs Renewable Capital ({scatter_year})",
            labels={
                "Renewable_Capital_USD": "Renewable Capital (USD per capita)",
                "CO2_per_person": "CO₂ per Person (tonnes)"
            },
            template="plotly_dark"
        )
        fig_scatter.update_layout(height=400)
        st.plotly_chart(fig_scatter, use_container_width=True)

with col_right3:
    st.subheader("☁️ N₂O Emissions from Wastewater (2015)")
    top_n = st.slider("Show Top N Countries", 5, 30, 15, key="n2o_slider")
    top_n2o = n2o.nlargest(top_n, "N2O_MTCO2E")
    fig_n2o = px.bar(
        top_n2o,
        x="Country", y="N2O_MTCO2E",
        color="N2O_MTCO2E",
        color_continuous_scale="Oranges",
        title=f"Top {top_n} Countries — N₂O from Wastewater (2015)",
        labels={"N2O_MTCO2E": "Megatonnes CO₂-equivalent"},
        template="plotly_dark"
    )
    fig_n2o.update_layout(xaxis_tickangle=-45, height=400)
    st.plotly_chart(fig_n2o, use_container_width=True)

st.markdown("---")

# ── Raw Data Explorer ─────────────────────────────────────────────────────────
st.subheader("🔍 Explore Raw Data")
dataset_choice = st.selectbox("Choose Dataset to Explore",
                               ["Renewable Natural Capital", "CO₂ Emissions", "N₂O Wastewater"])
if dataset_choice == "Renewable Natural Capital":
    show_df = ren
elif dataset_choice == "CO₂ Emissions":
    show_df = co2
else:
    show_df = n2o

st.dataframe(show_df, use_container_width=True, height=300)

st.markdown("---")
st.markdown("**5DATA004C Data Science Project Lifecycle** | University of Westminster | 2025/26")
