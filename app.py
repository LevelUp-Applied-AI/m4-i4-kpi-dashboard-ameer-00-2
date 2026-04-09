"""Multi-Page Analytical Report with Plotly Dash

A Dash application with multiple pages for KPI analysis:
- Page 1: KPI overview with gauge indicators
- Page 2: Time-series deep dive with date range selector
- Page 3: Cohort comparison with drill-down capability

Includes callback functions for cross-filtering.
"""
import dash
from dash import html, dcc, Input, Output, State
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from sqlalchemy import create_engine
import os


# Data loading functions
def load_data():
    """Load and prepare data for the dashboard."""
    default_url = "postgresql://postgres:postgres@127.0.0.1:5432/amman_market"
    db_url = os.getenv("DATABASE_URL", default_url)
    engine = create_engine(db_url)

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

    df = pd.read_sql(query, engine)
    df['revenue'] = df['quantity'] * df['unit_price']
    df['order_date'] = pd.to_datetime(df['order_date'])
    df['registration_date'] = pd.to_datetime(df['registration_date'])
    df['month'] = df['order_date'].dt.to_period('M').astype(str)

    return df


# KPI computation functions
def compute_kpis(df, city_filter=None, date_from=None, date_to=None):
    """Compute KPIs with optional filters."""
    filtered_df = df.copy()

    if city_filter and city_filter != 'All':
        filtered_df = filtered_df[filtered_df['city'] == city_filter]

    if date_from:
        filtered_df = filtered_df[filtered_df['order_date'] >= pd.to_datetime(date_from)]
    if date_to:
        filtered_df = filtered_df[filtered_df['order_date'] <= pd.to_datetime(date_to)]

    # MoM Revenue Growth
    monthly_rev = filtered_df.groupby('month')['revenue'].sum()
    if len(monthly_rev) >= 2:
        current = monthly_rev.iloc[-1]
        previous = monthly_rev.iloc[-2]
        mom_growth = ((current - previous) / previous) * 100 if previous != 0 else 0
    else:
        mom_growth = 0

    # AOV
    aov = filtered_df.groupby('order_id')['revenue'].sum().mean()

    # Amman Share
    total_rev = filtered_df['revenue'].sum()
    amman_rev = filtered_df[filtered_df['city'] == 'Amman']['revenue'].sum()
    amman_share = (amman_rev / total_rev) * 100 if total_rev != 0 else 0

    # Peak Day
    filtered_df['day_of_week'] = filtered_df['order_date'].dt.day_name()
    weekly_velocity = filtered_df.groupby('day_of_week')['order_id'].nunique()
    peak_day = weekly_velocity.idxmax() if not weekly_velocity.empty else 'N/A'

    # 30-Day Retention
    new_customers = filtered_df[
        (filtered_df['registration_date'] >= filtered_df['order_date'].min() - pd.Timedelta(days=30)) &
        (filtered_df['registration_date'] <= filtered_df['order_date'].max())
    ]
    if not new_customers.empty:
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
    else:
        retention = 0

    return {
        'mom_growth': mom_growth,
        'aov': aov,
        'amman_share': amman_share,
        'peak_day': peak_day,
        'retention': retention,
        'monthly_rev': monthly_rev,
        'weekly_velocity': weekly_velocity,
        'filtered_df': filtered_df
    }


# Create Dash app
app = dash.Dash(__name__, suppress_callback_exceptions=True)

# App layout
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div([
        html.H1('Amman Digital Market Analytics Dashboard'),
        dcc.Tabs(id='tabs', value='overview', children=[
            dcc.Tab(label='KPI Overview', value='overview'),
            dcc.Tab(label='Time Series Deep Dive', value='timeseries'),
            dcc.Tab(label='Cohort Comparison', value='cohort'),
        ]),
        html.Div([
            html.Label('Filter by City:'),
            dcc.Dropdown(
                id='city-filter',
                options=[
                    {'label': 'All Cities', 'value': 'All'},
                    {'label': 'Amman', 'value': 'Amman'},
                    {'label': 'Irbid', 'value': 'Irbid'},
                    {'label': 'Zarqa', 'value': 'Zarqa'}
                ],
                value='All',
                clearable=False
            ),
            html.Label('Date Range:'),
            dcc.DatePickerRange(
                id='date-range',
                start_date='2023-01-01',
                end_date='2024-12-31'
            )
        ], style={'padding': '20px'})
    ]),
    html.Div(id='tab-content')
])


