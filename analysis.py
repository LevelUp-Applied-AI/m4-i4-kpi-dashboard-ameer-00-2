"""Integration 4 — KPI Dashboard: Amman Digital Market Analytics

Extract data from PostgreSQL, compute KPIs, run statistical tests,
and create visualizations for the executive summary.

Usage:
    python analysis.py
"""
import os
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy import stats
from sqlalchemy import create_engine


# def connect_db():
#     """Create a SQLAlchemy engine connected to the amman_market database.

#     Returns:
#         engine: SQLAlchemy engine instance

#     Notes:
#         Use DATABASE_URL environment variable if set, otherwise default to:
#         postgresql://postgres:postgres@localhost:5432/amman_market
#     """
#     # T: Create and return a SQLAlchemy engine using DATABASE_URL or a default
#     db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/amman_market")
#     return create_engine(db_url)
def connect_db():
    """Create a SQLAlchemy engine connected to the amman_market database.

    Returns:
        engine: SQLAlchemy engine instance
    """
    # Use 127.0.0.1 for Windows compatibility and set password to 'postgres'
    default_url = "postgresql://postgres:postgres@127.0.0.1:5432/amman_market"
    
    # This will still respect the DATABASE_URL environment variable if it's set
    db_url = os.getenv("DATABASE_URL", default_url)
    return create_engine(db_url)

def extract_data(engine):
    """Extract all required tables from the database into DataFrames.

    Args:
        engine: SQLAlchemy engine connected to amman_market

    Returns:
        dict: mapping of table names to DataFrames
              (e.g., {"customers": df, "products": df, "orders": df, "order_items": df})
    """
    # TODO: Query each table and return a dictionary of DataFrames

    customers = pd.read_sql("SELECT * FROM customers", engine)
    products = pd.read_sql("SELECT * FROM products", engine)

    orders = pd.read_sql("SELECT * FROM orders WHERE status != 'cancelled'", engine)
    order_items = pd.read_sql("SELECT * FROM order_items WHERE quantity <= 100", engine)

    return {
        "customers": customers,
        "products": products,
        "orders": orders,
        "order_items": order_items
    }
def compute_kpis(data_dict):
    """Compute the 5 KPIs defined in kpi_framework.md.

    Args:
        data_dict: dict of DataFrames from extract_data()

    Returns:
        dict: mapping of KPI names to their computed values (or DataFrames
              for time-series / cohort KPIs)

    Notes:
        At least 2 KPIs should be time-based and 1 should be cohort-based.
    """
    # TODO: Join tables as needed, then compute each KPI from your framework
    # TODO: Return results as a dictionary for use in visualizations


    df_o = data_dict['orders']
    df_oi = data_dict['order_items']
    df_p = data_dict['products']
    df_c = data_dict['customers']

    merged = df_oi.merge(df_p, on='product_id').merge(df_o, on='order_id').merge(df_c, on='customer_id')
    merged['revenue'] = merged['quantity'] * merged['unit_price']
    merged['order_date'] = pd.to_datetime(merged['order_date'])
    merged['registration_date'] = pd.to_datetime(merged['registration_date'])

    # KPI 1: Monthly Revenue Growth (MoM)
    monthly_revenue = merged.groupby(merged['order_date'].dt.to_period('M'))['revenue'].sum()
    monthly_revenue = monthly_revenue.sort_index()
    if len(monthly_revenue) >= 2:
        current_month = monthly_revenue.iloc[-1]
        previous_month = monthly_revenue.iloc[-2]
        mom_growth = ((current_month - previous_month) / previous_month) * 100 if previous_month != 0 else 0
    else:
        mom_growth = 0

    # KPI 2: Average Order Value (AOV)
    avg_order_value = merged.groupby('order_id')['revenue'].sum().mean()

    # KPI 3: Regional Market Share (Amman)
    total_revenue = merged['revenue'].sum()
    amman_revenue = merged[merged['city'] == 'Amman']['revenue'].sum()
    amman_market_share = (amman_revenue / total_revenue) * 100 if total_revenue != 0 else 0

    # KPI 4: Weekly Sales Velocity (Peak Day)
    merged['day_of_week'] = merged['order_date'].dt.day_name()
    weekly_velocity = merged.groupby('day_of_week')['order_id'].nunique()
    peak_day = weekly_velocity.idxmax()
    peak_orders = weekly_velocity.max()

    # KPI 5: 30-Day New Customer Retention
    # New customers: first order within 30 days of registration
    merged['days_since_registration'] = (merged['order_date'] - merged['registration_date']).dt.days
    new_customers = merged[merged['days_since_registration'] <= 30]
    # Retention: customers with >1 order within 30 days of first order
    first_orders = new_customers.groupby('customer_id')['order_date'].min().reset_index()
    first_orders.columns = ['customer_id', 'first_order_date']
    new_customers = new_customers.merge(first_orders, on='customer_id')
    new_customers['days_since_first'] = (new_customers['order_date'] - new_customers['first_order_date']).dt.days
    repeat_within_30 = new_customers[(new_customers['days_since_first'] > 0) & (new_customers['days_since_first'] <= 30)]
    unique_new_customers = new_customers['customer_id'].nunique()
    unique_repeat_customers = repeat_within_30['customer_id'].nunique()
    retention_rate = (unique_repeat_customers / unique_new_customers) * 100 if unique_new_customers != 0 else 0

    return {
        "MoM Revenue Growth": mom_growth,
        "Average Order Value": avg_order_value,
        "Amman Market Share": amman_market_share,
        "Peak Sales Day": peak_day,
        "30-Day Retention Rate": retention_rate,
        "monthly_revenue": monthly_revenue,
        "weekly_velocity": weekly_velocity,
        "merged_data": merged
    }
    


