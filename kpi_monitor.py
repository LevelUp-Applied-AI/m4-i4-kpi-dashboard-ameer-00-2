"""KPI Monitoring Script

Automated KPI monitoring with thresholds, status indicators, and interactive gauges.
"""
import os
import json
import pandas as pd
from sqlalchemy import create_engine
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def load_config():
    """Load threshold configuration from config.json."""
    with open('config.json', 'r') as f:
        return json.load(f)


def connect_db():
    """Create database connection."""
    default_url = "postgresql://postgres:postgres@127.0.0.1:5432/amman_market"
    db_url = os.getenv("DATABASE_URL", default_url)
    return create_engine(db_url)


def extract_data(engine, city_filter=None, category_filter=None, date_from=None, date_to=None):
    """Extract data with optional filters."""
    query = """
    SELECT
        c.customer_id, c.customer_name, c.city, c.registration_date,
        p.product_id, p.product_name, p.category, p.unit_price,
        o.order_id, o.order_date, o.status,
        oi.quantity
    FROM order_items oi
    JOIN products p ON oi.product_id = p.product_id
    JOIN orders o ON oi.order_id = o.order_id
    JOIN customers c ON o.customer_id = c.customer_id
    WHERE o.status != 'cancelled' AND oi.quantity <= 100
    """

    params = []
    if city_filter:
        query += " AND c.city = %s"
        params.append(city_filter)
    if category_filter:
        query += " AND p.category = %s"
        params.append(category_filter)
    if date_from:
        query += " AND o.order_date >= %s"
        params.append(date_from)
    if date_to:
        query += " AND o.order_date <= %s"
        params.append(date_to)

    df = pd.read_sql(query, engine, params=params)
    df['revenue'] = df['quantity'] * df['unit_price']
    df['order_date'] = pd.to_datetime(df['order_date'])
    df['registration_date'] = pd.to_datetime(df['registration_date'])
    return df


def compute_kpis(df, config):
    """Compute all 5 KPIs."""
    # KPI 1: MoM Revenue Growth
    monthly_revenue = df.groupby(df['order_date'].dt.to_period('M'))['revenue'].sum()
    monthly_revenue = monthly_revenue.sort_index()
    if len(monthly_revenue) >= 2:
        current = monthly_revenue.iloc[-1]
        previous = monthly_revenue.iloc[-2]
        mom_growth = ((current - previous) / previous) * 100 if previous != 0 else 0
    else:
        mom_growth = 0

    # KPI 2: Average Order Value
    aov = df.groupby('order_id')['revenue'].sum().mean()

    # KPI 3: Amman Market Share
    total_rev = df['revenue'].sum()
    amman_rev = df[df['city'] == 'Amman']['revenue'].sum()
    amman_share = (amman_rev / total_rev) * 100 if total_rev != 0 else 0

    # KPI 4: Peak Sales Day
    df['day_of_week'] = df['order_date'].dt.day_name()
    weekly_velocity = df.groupby('day_of_week')['order_id'].nunique()
    peak_day = weekly_velocity.idxmax()

    # KPI 5: 30-Day Retention
    new_customers = df[df['registration_date'] >= df['order_date'].min() - pd.Timedelta(days=30)]
    first_orders = new_customers.groupby('customer_id')['order_date'].min().reset_index()
    first_orders.columns = ['customer_id', 'first_order_date']
    new_customers = new_customers.merge(first_orders, on='customer_id')
    repeat_within_30 = new_customers[
        (new_customers['order_date'] > new_customers['first_order_date']) &
        (new_customers['order_date'] <= new_customers['first_order_date'] + pd.Timedelta(days=30))
    ]
    unique_new = new_customers['customer_id'].nunique()
    unique_repeat = repeat_within_30['customer_id'].nunique()
    retention = (unique_repeat / unique_new) * 100 if unique_new != 0 else 0

    return {
        'mom_growth': mom_growth,
        'aov': aov,
        'amman_share': amman_share,
        'peak_day': peak_day,
        'retention': retention,
        'weekly_velocity': weekly_velocity
    }


def get_status(value, threshold, higher_better=True):
    """Determine green/yellow/red status based on threshold."""
    if higher_better:
        if value >= threshold:
            return 'green'
        elif value >= threshold * 0.8:
            return 'yellow'
        else:
            return 'red'
    else:
        if value <= threshold:
            return 'green'
        elif value <= threshold * 1.2:
            return 'yellow'
        else:
            return 'red'


