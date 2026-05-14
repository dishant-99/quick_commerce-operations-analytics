import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os

# Reproducibility
np.random.seed(42)
random.seed(42)

print("=" * 60)
print("  Q-COMMERCE DATA PREP: Mumbai Operations Dataset Builder")
print("=" * 60)

# =============================================================================
# STEP 1: LOAD RAW DATA
# =============================================================================
print("\n[1/7] Loading raw dataset...")

RAW_PATH = "data/raw/qcommerce_raw.csv"
OUTPUT_PATH = "data/processed/mumbai_qcommerce_enriched.csv"

os.makedirs("data/processed", exist_ok=True)

try:
    df = pd.read_csv(RAW_PATH)
    print(f"    ✓ Loaded {len(df):,} rows, {df.shape[1]} columns")
except FileNotFoundError:
    print(f"    ✗ ERROR: File not found at {RAW_PATH}")
    print("    → Download from: https://www.kaggle.com/datasets/rohitgrewal/quick-commerce-dataset")
    print("    → Save as: data/raw/qcommerce_raw.csv")
    exit(1)

# =============================================================================
# STEP 2: FILTER — Mumbai + Blinkit/Zepto only
# =============================================================================
print("\n[2/7] Filtering to Mumbai + Blinkit & Zepto...")

df_filtered = df[
    (df['City'].str.strip() == 'Mumbai') &
    (df['Company'].str.strip().isin(['Blinkit', 'Zepto']))
].copy()

df_filtered.reset_index(drop=True, inplace=True)
print(f"    ✓ Filtered to {len(df_filtered):,} rows")
print(f"    ✓ Blinkit: {len(df_filtered[df_filtered.Company == 'Blinkit']):,} orders")
print(f"    ✓ Zepto:   {len(df_filtered[df_filtered.Company == 'Zepto']):,} orders")

n = len(df_filtered)

# =============================================================================
# STEP 3: ENGINEER — Order Timestamps (2023-01-01 to 2024-12-31)
# =============================================================================
print("\n[3/7] Engineering timestamps with realistic distribution...")

def generate_timestamps(n):
    """
    Generate realistic order timestamps:
    - More orders on weekends (Fri/Sat/Sun)
    - Peaks at 12-2pm (lunch) and 7-10pm (dinner/evening)
    - Lower volume 2am-8am
    """
    base_date = datetime(2023, 1, 1)
    total_days = 730  # 2 years

    timestamps = []

    # Hour weights (0-23): simulate real Q-commerce demand curve
    hour_weights = [
        0.5, 0.3, 0.2, 0.1, 0.1, 0.2,  # 0-5am (dead zone)
        0.4, 0.8, 1.2, 1.5, 1.8, 2.0,  # 6-11am (morning ramp)
        3.0, 3.5, 2.8, 2.0, 1.8, 2.0,  # 12-5pm (lunch peak, afternoon)
        2.5, 3.8, 4.0, 3.5, 2.5, 1.5   # 6-11pm (evening peak, taper)
    ]
    hour_weights = np.array(hour_weights)
    hour_weights = hour_weights / hour_weights.sum()

    for _ in range(n):
        day_offset = random.randint(0, total_days - 1)
        hour = np.random.choice(24, p=hour_weights)
        minute = random.randint(0, 59)
        second = random.randint(0, 59)
        ts = base_date + timedelta(days=day_offset, hours=int(hour),
                                   minutes=minute, seconds=second)
        timestamps.append(ts)

    return timestamps

df_filtered['Order_Timestamp'] = generate_timestamps(n)
df_filtered['Order_Hour'] = df_filtered['Order_Timestamp'].dt.hour
df_filtered['Order_DayOfWeek'] = df_filtered['Order_Timestamp'].dt.day_name()
df_filtered['Order_Month'] = df_filtered['Order_Timestamp'].dt.to_period('M').astype(str)
df_filtered['Order_Quarter'] = df_filtered['Order_Timestamp'].dt.to_period('Q').astype(str)
print(f"    ✓ Timestamps generated: {df_filtered['Order_Timestamp'].min()} → {df_filtered['Order_Timestamp'].max()}")

# =============================================================================
# STEP 4: ENGINEER — Mumbai Zones + Dark Stores
# =============================================================================
print("\n[4/7] Mapping to Mumbai zones and dark stores...")

# Zone distribution weights (based on population density & order density)
zones = ['Andheri', 'Bandra', 'Powai', 'Thane', 'Kurla',
         'Borivali', 'Malad', 'Dadar', 'Juhu', 'Navi Mumbai',
         'Chembur', 'Colaba']

zone_weights = [0.15, 0.12, 0.10, 0.10, 0.08,
                0.08, 0.07, 0.07, 0.06, 0.06,
                0.06, 0.05]

