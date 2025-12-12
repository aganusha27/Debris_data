import pandas as pd
import numpy as np
from datetime import datetime
import random
import re

# ============================
# INPUT / OUTPUT FILES
# ============================
IN_CSV = "data/Sheet1-Table 1.csv"
OUT_CSV = "data/norad_mass_dataset_500.csv"
OUT_XLSX = "data/norad_mass_dataset_500.xlsx"

# ============================
# MATERIAL POOL (Version B)
# ============================
MATERIAL_POOL = [
    "Aluminum Alloy 6061",
    "Aluminum Alloy 7075",
    "Aluminum Alloy 2024",
    "Titanium Alloy Ti-6Al-4V",
    "Titanium Alloy Ti-5Al-2.5Sn",
    "Stainless Steel 304",
    "Stainless Steel 316",
    "Inconel 718",
    "Inconel 625",
    "Magnesium Alloy AZ31",
    "Magnesium Alloy AZ80",
    "Carbon Fiber Reinforced Polymer",
    "Glass Fiber Reinforced Polymer",
    "Kevlar Composite",
    "Epoxy Composite",
    "Phenolic Composite",
    "Multi-Layer Insulation Foil",
    "Kapton Polyimide",
    "Nomex Honeycomb",
    "CFRP Honeycomb",
    "Aluminum Honeycomb",
    "Copper Wiring",
    "Gold Plating",
    "Silver Coating",
    "Teflon (PTFE)",
    "PEEK Polymer",
    "Polyethylene (HDPE)",
    "Polypropylene",
    "Silicone Elastomer",
    "Fused Silica",
    "Quartz Glass",
    "Borosilicate Glass",
    "Silicon Semiconductor",
    "GaAs Semiconductor",
    "Lithium-Ion Battery Cells",
    "Nickel-Hydrogen Battery Cells",
    "Solar Cell Silicon",
    "Gallium Nitride (GaN)",
    "Indium Phosphide (InP)",
    "Solder Alloy Sn-Pb",
    "Solder Alloy SAC305",
    "PCB FR-4 Substrate",
    "CFRP Structural Tubes",
    "Beryllium Structure",
    "Beryllium-Copper Alloy",
    "Tungsten Masses",
    "Molybdenum Structure",
    "Niobium Alloy",
    "Rhenium Alloy",
    "Ceramic Thermal Tiles"
]

# ============================
# DRY MASS ESTIMATION FUNCTION
# ============================
def compute_dry_mass(mass, orbit_type):
    try:
        m = float(mass)
    except:
        return None

    if orbit_type == "LEO":
        return round(m * 0.72, 3)
    elif orbit_type == "MEO":
        return round(m * 0.65, 3)
    elif orbit_type == "GEO":
        return round(m * 0.50, 3)
    else:
        return round(m * 0.70, 3)


# ============================
# LOAD CSV
# ============================
df = pd.read_csv(IN_CSV, encoding="utf-8", low_memory=False)

# ============================
# HELPER: FIND COLUMN BY KEYWORDS
# ============================
def find_col(df, keywords):
    for k in keywords:
        for c in df.columns:
            if k.lower() in str(c).lower():
                return c
    return None

# Identify required columns
col_norad    = find_col(df, ["norad"])
col_mass     = find_col(df, ["launch mass"])
col_date     = find_col(df, ["date of launch", "launch date", "date"])
col_name     = find_col(df, ["name"])
col_perigee  = find_col(df, ["perigee"])
col_apogee   = find_col(df, ["apogee"])
col_incl     = find_col(df, ["inclination"])
col_operator = find_col(df, ["operator"])
col_country  = find_col(df, ["country"])
col_purpose  = find_col(df, ["purpose"])
col_bus      = find_col(df, ["bus", "contractor", "manufacturer"])

# Basic validation
if col_norad is None or col_mass is None:
    raise SystemExit("ERROR: NORAD or Launch Mass column not found.")

# ============================
# HELPER: PARSE DATE (M2)
# ============================
def parse_date_val(x):
    if pd.isna(x):
        return None
    try:
        dt = pd.to_datetime(x, errors='coerce')
        if not pd.isna(dt):
            return dt
    except:
        pass

    s = str(x)
    m = re.search(r"(19|20)\d{2}", s)
    if m:
        y = int(m.group(0))
        return datetime(y, 1, 1)

    return None


# ============================
# FILTER + PARSE DATES
# ============================
df2 = df[df[col_norad].notna() & df[col_mass].notna()].copy()
df2["launch_datetime"] = df2[col_date].apply(parse_date_val)
df2 = df2[df2["launch_datetime"].notna()]

