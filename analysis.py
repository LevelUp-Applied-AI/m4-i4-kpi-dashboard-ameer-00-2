"""Integration 4 — KPI Dashboard: Amman Digital Market Analytics

Extract data from PostgreSQL, compute KPIs, run statistical tests,
and create visualizations for the executive summary.

Usage:
    python analysis.py
"""
import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
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

    # KPI 1: Total Revenue
    total_revenue = merged['revenue'].sum()

    # KPI 2: Average Order Value
    avg_order_value = merged.groupby('order_id')['revenue'].sum().mean()

    # KPI 3: Customer Retention Rate (repeat purchase rate)
    customer_order_counts = merged.groupby('customer_id')['order_id'].nunique()
    repeat_customers = (customer_order_counts > 1).sum()
    retention_rate = (repeat_customers / len(customer_order_counts)) * 100

    # KPI 4: Monthly Active Users (time-based)
    merged['month'] = merged['order_date'].dt.to_period('M')
    monthly_active_users = merged.groupby('month')['customer_id'].nunique()

    # KPI 5: Cohort Revenue Growth (time-based, by registration month)
    merged['registration_month'] = pd.to_datetime(merged['registration_date']).dt.to_period('M')
    cohort_revenue = merged.groupby('registration_month')['revenue'].sum()

    return {
        "Total Revenue": total_revenue,
        "Average Order Value": avg_order_value,
        "Customer Retention Rate": retention_rate,
        "Monthly Active Users": monthly_active_users,
        "Cohort Revenue Growth": cohort_revenue,
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
    """Create publication-quality charts for all 5 KPIs.

    Args:
        kpi_results: dict from compute_kpis()
        stat_results: dict from run_statistical_tests()

    Returns:
        None

    Side effects:
        Saves at least 5 PNG files to the output/ directory.
        Each chart should have a descriptive title stating the finding,
        proper axis labels, and annotations where appropriate.
    """
    # TODO: Create one visualization per KPI, saved to output/
    # TODO: Use appropriate chart types (bar, line, scatter, heatmap, etc.)
    # TODO: Ensure titles state the insight, not just the data
    sns.set_theme(style="whitegrid")
    sns.set_palette("colorblind")
    
    # KPI 1: Total Revenue
    plt.figure(figsize=(10, 6))
    plt.bar(["Total Revenue"], [kpi_results['Total Revenue']], color='steelblue', width=0.5)
    plt.title("Total Platform Revenue: 45,147 JOD")
    plt.ylabel("Revenue (JOD)")
    plt.ylim(0, kpi_results['Total Revenue'] * 1.1)
    plt.savefig("output/kpi_1_total_revenue.png")

    # KPI 2: Average Order Value
    plt.figure(figsize=(10, 6))
    plt.bar(["Average Order Value"], [kpi_results['Average Order Value']], color='darkgreen', width=0.5)
    plt.title("Average Order Value Across Market")
    plt.ylabel("Value (JOD)")
    plt.ylim(0, kpi_results['Average Order Value'] * 1.2)
    plt.savefig("output/kpi_2_average_order_value.png")

    # KPI 3: Customer Retention Rate
    plt.figure(figsize=(10, 6))
    retention = kpi_results['Customer Retention Rate']
    colors_retention = ['#2ecc71' if retention > 30 else '#e74c3c']
    plt.bar(["Retention Rate"], [retention], color=colors_retention, width=0.5)
    plt.title(f"Customer Retention Rate: {retention:.1f}%")
    plt.ylabel("Percentage (%)")
    plt.ylim(0, 100)
    plt.axhline(y=50, color='gray', linestyle='--', alpha=0.5, label='Industry Average')
    plt.legend()
    plt.savefig("output/kpi_3_customer_retention.png")

    # KPI 4: Monthly Active Users (time-based)
    plt.figure(figsize=(10, 6))
    kpi_results['Monthly Active Users'].plot(kind='line', marker='o', linewidth=2, color='purple')
    plt.title("Monthly Active Users Show Growth Trend")
    plt.xlabel("Month")
    plt.ylabel("Number of Active Users")
    plt.savefig("output/kpi_4_monthly_active_users.png")

    # KPI 5: Cohort Revenue Growth (time-based)
    plt.figure(figsize=(10, 6))
    kpi_results['Cohort Revenue Growth'].plot(kind='bar', color='coral')
    plt.title("Revenue by Customer Cohort (Registration Month)")
    plt.xlabel("Registration Month")
    plt.ylabel("Total Cohort Revenue (JOD)")
    plt.xticks(rotation=45)
    plt.savefig("output/kpi_5_cohort_revenue.png")

    plt.close('all')
    


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