def run_statistical_tests(kpi_results):
    """Run hypothesis tests to validate patterns in the data.

    Args:
        data_dict: dict of DataFrames from extract_data()

    Returns:
        dict: mapping of test names to results (test statistic, p-value,
              interpretation)

    Notes:
        Run at least one test. Consider:
        - Does average order value differ across product categories?
        - Is there a significant trend in monthly revenue?
        - Do customer cities differ in purchasing behavior?
    """
    # TODO: Select and run appropriate statistical tests
    # TODO: Interpret results (reject or fail to reject the null hypothesis)
    df = kpi_results['merged_data']
    
    amman_rev = df[df['city'] == 'Amman'].groupby('order_id')['revenue'].sum()
    irbid_rev = df[df['city'] == 'Irbid'].groupby('order_id')['revenue'].sum()
    
    t_stat, p_val = stats.ttest_ind(amman_rev, irbid_rev)
    
    all_std = pd.concat([amman_rev, irbid_rev]).std()
    cohen_d = (amman_rev.mean() - irbid_rev.mean()) / all_std

    return {
        "city_comparison": {
            "test": "Independent T-Test",
            "t_stat": t_stat,
            "p_value": p_val,
            "cohen_d": cohen_d,
            "interpretation": "Significant" if p_val < 0.05 else "Not Significant"
        }
    }
    


def create_visualizations(kpi_results, stat_results):
    """Create publication-quality charts for all 5 KPIs using Plotly.

    Args:
        kpi_results: dict from compute_kpis()
        stat_results: dict from run_statistical_tests()

    Returns:
        None

    Side effects:
        Saves an interactive HTML dashboard to output/dashboard.html
    """
    # Create subplots for the dashboard
    fig = make_subplots(
        rows=3, cols=2,
        subplot_titles=(
            f"MoM Revenue Growth: {kpi_results['MoM Revenue Growth']:.1f}%",
            f"Average Order Value: {kpi_results['Average Order Value']:.2f} JOD",
            f"Amman Market Share: {kpi_results['Amman Market Share']:.1f}%",
            f"Peak Sales Day: {kpi_results['Peak Sales Day']}",
            f"30-Day Retention Rate: {kpi_results['30-Day Retention Rate']:.1f}%",
            "Weekly Sales Velocity"
        ),
        specs=[
            [{"type": "indicator"}, {"type": "indicator"}],
            [{"type": "indicator"}, {"type": "indicator"}],
            [{"type": "indicator"}, {"type": "bar"}]
        ]
    )

    # KPI 1: MoM Revenue Growth
    fig.add_trace(
        go.Indicator(
            mode="number+delta",
            value=kpi_results['MoM Revenue Growth'],
            delta={'reference': 15, 'relative': True},
            title={"text": "MoM Growth %"},
            domain={'row': 0, 'column': 0}
        ),
        row=1, col=1
    )

    # KPI 2: Average Order Value
    fig.add_trace(
        go.Indicator(
            mode="number",
            value=kpi_results['Average Order Value'],
            title={"text": "AOV (JOD)"},
            domain={'row': 0, 'column': 1}
        ),
        row=1, col=2
    )

    # KPI 3: Amman Market Share
    fig.add_trace(
        go.Indicator(
            mode="number",
            value=kpi_results['Amman Market Share'],
            title={"text": "Amman Share %"},
            domain={'row': 1, 'column': 0}
        ),
        row=2, col=1
    )

    # KPI 4: Peak Sales Day
    fig.add_trace(
        go.Indicator(
            mode="number",
            value=kpi_results['weekly_velocity'][kpi_results['Peak Sales Day']],
            title={"text": f"Orders on {kpi_results['Peak Sales Day']}"},
            domain={'row': 1, 'column': 1}
        ),
        row=2, col=2
    )

    # KPI 5: 30-Day Retention Rate
    fig.add_trace(
        go.Indicator(
            mode="number",
            value=kpi_results['30-Day Retention Rate'],
            title={"text": "Retention %"},
            domain={'row': 2, 'column': 0}
        ),
        row=3, col=1
    )

    # Weekly Sales Velocity Bar Chart
    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    weekly_data = kpi_results['weekly_velocity'].reindex(days_order)
    fig.add_trace(
        go.Bar(
            x=weekly_data.index,
            y=weekly_data.values,
            marker_color='lightblue',
            name='Orders per Day'
        ),
        row=3, col=2
    )

    # Update layout
    fig.update_layout(
        title_text="Amman Digital Market KPI Dashboard",
        showlegend=False,
        height=800
    )

    # Save as HTML
    fig.write_html("output/dashboard.html")
    print("Interactive dashboard saved to output/dashboard.html")
    


def main():
    """Orchestrate the full analysis pipeline."""
    os.makedirs("output", exist_ok=True)

    # TODO: Connect to the database
    # TODO: Extract data
    # TODO: Compute KPIs
    # TODO: Run statistical tests
    # TODO: Create visualizations
    # TODO: Print a summary of KPI values and test results

    engine = connect_db()
    data = extract_data(engine)
    kpis = compute_kpis(data)
    stats_res = run_statistical_tests(kpis)
    create_visualizations(kpis, stats_res)
    print("Success: Analysis complete. Check the 'output/' folder for results.")
if __name__ == "__main__":
    main()
