# KPI Framework — Amman Digital Market

This document defines the 5 core Key Performance Indicators (KPIs) used to monitor the health and growth of the Amman Digital Market platform.

---

## KPI 1: Monthly Revenue Growth (Time-Based)

- **Name:** MoM (Month-over-Month) Revenue Growth
- **Definition:** The percentage change in total sales value compared to the previous month.
- **Formula:** `((Current Month Revenue - Previous Month Revenue) / Previous Month Revenue) * 100`
- **Data Source (tables/columns):** - `order_items`: `quantity`, `unit_price`
    - `orders`: `order_date`
- **Baseline Value:** 15%
- **Interpretation:** Indicates market expansion and demand trends. Positive growth confirms successful marketing and product-market fit in Jordan.

---

## KPI 2: Average Order Value (AOV)

- **Name:** Average Order Value (AOV)
- **Definition:** The average amount of money spent by a customer per single transaction.
- **Formula:** `Total Revenue / Total Number of Orders`
- **Data Source (tables/columns):**
    - `order_items`: `quantity`, `unit_price`
    - `orders`: `order_id`
- **Baseline Value:** 45 JOD
- **Interpretation:** Measures customer purchasing power. Tracking AOV helps determine if cross-selling or up-selling strategies are effective.

---

## KPI 3: Regional Market Share (City-Based)

- **Name:** Amman vs. Regional Revenue Concentration
- **Definition:** The percentage of total platform revenue generated specifically by customers residing in Amman.
- **Formula:** `(Total Revenue from Amman Customers / Total Revenue) * 100`
- **Data Source (tables/columns):**
    - `order_items`: `quantity`, `unit_price`
    - `customers`: `city`
    - `orders`: `customer_id`
- **Baseline Value:** 65%
- **Interpretation:** Determines geographical dominance. A high percentage confirms Amman is the primary hub, while growth in Irbid or Zarqa would indicate successful regional scaling.

---

## KPI 4: Weekly Sales Velocity (Time-Based)

- **Name:** Peak Day Sales Volume
- **Definition:** Identifying the day of the week with the highest frequency of order completions.
- **Formula:** `MAX(Count of Orders grouped by DAY_OF_WEEK(order_date))`
- **Data Source (tables/columns):**
    - `orders`: `order_date`, `status`
- **Baseline Value:** Thursday (Anticipated peak for local shopping behavior)
- **Interpretation:** Informs logistics and operational readiness. High velocity on specific days guides staffing for delivery drivers and customer support in Amman.

---

## KPI 5: 30-Day New Customer Retention (Cohort-Based)

- **Name:** First-Month Repeat Purchase Rate
- **Definition:** The percentage of new customers from a specific monthly cohort who return to make a second purchase within 30 days.
- **Formula:** `(Count of New Customers with > 1 Order in 30 Days / Total New Customers in Cohort) * 100`
- **Data Source (tables/columns):**
    - `orders`: `customer_id`, `order_date`
    - `customers`: `registration_date`
- **Baseline Value:** 20%
- **Interpretation:** A direct measure of platform "stickiness" and customer satisfaction. Lower rates signal a need for improved post-purchase engagement or loyalty programs.