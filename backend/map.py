import pandas as pd
from pathlib import Path

# Define data directory path
DATA = Path(__file__).parent / "data"

lines = pd.read_csv(DATA / "lines.csv")           # columns: name, bus0, bus1, s_nom, conductor, MOT, branch_name, ...
flows = pd.read_csv(DATA / "line_flows_nominal.csv")  # columns: name, p0_nominal
buses = pd.read_csv(DATA / "buses.csv")           # columns: name (bus id), v_nom (kV), etc.

# sanity checks
lines.head(), flows.head(), buses.head()
# Attach v_nom to both endpoints (they should match)
bus_cols = buses[["name","v_nom"]].rename(columns={"name":"bus0"})
lines_bus0 = lines.merge(bus_cols, on="bus0", how="left").rename(columns={"v_nom":"v_nom0"})

bus_cols = buses[["name","v_nom"]].rename(columns={"name":"bus1"})
lines_full = lines_bus0.merge(bus_cols, on="bus1", how="left").rename(columns={"v_nom":"v_nom1"})

# By definition, v_nom0 == v_nom1 for a line. Keep one and assert.
lines_full["v_nom"] = lines_full["v_nom0"].fillna(lines_full["v_nom1"])
assert (lines_full["v_nom0"].fillna(lines_full["v_nom1"]) == lines_full["v_nom1"].fillna(lines_full["v_nom0"])).all()

lines_full = lines_full.drop(columns=["v_nom0","v_nom1"])
lines_full[["name","bus0","bus1","v_nom","s_nom","conductor","MOT"]].head()
base = lines_full.merge(flows, on="name", how="left")
base["loading_pct_nominal"] = 100 * base["p0_nominal"] / base["s_nom"]
base[["name","p0_nominal","s_nom","loading_pct_nominal"]].sort_values("loading_pct_nominal", ascending=False).head(10)

import math
import ieee738
from ieee738 import ConductorParams

# 4.1 load conductor library
clib = pd.read_csv(DATA / "conductor_library.csv")  # ConductorName, RES_25C, RES_50C, CDRAD_IN, CDGMR_ft (not used)
clib = clib.rename(columns={
    "ConductorName":"conductor",
    "RES_25C":"RES_25C_ohm_per_mi",
    "RES_50C":"RES_50C_ohm_per_mi",
    "CDRAD_in":"CDRAD_IN"
})

# 4.2 ambient defaults (tune these per scenario)
ambient_defaults = {
    'Ta': 25,                # degC
    'WindVelocity': 2.0,     # ft/s  (careful: many APIs return m/s; convert if needed)
    'WindAngleDeg': 90,      # crosswind
    'SunTime': 12,           # noon worst-case solar
    'Date': '12 Jun',
    'Emissivity': 0.8,
    'Absorptivity': 0.8,
    'Direction': 'EastWest',
    'Atmosphere': 'Clear',
    'Elevation': 1000,
    'Latitude': 27,
}

def amps_to_mva(i_amps: float, v_kv: float) -> float:
    return math.sqrt(3) * i_amps * (v_kv*1e3) * 1e-6

# 4.3 build a function to compute rating MVA for a single line given ambient
def compute_ieee738_rating_mva_for_line(line_row, ambient=ambient_defaults):
    """
    line_row: a pandas row with fields conductor, MOT, v_nom (kV)
    returns: rating_mva (float)
    """
    c = clib.loc[clib["conductor"]==line_row["conductor"]].iloc[0]

    # Convert manufacturer ohm/mi → ohm/ft for the ieee kernel
    RLo = c["RES_25C_ohm_per_mi"] / 5280.0
    RHi = c["RES_50C_ohm_per_mi"] / 5280.0

    # The kernel expects "Diameter" (inches) not radius; datasheet gave radius (inches)
    diameter_in = 2.0 * c["CDRAD_IN"]

    params = dict(ambient)
    params.update({
        "TLo": 25, "THi": 50, "RLo": RLo, "RHi": RHi,
        "Diameter": diameter_in,
        "Tc": float(line_row["MOT"])  # Maximum operating temp (degC)
    })

    cp = ConductorParams(**params)
    con = ieee738.Conductor(cp)
    rating_amps = con.steady_state_thermal_rating()

    return amps_to_mva(rating_amps, line_row["v_nom"])

scenario = base.copy()
scenario["s_nom_ieee738_mva"] = scenario.apply(lambda r: compute_ieee738_rating_mva_for_line(r, ambient_defaults), axis=1)

# Compare the IEEE-738 recomputed rating vs provided s_nom
scenario["loading_pct_ieee738"] = 100 * scenario["p0_nominal"] / scenario["s_nom_ieee738_mva"]
scenario[["name","p0_nominal","s_nom","s_nom_ieee738_mva","loading_pct_ieee738"]].head()