def create_gauge_dashboard(kpis, config):
    """Create interactive gauge dashboard with dropdown filters."""
    fig = make_subplots(
        rows=2, cols=3,
        specs=[
            [{"type": "indicator"}, {"type": "indicator"}, {"type": "indicator"}],
            [{"type": "indicator"}, {"type": "indicator"}, {"type": "bar"}]
        ],
        subplot_titles=[
            f"MoM Growth: {kpis['mom_growth']:.1f}%",
            f"AOV: {kpis['aov']:.2f} JOD",
            f"Amman Share: {kpis['amman_share']:.1f}%",
            f"Peak Day: {kpis['peak_day']}",
            f"Retention: {kpis['retention']:.1f}%",
            "Weekly Velocity"
        ]
    )

    # Color mapping for status
    color_map = {'green': 'green', 'yellow': 'orange', 'red': 'red'}

    # KPI 1: MoM Growth
    status1 = get_status(kpis['mom_growth'], config['thresholds']['mom_growth'])
    fig.add_trace(
        go.Indicator(
            mode="gauge+number",
            value=kpis['mom_growth'],
            gauge={'axis': {'range': [0, 50]}, 'bar': {'color': color_map[status1]}},
            title={"text": "MoM Growth %"},
            domain={'row': 0, 'column': 0}
        ),
        row=1, col=1
    )

    # KPI 2: AOV
    status2 = get_status(kpis['aov'], config['thresholds']['aov'])
    fig.add_trace(
        go.Indicator(
            mode="gauge+number",
            value=kpis['aov'],
            gauge={'axis': {'range': [0, 100]}, 'bar': {'color': color_map[status2]}},
            title={"text": "AOV (JOD)"},
            domain={'row': 0, 'column': 1}
        ),
        row=1, col=2
    )

    # KPI 3: Amman Share
    status3 = get_status(kpis['amman_share'], config['thresholds']['amman_share'])
    fig.add_trace(
        go.Indicator(
            mode="gauge+number",
            value=kpis['amman_share'],
            gauge={'axis': {'range': [0, 100]}, 'bar': {'color': color_map[status3]}},
            title={"text": "Amman Share %"},
            domain={'row': 0, 'column': 2}
        ),
        row=1, col=3
    )

    # KPI 4: Peak Day (using number indicator)
    fig.add_trace(
        go.Indicator(
            mode="number",
            value=kpis['weekly_velocity'][kpis['peak_day']],
            title={"text": f"Orders on {kpis['peak_day']}"},
            domain={'row': 1, 'column': 0}
        ),
        row=2, col=1
    )

    # KPI 5: Retention
    status5 = get_status(kpis['retention'], config['thresholds']['retention'])
    fig.add_trace(
        go.Indicator(
            mode="gauge+number",
            value=kpis['retention'],
            gauge={'axis': {'range': [0, 50]}, 'bar': {'color': color_map[status5]}},
            title={"text": "Retention %"},
            domain={'row': 1, 'column': 1}
        ),
        row=2, col=2
    )

    # Weekly Velocity
    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    weekly_data = kpis['weekly_velocity'].reindex(days_order)
    fig.add_trace(
        go.Bar(x=weekly_data.index, y=weekly_data.values, marker_color='lightblue'),
        row=2, col=3
    )

    fig.update_layout(
        title_text="KPI Monitoring Dashboard",
        height=800
    )

    return fig


def main():
    """Main monitoring function."""
    config = load_config()
    engine = connect_db()

    # Get filter options from config or compute dynamically
    df = extract_data(engine)

    # Compute KPIs
    kpis = compute_kpis(df, config)

    # Print status summary
    print("KPI Monitoring Results:")
    print(f"MoM Growth: {kpis['mom_growth']:.1f}% (Target: {config['thresholds']['mom_growth']}%) - {get_status(kpis['mom_growth'], config['thresholds']['mom_growth'])}")
    print(f"AOV: {kpis['aov']:.2f} JOD (Target: {config['thresholds']['aov']} JOD) - {get_status(kpis['aov'], config['thresholds']['aov'])}")
    print(f"Amman Share: {kpis['amman_share']:.1f}% (Target: {config['thresholds']['amman_share']}%) - {get_status(kpis['amman_share'], config['thresholds']['amman_share'])}")
    print(f"Peak Day: {kpis['peak_day']}")
    print(f"Retention: {kpis['retention']:.1f}% (Target: {config['thresholds']['retention']}%) - {get_status(kpis['retention'], config['thresholds']['retention'])}")

    # Create and save dashboard
    fig = create_gauge_dashboard(kpis, config)
    fig.write_html("output/kpi_monitor_dashboard.html")
    print("Monitoring dashboard saved to output/kpi_monitor_dashboard.html")


if __name__ == "__main__":
    main()