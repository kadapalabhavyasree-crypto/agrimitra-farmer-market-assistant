import sqlite3
from pathlib import Path
from datetime import date
import pandas as pd
import plotly.express as px
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = BASE_DIR / "agrimitra.db"
SAMPLE_CSV = DATA_DIR / "sample_prices.csv"

st.set_page_config(page_title="AgriMitra | Farmer Market Price Assistant",
                   page_icon="🌾", layout="wide")

REQUIRED_COLUMNS = [
    "State", "District", "Market", "Commodity", "Variety", "Date",
    "Minimum Price", "Maximum Price", "Modal Price", "Unit", "Source",
    "Data_Status"
]

def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def initialize_database():
    DATA_DIR.mkdir(exist_ok=True)
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS market_prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                State TEXT NOT NULL,
                District TEXT NOT NULL,
                Market TEXT NOT NULL,
                Commodity TEXT NOT NULL,
                Variety TEXT,
                Date TEXT NOT NULL,
                "Minimum Price" REAL,
                "Maximum Price" REAL,
                "Modal Price" REAL,
                Unit TEXT NOT NULL,
                Source TEXT,
                Data_Status TEXT DEFAULT 'Sample'
            )
        """)
        count = conn.execute("SELECT COUNT(*) FROM market_prices").fetchone()[0]
        if count == 0 and SAMPLE_CSV.exists():
            df = pd.read_csv(SAMPLE_CSV)
            df = prepare_data(df)
            df.to_sql("market_prices", conn, if_exists="append", index=False)

def prepare_data(df):
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError("Missing required columns: " + ", ".join(missing))
    df = df[REQUIRED_COLUMNS]
    for col in ["State", "District", "Market", "Commodity", "Variety", "Unit", "Source", "Data_Status"]:
        df[col] = df[col].fillna("").astype(str).str.strip()
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce").dt.strftime("%Y-%m-%d")
    for col in ["Minimum Price", "Maximum Price", "Modal Price"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["Date", "Minimum Price", "Maximum Price", "Modal Price"])
    df = df[(df["Minimum Price"] >= 0) &
            (df["Maximum Price"] >= df["Minimum Price"]) &
            (df["Modal Price"] >= df["Minimum Price"]) &
            (df["Modal Price"] <= df["Maximum Price"])]
    df = df[df["Unit"] != ""]
    df["Data_Status"] = df["Data_Status"].replace("", "Sample")
    return df

def load_data():
    with get_connection() as conn:
        return pd.read_sql_query("SELECT * FROM market_prices ORDER BY Date DESC", conn)

def money(value):
    return f"₹{value:,.2f}"

initialize_database()
df = load_data()

st.title("🌾 AgriMitra")
st.subheader("Farmer Market Price Assistant")
st.caption("Agricultural market information, price comparison and selling support")

if df.empty:
    st.warning("No market records are available. Upload a CSV file from Data Management.")
    st.stop()

# Sidebar filters
st.sidebar.header("🔎 Market Filters")
commodities = sorted(df["Commodity"].dropna().unique().tolist())
states = sorted(df["State"].dropna().unique().tolist())
selected_crop = st.sidebar.selectbox("Select crop", commodities)
selected_state = st.sidebar.selectbox("Select state", ["All"] + states)
filtered_base = df[df["Commodity"] == selected_crop]
if selected_state != "All":
    filtered_base = filtered_base[filtered_base["State"] == selected_state]
districts = sorted(filtered_base["District"].dropna().unique().tolist())
selected_district = st.sidebar.selectbox("Select district", ["All"] + districts)
if selected_district != "All":
    filtered_base = filtered_base[filtered_base["District"] == selected_district]
markets = sorted(filtered_base["Market"].dropna().unique().tolist())
selected_market = st.sidebar.selectbox("Select market", ["All"] + markets)
if selected_market != "All":
    filtered_base = filtered_base[filtered_base["Market"] == selected_market]

min_date = pd.to_datetime(filtered_base["Date"]).min().date()
max_date = pd.to_datetime(filtered_base["Date"]).max().date()
date_range = st.sidebar.date_input("Date range", value=(min_date, max_date),
                                   min_value=min_date, max_value=max_date)
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
    filtered_base = filtered_base[
        (pd.to_datetime(filtered_base["Date"]).dt.date >= start_date) &
        (pd.to_datetime(filtered_base["Date"]).dt.date <= end_date)
    ]

page = st.sidebar.radio("Navigation", [
    "Overview", "Market Comparison", "Price Trends",
    "Selling Calculator", "Data Management"
])

sample_count = int((filtered_base["Data_Status"].str.lower() == "sample").sum())
verified_count = int((filtered_base["Data_Status"].str.lower() == "verified").sum())

if page == "Overview":
    st.markdown("### 📊 Market Overview")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Price records", f"{len(filtered_base):,}")
    c2.metric("Crops available", f"{df['Commodity'].nunique():,}")
    c3.metric("Markets in view", f"{filtered_base['Market'].nunique():,}")
    avg_price = filtered_base["Modal Price"].mean()
    c4.metric("Average modal price", money(avg_price) if pd.notna(avg_price) else "N/A")

    st.info(f"Selected crop: **{selected_crop}** · Sample records: **{sample_count}** · Verified records: **{verified_count}**")
    left, right = st.columns(2)
    with left:
        st.markdown("#### Modal price by market")
        if not filtered_base.empty:
            market_avg = (filtered_base.groupby("Market", as_index=False)["Modal Price"]
                          .mean().sort_values("Modal Price", ascending=False))
            fig = px.bar(market_avg, x="Market", y="Modal Price",
                         labels={"Modal Price": f"Modal price ({filtered_base['Unit'].iloc[0]})"},
                         color="Modal Price", title="Average reported modal price")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No records match the selected filters.")
    with right:
        st.markdown("#### Data status")
        status_df = filtered_base["Data_Status"].value_counts().rename_axis("Status").reset_index(name="Records")
        if not status_df.empty:
            fig = px.pie(status_df, names="Status", values="Records", hole=0.45)
            st.plotly_chart(fig, use_container_width=True)
    st.markdown("#### Latest available records")
    st.dataframe(filtered_base.head(15), use_container_width=True, hide_index=True)

elif page == "Market Comparison":
    st.markdown("### ⚖️ Compare market prices")
    if filtered_base.empty:
        st.warning("No records match the selected filters.")
    else:
        comparison = (filtered_base.groupby(["State", "District", "Market", "Unit"], as_index=False)
                      .agg({"Minimum Price": "mean", "Maximum Price": "mean", "Modal Price": "mean"}))
        comparison = comparison.sort_values("Modal Price", ascending=False)
        unit_list = comparison["Unit"].unique()
        if len(unit_list) > 1:
            st.warning("More than one price unit is present. Compare records only after confirming compatible units.")
        fig = px.bar(comparison, x="Market", y="Modal Price", color="Market",
                     hover_data=["State", "District", "Minimum Price", "Maximum Price", "Unit"],
                     title="Market-wise average modal price")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(comparison, use_container_width=True, hide_index=True)
        if len(comparison):
            best = comparison.iloc[0]
            st.success(f"Highest average reported modal price in this filtered view: {best['Market']} — {money(best['Modal Price'])} per {best['Unit']}. This is not a sale recommendation.")

elif page == "Price Trends":
    st.markdown("### 📈 Historical price trends")
    if filtered_base.empty:
        st.warning("No records match the selected filters.")
    else:
        trend = filtered_base.copy()
        trend["Date"] = pd.to_datetime(trend["Date"])
        trend = trend.sort_values("Date")
        fig = px.line(trend, x="Date", y="Modal Price", color="Market",
                      markers=True, hover_data=["Minimum Price", "Maximum Price", "Unit", "Source"],
                      title=f"{selected_crop}: reported modal price over time")
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Trend lines are based only on records currently stored in the application. Missing dates do not imply zero prices.")

elif page == "Selling Calculator":
    st.markdown("### 🧮 Selling-value calculator")
    st.write("Enter your expected quantity and expenses. The result is an estimate based on the price you choose.")
    if filtered_base.empty:
        st.warning("No price records are available for the selected filters.")
    else:
        records = filtered_base.sort_values("Date", ascending=False)
        options = records.apply(lambda r: f"{r['Market']} | {r['Date']} | ₹{r['Modal Price']:,.2f}/{r['Unit']} | {r['Data_Status']}", axis=1)
        selected_idx = st.selectbox("Choose a price record", range(len(options)),
                                    format_func=lambda i: options.iloc[i])
        record = records.iloc[selected_idx]
        st.caption(f"Source: {record['Source']} · Reporting date: {record['Date']} · Status: {record['Data_Status']}")
        col1, col2 = st.columns(2)
        with col1:
            quantity = st.number_input(f"Quantity ({record['Unit']})", min_value=0.0, value=10.0, step=1.0)
            price = st.number_input("Expected selling price per unit (₹)", min_value=0.0,
                                    value=float(record["Modal Price"]), step=10.0)
        with col2:
            transport = st.number_input("Transport expenses (₹)", min_value=0.0, value=0.0, step=50.0)
            other = st.number_input("Other expenses (₹)", min_value=0.0, value=0.0, step=50.0)
        gross = quantity * price
        total_expenses = transport + other
        net = gross - total_expenses
        a, b, c = st.columns(3)
        a.metric("Estimated gross value", money(gross))
        b.metric("Total expenses", money(total_expenses))
        c.metric("Estimated net value", money(net))
        st.caption("Illustrative estimate only. Actual returns may differ due to quality, weighing, fees, price changes and other costs.")

elif page == "Data Management":
    st.markdown("### 🗂️ Data management")
    st.write("Upload a CSV using the exact columns shown below. Uploaded records are stored in the local SQLite database.")
    st.code(", ".join(REQUIRED_COLUMNS))
    uploaded = st.file_uploader("Upload market price CSV", type=["csv"])
    if uploaded is not None:
        try:
            incoming = prepare_data(pd.read_csv(uploaded))
            if incoming.empty:
                st.error("No valid records found. Check dates, prices, units and required columns.")
            else:
                if st.button("Import records", type="primary"):
                    with get_connection() as conn:
                        incoming.to_sql("market_prices", conn, if_exists="append", index=False)
                    st.success(f"Imported {len(incoming)} records. Refresh the page to view them.")
        except Exception as exc:
            st.error(f"CSV validation failed: {exc}")

    st.markdown("#### Current database records")
    st.dataframe(df, use_container_width=True, hide_index=True)
    csv_bytes = df[REQUIRED_COLUMNS].to_csv(index=False).encode("utf-8")
    st.download_button("Download current records as CSV", csv_bytes,
                       file_name="agrimitra_market_prices.csv", mime="text/csv")

st.divider()
st.caption("AgriMitra is an information aid. Always confirm current prices, quality requirements and market conditions locally before selling.")