# Dark store mapping (one per zone)
zone_to_darkstore = {
    'Andheri':    'DS_001',
    'Bandra':     'DS_002',
    'Powai':      'DS_003',
    'Thane':      'DS_004',
    'Kurla':      'DS_005',
    'Borivali':   'DS_006',
    'Malad':      'DS_007',
    'Dadar':      'DS_008',
    'Juhu':       'DS_009',
    'Navi Mumbai':'DS_010',
    'Chembur':    'DS_011',
    'Colaba':     'DS_012',
}

df_filtered['Mumbai_Zone'] = np.random.choice(zones, size=n, p=zone_weights)
df_filtered['Dark_Store_ID'] = df_filtered['Mumbai_Zone'].map(zone_to_darkstore)

# Pincode mapping (representative pincodes per zone)
zone_to_pincode = {
    'Andheri': '400053', 'Bandra': '400050', 'Powai': '400076',
    'Thane': '400601', 'Kurla': '400070', 'Borivali': '400066',
    'Malad': '400064', 'Dadar': '400014', 'Juhu': '400049',
    'Navi Mumbai': '400703', 'Chembur': '400071', 'Colaba': '400005'
}
df_filtered['Pincode'] = df_filtered['Mumbai_Zone'].map(zone_to_pincode)

print(f"    ✓ Zones assigned. Top zone: {df_filtered['Mumbai_Zone'].value_counts().index[0]}")
print(f"    ✓ Dark stores: {df_filtered['Dark_Store_ID'].nunique()} active")

# =============================================================================
# STEP 5: ENGINEER — Rider IDs
# =============================================================================
print("\n[5/7] Assigning Rider IDs (300 riders across 12 zones)...")

# Each zone gets ~25 riders assigned to it (realistic pool)
def assign_rider(zone):
    zone_idx = zones.index(zone)
    rider_pool_start = (zone_idx * 25) + 1
    rider_pool_end = rider_pool_start + 24
    rider_num = random.randint(rider_pool_start, rider_pool_end)
    return f"R_{rider_num:03d}"

df_filtered['Rider_ID'] = df_filtered['Mumbai_Zone'].apply(assign_rider)
print(f"    ✓ {df_filtered['Rider_ID'].nunique()} unique riders assigned")

# =============================================================================
# STEP 6: ENGINEER — Financial Columns
# =============================================================================
print("\n[6/7] Engineering financial features (cost, margin, profit)...")

# --- Delivery Cost: ₹12/km base + ₹5 flat fee ---
df_filtered['Distance_Km'] = pd.to_numeric(df_filtered['Distance_Km'], errors='coerce')
df_filtered['Distance_Km'].fillna(df_filtered['Distance_Km'].median(), inplace=True)
df_filtered['Delivery_Cost'] = (df_filtered['Distance_Km'] * 12 + 5).round(2)

# --- Discount Amount ---
df_filtered['Order_Value'] = pd.to_numeric(df_filtered['Order_Value'], errors='coerce')
df_filtered['Order_Value'].fillna(df_filtered['Order_Value'].median(), inplace=True)

discount_rates = np.where(
    df_filtered['Discount_Applied'] == 1,
    np.random.uniform(0.05, 0.35, size=n),
    0.0
)
df_filtered['Discount_Amount'] = (df_filtered['Order_Value'] * discount_rates).round(2)
df_filtered['Discount_Pct'] = (discount_rates * 100).round(1)

# --- COGS Proxy (category-specific gross margins) ---
# Lower number = more of revenue goes to cost
category_cogs_pct = {
    'Groceries':          0.65,
    'Dairy':              0.62,
    'Beverages':          0.55,
    'Snacks':             0.48,
    'Personal Care':      0.38,
    'Household':          0.45,
    'Fruits & Vegetables':0.68,
    'Meat & Seafood':     0.65,
    'Frozen Foods':       0.55,
    'Baby Care':          0.40,
}
default_cogs = 0.55
df_filtered['COGS_Proxy'] = df_filtered['Product_Category'].map(
    category_cogs_pct
).fillna(default_cogs)
df_filtered['COGS_Amount'] = (df_filtered['Order_Value'] * df_filtered['COGS_Proxy']).round(2)

# --- Net Profit ---
# Profit = Revenue - Discount Given - COGS - Delivery Cost
df_filtered['Profit'] = (
    df_filtered['Order_Value']
    - df_filtered['Discount_Amount']
    - df_filtered['COGS_Amount']
    - df_filtered['Delivery_Cost']
).round(2)

# --- Profit Margin % ---
df_filtered['Profit_Margin_Pct'] = (
    df_filtered['Profit'] / df_filtered['Order_Value'] * 100
).round(2)

print(f"    ✓ Avg Order Value:  ₹{df_filtered['Order_Value'].mean():.0f}")
print(f"    ✓ Avg Profit:       ₹{df_filtered['Profit'].mean():.0f}")
print(f"    ✓ Loss-making orders: {(df_filtered['Profit'] < 0).sum():,} ({(df_filtered['Profit'] < 0).mean()*100:.1f}%)")

# =============================================================================
# STEP 7: ENGINEER — Operational Flag Columns
# =============================================================================
print("\n[7/7] Engineering operational flag columns...")

