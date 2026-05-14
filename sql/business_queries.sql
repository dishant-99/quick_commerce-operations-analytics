/*
===============================================================================
SQL QUERIES: Mumbai Q-Commerce Profitability & Operations
===============================================================================
Database: SQLite / Data Warehouse
Table: orders (from mumbai_qcommerce_enriched.csv)
*/

-- 1. Total GMV and profit by company
SELECT 
    Company,
    SUM(Order_Value) AS Total_GMV,
    SUM(Profit) AS Total_Profit,
    ROUND((SUM(Profit) / SUM(Order_Value)) * 100, 2) AS Profit_Margin_Pct
FROM orders
GROUP BY Company;

-- 2. Average delivery time by zone and peak/off-peak
SELECT 
    Mumbai_Zone,
    Is_Peak_Hour,
    ROUND(AVG(Delivery_Time_Min), 2) AS Avg_Delivery_Time_Min,
    COUNT(Order_ID) AS Total_Orders
FROM orders
GROUP BY Mumbai_Zone, Is_Peak_Hour
ORDER BY Mumbai_Zone, Is_Peak_Hour;

-- 3. Top 5 dark stores by GMV
SELECT 
    Dark_Store_ID,
    Mumbai_Zone,
    SUM(Order_Value) AS Total_GMV
FROM orders
GROUP BY Dark_Store_ID, Mumbai_Zone
ORDER BY Total_GMV DESC
LIMIT 5;

-- 4. Bottom 5 dark stores by profit margin
SELECT 
    Dark_Store_ID,
    Mumbai_Zone,
    SUM(Order_Value) AS Total_GMV,
    SUM(Profit) AS Total_Profit,
    ROUND((SUM(Profit) / SUM(Order_Value)) * 100, 2) AS Profit_Margin_Pct
FROM orders
GROUP BY Dark_Store_ID, Mumbai_Zone
ORDER BY Profit_Margin_Pct ASC
LIMIT 5;

-- 5. Discount impact: avg profit when discounted vs not discounted, by category
SELECT 
    Product_Category,
    Discount_Applied,
    COUNT(Order_ID) AS Order_Count,
    ROUND(AVG(Profit), 2) AS Avg_Profit,
    ROUND(AVG(Order_Value), 2) AS Avg_Order_Value
FROM orders
GROUP BY Product_Category, Discount_Applied
ORDER BY Product_Category, Discount_Applied;

-- 6. Orders beyond 4.5km — count, avg profit, total loss
SELECT 
    COUNT(Order_ID) AS Long_Distance_Orders,
    ROUND(AVG(Profit), 2) AS Avg_Profit_Per_Order,
    SUM(CASE WHEN Profit < 0 THEN Profit ELSE 0 END) AS Total_Loss_From_Negative_Orders
FROM orders
WHERE Distance_Km > 4.5;

-- 7. Peak hour order surge — orders per hour
SELECT 
    Order_Hour,
    Is_Peak_Hour,
    COUNT(Order_ID) AS Total_Orders,
    ROUND(AVG(Delivery_Time_Min), 2) AS Avg_Delivery_Time_Min
FROM orders
GROUP BY Order_Hour, Is_Peak_Hour
ORDER BY Order_Hour;

-- 8. Category performance: revenue, profit, margin% ranked
SELECT 
    Product_Category,
    SUM(Order_Value) AS Total_Revenue,
    SUM(Profit) AS Total_Profit,
    ROUND((SUM(Profit) / SUM(Order_Value)) * 100, 2) AS Profit_Margin_Pct
FROM orders
GROUP BY Product_Category
ORDER BY Profit_Margin_Pct DESC;

-- 9. Churn risk customers — count by zone and company
SELECT 
    Company,
    Mumbai_Zone,
    COUNT(Order_ID) AS Churn_Risk_Customers
FROM orders
WHERE Churn_Risk_Flag = 1 OR Churn_Risk_Flag = 'True'
GROUP BY Company, Mumbai_Zone
ORDER BY Churn_Risk_Customers DESC;

-- 10. Rider efficiency: avg orders per rider per zone (proxy)
SELECT 
    Mumbai_Zone,
    Rider_ID,
    COUNT(Order_ID) AS Total_Orders_Handled
FROM orders
GROUP BY Mumbai_Zone, Rider_ID
ORDER BY Total_Orders_Handled DESC;

-- 11. Monthly GMV trend (YoY style since we have 2023-2024)
SELECT 
    Order_Month,
    SUM(Order_Value) AS Monthly_GMV,
    COUNT(Order_ID) AS Total_Orders
FROM orders
GROUP BY Order_Month
ORDER BY Order_Month;

-- 12. Payment method split and avg order value by method
SELECT 
    Payment_Method,
    COUNT(Order_ID) AS Total_Orders,
    ROUND(COUNT(Order_ID) * 100.0 / SUM(COUNT(Order_ID)) OVER (), 2) AS Order_Pct,
    ROUND(AVG(Order_Value), 2) AS Avg_Order_Value
FROM orders
GROUP BY Payment_Method
ORDER BY Total_Orders DESC;