def run_scenario(lines_flows_df, ambient, thresholds=(90, 60)):
    """
    thresholds: (critical, caution) percent loading thresholds.
    Returns a DataFrame with loading and severity labels.
    """
    df = lines_flows_df.copy()
    df["s_nom_ieee738_mva"] = df.apply(lambda r: compute_ieee738_rating_mva_for_line(r, ambient), axis=1)
    df["loading_pct"] = 100 * df["p0_nominal"] / df["s_nom_ieee738_mva"]

    crit, caution = thresholds
    def label(p):
        if p >= crit: return "CRITICAL (≥{}%)".format(crit)
        if p >= caution: return "CAUTION ({}–{}%)".format(caution, crit)
        return "NOMINAL (<{}%)".format(caution)

    df["severity"] = df["loading_pct"].apply(label)
    return df.sort_values("loading_pct", ascending=False)

# Example: hot & low wind @ 2pm (SunTime=14)
hot_lowwind = dict(ambient_defaults, Ta=70, WindVelocity=2, SunTime=12)
out = run_scenario(base, hot_lowwind)

# Select key columns and save
cols = ["name", "p0_nominal", "s_nom_ieee738_mva", "loading_pct", "severity"]
out[cols].to_csv(DATA / "scenario_results.csv", index=False)
print("Saved results to scenario_results.csv")



import geopandas as gpd

# Load GIS and your computed results
gis = gpd.read_file(DATA / "oneline_lines.geojson")
data = pd.read_csv(DATA / "scenario_results.csv")  # your computed data

# Merge on line name
merged = gis.merge(data, left_on="Name", right_on="name")

# Save for visualization
merged.to_file(DATA / "merged_lines.geojson", driver="GeoJSON")

from shapely.geometry import Point
import re

# Create buses GeoDataFrame from the buses CSV data
buses_clean = gpd.GeoDataFrame(
    buses, 
    geometry=gpd.points_from_xy(buses['x'], buses['y']),
    crs='EPSG:4326'
)

# --- 1. Clean and normalize names ---
buses_clean["BusName"] = (
    buses_clean["BusName"]
    .astype(str)
    .str.strip()
    .str.upper()
    .str.replace(r"\s+", "", regex=True)
)

# --- 2. Add prefix column (first 5 chars) ---
buses_clean["Prefix"] = buses_clean["BusName"].str[:5]

# --- 3. Project to local metric CRS for Hawaii ---
buses_proj = buses_clean.to_crs(epsg=3759)

# --- 4. Merge by prefix within ~100 m ---
unique_rows = []
used = set()
tolerance_m = 100  # 100 meters

for prefix, group in buses_proj.groupby("Prefix"):
    # group might include multiple coordinates/kV variants
    x_mean = group.geometry.x.mean()
    y_mean = group.geometry.y.mean()
    new_geom = Point(x_mean, y_mean)
    kvs = sorted(set(group["v_nom"].astype(int)))
    unique_rows.append({
        "BusName": prefix,
        "kV": kvs,
        "geometry": new_geom
    })
    used.add(prefix)

# --- 5. Rebuild GeoDataFrame ---
buses_dedup = gpd.GeoDataFrame(unique_rows, geometry="geometry", crs=3759).to_crs(epsg=4326)

print(f"✅ Reduced {len(buses_clean)} → {len(buses_dedup)} unique sites.")


import folium
from folium.plugins import MarkerCluster

m = folium.Map(location=[20.9, -157.5], zoom_start=7, tiles="cartodbpositron")

def color(row):
    if "CRITICAL" in row["severity"]:
        return "red"
    elif "CAUTION" in row["severity"]:
        return "orange"
    else:
        return "green"

for _, row in merged.iterrows():
    folium.GeoJson(
        row["geometry"],
        style_function=lambda x, color=color(row): {"color": color, "weight": 3},
        tooltip=f"{row['name']}: {row['loading_pct']:.1f}%"
    ).add_to(m)

marker_cluster = MarkerCluster().add_to(m)

for _, row in buses_dedup.iterrows():
    lat, lon = row.geometry.y, row.geometry.x
    popup = f"<b>{row['BusName']}</b><br>{row['kV']} kV"
    folium.CircleMarker(
        location=[lat, lon],
        radius=5,
        color="blue" if 69 in row["kV"] else "purple",
        fill=True,
        fill_opacity=0.8,
        popup=popup,
        tooltip=row["BusName"]
    ).add_to(marker_cluster)

m.save(DATA / "line_map.html")