# --- Peak Hour Flag ---
peak_hours = [12, 13, 19, 20, 21]  # Lunch + Evening peaks
df_filtered['Is_Peak_Hour'] = df_filtered['Order_Hour'].isin(peak_hours)

# --- Basket Size Tier ---
df_filtered['Items_Count'] = pd.to_numeric(df_filtered['Items_Count'], errors='coerce').fillna(3)
df_filtered['Basket_Size_Tier'] = pd.cut(
    df_filtered['Items_Count'],
    bins=[0, 3, 7, float('inf')],
    labels=['Small', 'Medium', 'Large']
)

# --- Churn Risk Flag ---
df_filtered['Customer_Rating'] = pd.to_numeric(df_filtered['Customer_Rating'], errors='coerce')
df_filtered['Customer_Rating'].fillna(df_filtered['Customer_Rating'].median(), inplace=True)
df_filtered['Churn_Risk_Flag'] = df_filtered['Customer_Rating'] <= 2

# --- Delivery Partner Rating cleanup ---
df_filtered['Delivery_Partner_Rating'] = pd.to_numeric(
    df_filtered['Delivery_Partner_Rating'], errors='coerce'
)
df_filtered['Delivery_Partner_Rating'].fillna(
    df_filtered['Delivery_Partner_Rating'].median(), inplace=True
)

# --- On-Time Delivery Flag (≤15 min = on time for Q-commerce) ---
df_filtered['Delivery_Time_Min'] = pd.to_numeric(
    df_filtered['Delivery_Time_Min'], errors='coerce'
)
df_filtered['Delivery_Time_Min'].fillna(df_filtered['Delivery_Time_Min'].median(), inplace=True)
df_filtered['Is_On_Time'] = df_filtered['Delivery_Time_Min'] <= 15

# --- Stockout Risk Flag ---
high_velocity_categories = ['Dairy', 'Groceries', 'Snacks', 'Beverages']
stockout_random = np.random.random(n)
df_filtered['Stockout_Risk'] = (
    df_filtered['Is_Peak_Hour'] &
    df_filtered['Product_Category'].isin(high_velocity_categories) &
    (stockout_random < 0.28)  # 28% of peak-hour high-velocity orders risk stockout
)

# --- Loss Making Order Flag ---
df_filtered['Is_Loss_Making'] = df_filtered['Profit'] < 0

# --- Long Distance Flag (our key finding threshold) ---
df_filtered['Is_Long_Distance'] = df_filtered['Distance_Km'] > 4.5

# =============================================================================
# FINAL: SAVE + SUMMARY
# =============================================================================
# Sort by timestamp
df_filtered.sort_values('Order_Timestamp', inplace=True)
df_filtered.reset_index(drop=True, inplace=True)

# Save
df_filtered.to_csv(OUTPUT_PATH, index=False)

print("\n" + "=" * 60)
print("  ✅ ENRICHED DATASET SAVED SUCCESSFULLY")
print("=" * 60)
print(f"\n  📁 Output: {OUTPUT_PATH}")
print(f"  📊 Shape:  {df_filtered.shape[0]:,} rows × {df_filtered.shape[1]} columns")
print(f"\n  COLUMN SUMMARY:")
print(f"  {'Column':<30} {'Non-Null':>10} {'Dtype':>12}")
print(f"  {'-'*55}")
for col in df_filtered.columns:
    print(f"  {col:<30} {df_filtered[col].notna().sum():>10,} {str(df_filtered[col].dtype):>12}")

print(f"\n  KEY BUSINESS METRICS:")
print(f"  Total GMV:              ₹{df_filtered['Order_Value'].sum():>12,.0f}")
print(f"  Total Profit:           ₹{df_filtered['Profit'].sum():>12,.0f}")
print(f"  Overall Margin:          {df_filtered['Profit'].sum()/df_filtered['Order_Value'].sum()*100:>11.1f}%")
print(f"  Avg Delivery Time:       {df_filtered['Delivery_Time_Min'].mean():>10.1f} min")
print(f"  On-Time Delivery %:      {df_filtered['Is_On_Time'].mean()*100:>10.1f}%")
print(f"  Loss-Making Orders:      {df_filtered['Is_Loss_Making'].sum():>10,}")
print(f"  Churn Risk Customers:    {df_filtered['Churn_Risk_Flag'].sum():>10,}")
print(f"  Stockout Risk Orders:    {df_filtered['Stockout_Risk'].sum():>10,}")
print(f"\n  COMPANY SPLIT:")
for company, grp in df_filtered.groupby('Company'):
    margin = grp['Profit'].sum() / grp['Order_Value'].sum() * 100
    print(f"  {company}: {len(grp):,} orders | GMV ₹{grp['Order_Value'].sum():,.0f} | Margin {margin:.1f}%")

print("\n  ✅ Ready for analysis. Open notebooks/qcommerce_analysis.ipynb next.\n")