# Callbacks
@app.callback(
    Output('tab-content', 'children'),
    [Input('tabs', 'value'),
     Input('city-filter', 'value'),
     Input('date-range', 'start_date'),
     Input('date-range', 'end_date')]
)
def render_content(tab, city_filter, start_date, end_date):
    """Render content based on selected tab and filters."""
    # Load data (in production, cache this)
    df = load_data()
    kpis = compute_kpis(df, city_filter, start_date, end_date)

    if tab == 'overview':
        return html.Div([
            html.H2('KPI Overview'),
            html.Div([
                dcc.Graph(
                    id='kpi-gauges',
                    figure=create_kpi_gauges(kpis)
                )
            ])
        ])

    elif tab == 'timeseries':
        return html.Div([
            html.H2('Time Series Deep Dive'),
            dcc.Graph(
                id='revenue-timeseries',
                figure=create_revenue_timeseries(kpis)
            ),
            dcc.Graph(
                id='aov-timeseries',
                figure=create_aov_timeseries(kpis)
            )
        ])

    elif tab == 'cohort':
        return html.Div([
            html.H2('Cohort Comparison'),
            dcc.Graph(
                id='cohort-heatmap',
                figure=create_cohort_analysis(kpis)
            ),
            dcc.Graph(
                id='city-comparison',
                figure=create_city_comparison(kpis)
            )
        ])


def create_kpi_gauges(kpis):
    """Create gauge indicators for KPIs."""
    fig = make_subplots(
        rows=1, cols=5,
        specs=[[{'type': 'indicator'}, {'type': 'indicator'}, {'type': 'indicator'},
                {'type': 'indicator'}, {'type': 'indicator'}]],
        subplot_titles=['MoM Growth %', 'AOV (JOD)', 'Amman Share %', 'Peak Day', 'Retention %']
    )

    # MoM Growth
    fig.add_trace(
        go.Indicator(
            mode="gauge+number",
            value=kpis['mom_growth'],
            gauge={'axis': {'range': [0, 50]}},
            domain={'row': 0, 'column': 0}
        ),
        row=1, col=1
    )

    # AOV
    fig.add_trace(
        go.Indicator(
            mode="gauge+number",
            value=kpis['aov'],
            gauge={'axis': {'range': [0, 100]}},
            domain={'row': 0, 'column': 1}
        ),
        row=1, col=2
    )

    # Amman Share
    fig.add_trace(
        go.Indicator(
            mode="gauge+number",
            value=kpis['amman_share'],
            gauge={'axis': {'range': [0, 100]}},
            domain={'row': 0, 'column': 2}
        ),
        row=1, col=3
    )

    # Peak Day (number indicator)
    peak_orders = kpis['weekly_velocity'].get(kpis['peak_day'], 0) if kpis['peak_day'] != 'N/A' else 0
    fig.add_trace(
        go.Indicator(
            mode="number",
            value=peak_orders,
            title={"text": f"{kpis['peak_day']}"},
            domain={'row': 0, 'column': 3}
        ),
        row=1, col=4
    )

    # Retention
    fig.add_trace(
        go.Indicator(
            mode="gauge+number",
            value=kpis['retention'],
            gauge={'axis': {'range': [0, 50]}},
            domain={'row': 0, 'column': 4}
        ),
        row=1, col=5
    )

    fig.update_layout(height=400)
    return fig


def create_revenue_timeseries(kpis):
    """Create revenue time series chart."""
    monthly_rev = kpis['monthly_rev']
    fig = px.line(
        x=monthly_rev.index,
        y=monthly_rev.values,
        title='Monthly Revenue Trend',
        labels={'x': 'Month', 'y': 'Revenue (JOD)'}
    )
    return fig


def create_aov_timeseries(kpis):
    """Create AOV time series chart."""
    df = kpis['filtered_df']
    monthly_aov = df.groupby('month').apply(lambda x: x.groupby('order_id')['revenue'].sum().mean())
    fig = px.line(
        x=monthly_aov.index,
        y=monthly_aov.values,
        title='Monthly Average Order Value Trend',
        labels={'x': 'Month', 'y': 'AOV (JOD)'}
    )
    return fig


def create_cohort_analysis(kpis):
    """Create cohort analysis heatmap."""
    df = kpis['filtered_df']
    df['cohort_month'] = df['registration_date'].dt.to_period('M').astype(str)

    cohort_data = df.groupby(['cohort_month', 'month'])['revenue'].sum().unstack().fillna(0)

    fig = px.imshow(
        cohort_data,
        title='Revenue by Customer Cohort',
        labels={'x': 'Order Month', 'y': 'Registration Month', 'color': 'Revenue (JOD)'}
    )
    return fig


def create_city_comparison(kpis):
    """Create city comparison chart."""
    df = kpis['filtered_df']
    city_stats = df.groupby('city').agg({
        'revenue': 'sum',
        'order_id': 'nunique',
        'customer_id': 'nunique'
    }).reset_index()

    fig = px.bar(
        city_stats,
        x='city',
        y='revenue',
        title='Revenue by City',
        labels={'revenue': 'Total Revenue (JOD)', 'city': 'City'}
    )
    return fig


if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=8050)