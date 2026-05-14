# Power BI Dashboard Setup Guide

This guide explains how to set up the Power BI dashboard for the Mumbai Quick Commerce project using the enriched dataset.

## Data Source
Load `data/processed/mumbai_qcommerce_enriched.csv` into Power BI Desktop.

## DAX Measures

Create the following measures in your data model:

```dax
Total GMV = SUM(orders[Order_Value])

Total Profit = SUM(orders[Profit])

Profit Margin % = DIVIDE([Total Profit], [Total GMV]) * 100

Avg Delivery Time = AVERAGE(orders[Delivery_Time_Min])

On Time % = DIVIDE(COUNTROWS(FILTER(orders, orders[Delivery_Time_Min] <= 15)), COUNTROWS(orders)) * 100

Loss Making Orders = COUNTROWS(FILTER(orders, orders[Profit] < 0))

Discount Rate = DIVIDE(SUM(orders[Discount_Amount]), SUM(orders[Order_Value])) * 100
```

## Dashboard Pages Structure

### Page 1: Executive Overview
- **KPI Cards:** Total GMV, Total Profit, Profit Margin %, Total Orders, Avg Delivery Time
- **Chart:** Blinkit vs Zepto comparison bar chart
- **Chart:** Monthly GMV trend line (YoY style)

### Page 2: Delivery Performance
- **Visual:** Avg delivery time by zone (Map or Bar)
- **Chart:** Peak vs off-peak delivery time comparison
- **Gauge:** On-time delivery %
- **Scatter:** Distance vs delivery time

### Page 3: Product & Category Insights
- **Treemap:** GMV by category
- **Bar Chart:** Profit margin by category
- **Visual:** Discount applied % by category
- **Table:** Top 10 / Bottom 10 categories by profit

### Page 4: Dark Store & Regional Analysis
- **Table:** Dark store performance (GMV, Orders, Avg Rating, Profit)
- **Heatmap:** Zone-wise order concentration
- **Visual:** Peak hour utilization by store

### Page 5: Recommendations & What-If
- **Cards:** Summary of the 6 strategic recommendations
- **Slider/Parameter:** What-if scenario: "If we reduce discounts by X% → profit increases by Y"
- **Visual:** Churn risk customer count and estimated LTV at stake