# ============================
# ORBIT TYPE ESTIMATION
# ============================
def compute_orbit_type(ap, pe):
    try:
        apf = float(ap) if not pd.isna(ap) else np.nan
        pef = float(pe) if not pd.isna(pe) else np.nan
    except:
        return "Unknown"

    if np.isnan(apf) or np.isnan(pef):
        return "Unknown"

    alt = (apf + pef) / 2
    if alt < 2000:
        return "LEO"
    if alt < 35000:
        return "MEO"
    if abs(alt - 35786) < 2000:
        return "GEO"
    if alt >= 35000:
        return "HEO"
    return "Unknown"


# ============================
# MAIN LOOP
# ============================
rows = []

for _, r in df2.iterrows():

    try:
        norad = int(r[col_norad])
    except:
        continue

    try:
        mass = float(r[col_mass])
    except:
        continue

    name = r[col_name] if col_name and pd.notna(r[col_name]) else ""
    operator = r[col_operator] if col_operator and pd.notna(r[col_operator]) else ""
    country  = r[col_country] if col_country and pd.notna(r[col_country]) else ""
    purpose  = r[col_purpose] if col_purpose and pd.notna(r[col_purpose]) else ""

    perigee = r[col_perigee] if col_perigee and pd.notna(r[col_perigee]) else np.nan
    apogee  = r[col_apogee] if col_apogee and pd.notna(r[col_apogee]) else np.nan
    incl    = r[col_incl] if col_incl and pd.notna(r[col_incl]) else np.nan

    orbit = compute_orbit_type(apogee, perigee)
    launch_dt = r["launch_datetime"]
    launch_year = int(launch_dt.year)

    fam = r[col_bus] if col_bus and pd.notna(r[col_bus]) else "unknown"

    # ========== DRY MASS ==========
    dry_mass = compute_dry_mass(mass, orbit)

    # ========== RANDOM MATERIALS ==========
    chosen_materials = random.sample(MATERIAL_POOL, 3)

    f1 = round(random.uniform(0.40, 0.60), 3)
    f2 = round(random.uniform(0.20, 0.35), 3)
    f3 = round(1 - (f1 + f2), 3)
    if f3 < 0:
        f3 = abs(f3)

    # ========== BUILD ROW ==========
    rows.append({
        "object_id": norad,
        "satellite_name": name,
        "launch_year": launch_year,
        "launch_mass_kg": mass,
        "dry_mass_kg": dry_mass,
        "operator": operator,
        "country": country,
        "purpose": purpose,
        "orbit_type": orbit,
        "perigee_km": None if pd.isna(perigee) else perigee,
        "apogee_km": None if pd.isna(apogee) else apogee,
        "inclination_deg": None if pd.isna(incl) else incl,
        "bus_family": fam,
        "mass_source": "UCS Database",
        "mass_confidence": 0.9,

        "dominant_material_1": chosen_materials[0],
        "dominant_material_fraction_1": f1,

        "dominant_material_2": chosen_materials[1],
        "dominant_material_fraction_2": f2,

        "dominant_material_3": chosen_materials[2],
        "dominant_material_fraction_3": f3,
    })

# ============================
# SORT AND EXPORT
# ============================
clean_df = pd.DataFrame(rows)
clean_df = clean_df.sort_values("launch_year").head(500)

clean_df.to_csv(OUT_CSV, index=False)
clean_df.to_excel(OUT_XLSX, index=False)

print("SUCCESS!")
print("Wrote:", OUT_CSV)
print("Wrote:", OUT_XLSX)

# ERASE 20% OF DRY MASS + MATERIALS
n = int(len(clean_df) * 0.20)
erase_idx = np.random.choice(clean_df.index, size=n, replace=False)

cols_to_erase = [
    "dry_mass_kg",
    "dominant_material_1", "dominant_material_fraction_1",
    "dominant_material_2", "dominant_material_fraction_2",
    "dominant_material_3", "dominant_material_fraction_3"
]

clean_df.loc[erase_idx, cols_to_erase] = np.nan

print("20% rows erased =", len(erase_idx))
print(clean_df.loc[erase_idx][cols_to_erase].head())

# SAVE FINAL OUTPUT
clean_df.to_csv(OUT_CSV, index=False)
clean_df.to_excel(OUT_XLSX, index=False)

print("UPDATED FILES SAVED AFTER ERASE")
