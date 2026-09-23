import os
import pandas as pd


# ============================================================
# KRONOS INTELLIGENCE
# WORLD OF WARCRAFT RAID ANALYTICS
#
# V8 - RAID ANALYTICS DATASET BUILDER
#
# Purpose:
#   Build a clean RAID-ONLY analytical layer from V7.
#
#   V7 remains untouched.
#
#   V8 creates:
#
#       1. raid_fights.csv
#       2. raid_reports.csv
#       3. raid_boss_summary.csv
#       4. raid_progression.csv
#       5. raid_attempts.csv
#       6. raid_analytics_inventory.csv
#
#   This is the foundation for the Power BI model.
# ============================================================


# ============================================================
# 1. CONFIGURATION
# ============================================================

BASE_FOLDER = os.getenv("WOW_RAID_ANALYTICS_BASE", os.getcwd())

V7_FOLDER = os.path.join(
    BASE_FOLDER,
    "normalized_v3"
)

INPUT_FILE = os.path.join(
    V7_FOLDER,
    "v7_content_classification.csv"
)

OUTPUT_FOLDER = os.path.join(
    BASE_FOLDER,
    "raid_analytics_v8"
)

os.makedirs(
    OUTPUT_FOLDER,
    exist_ok=True
)


# ============================================================
# 2. OUTPUT FILES
# ============================================================

RAID_FIGHTS_FILE = os.path.join(
    OUTPUT_FOLDER,
    "raid_fights.csv"
)

RAID_REPORTS_FILE = os.path.join(
    OUTPUT_FOLDER,
    "raid_reports.csv"
)

BOSS_SUMMARY_FILE = os.path.join(
    OUTPUT_FOLDER,
    "raid_boss_summary.csv"
)

PROGRESSION_FILE = os.path.join(
    OUTPUT_FOLDER,
    "raid_progression.csv"
)

ATTEMPTS_FILE = os.path.join(
    OUTPUT_FOLDER,
    "raid_attempts.csv"
)

INVENTORY_FILE = os.path.join(
    OUTPUT_FOLDER,
    "raid_analytics_inventory.csv"
)


# ============================================================
# 3. START
# ============================================================

print("=" * 70)
print("KRONOS INTELLIGENCE")
print("WORLD OF WARCRAFT RAID ANALYTICS")
print("V8 - RAID ANALYTICS DATASET BUILDER")
print("=" * 70)
print()


# ============================================================
# 4. CHECK INPUT
# ============================================================

if not os.path.exists(INPUT_FILE):

    print("ERROR: V7 classification file was not found.")
    print()
    print(INPUT_FILE)
    raise SystemExit(1)


# ============================================================
# 5. LOAD V7
# ============================================================

df = pd.read_csv(
    INPUT_FILE
)

print(
    f"V7 fights loaded: {len(df):,}"
)

print()


# ============================================================
# 6. REQUIRED COLUMNS
# ============================================================

required_columns = [

    "report_code",
    "fight_id",
    "fight_name",
    "encounter_id",
    "kill",
    "duration_seconds",
    "difficulty",
    "raid_size",
    "player_count",
    "report_date",
    "content_type"

]

missing_columns = [

    column

    for column in required_columns

    if column not in df.columns

]

if missing_columns:

    print("ERROR: Missing required columns:")

    for column in missing_columns:
        print(f" - {column}")

    raise SystemExit(1)


# ============================================================
# 7. FILTER RAID CONTENT
# ============================================================

raid_df = df[
    df["content_type"]
    .astype(str)
    .str.upper()
    == "RAID"
].copy()


print(
    f"Raid fights selected: {len(raid_df):,}"
)

print()


# ============================================================
# 8. BASIC DATA CLEANING
# ============================================================

raid_df["report_date"] = pd.to_datetime(
    raid_df["report_date"],
    errors="coerce"
)

raid_df["duration_seconds"] = pd.to_numeric(
    raid_df["duration_seconds"],
    errors="coerce"
)

raid_df["raid_size"] = pd.to_numeric(
    raid_df["raid_size"],
    errors="coerce"
)

raid_df["player_count"] = pd.to_numeric(
    raid_df["player_count"],
    errors="coerce"
)

raid_df["difficulty"] = pd.to_numeric(
    raid_df["difficulty"],
    errors="coerce"
)

raid_df["kill"] = (
    raid_df["kill"]
    .astype(str)
    .str.lower()
    .isin([
        "true",
        "1",
        "yes"
    ])
)


# ============================================================
# 9. DERIVED FIGHT METRICS
# ============================================================

raid_df["duration_minutes"] = (
    raid_df["duration_seconds"]
    / 60
)


raid_df["duration_minutes"] = (
    raid_df["duration_minutes"]
    .round(2)
)


raid_df["fight_result"] = (
    raid_df["kill"]
    .map({
        True: "KILL",
        False: "WIPE"
    })
)


raid_df["raid_size_difference"] = (

    raid_df["raid_size"]
    -
    raid_df["player_count"]

)


raid_df["report_fight_key"] = (

    raid_df["report_code"]
    .astype(str)
    +
    "_"
    +
    raid_df["fight_id"]
    .astype(str)

)


# ============================================================
# 10. SORT
# ============================================================

raid_df = raid_df.sort_values(

    [
        "report_date",
        "report_code",
        "fight_id"
    ]

).reset_index(
    drop=True
)


# ============================================================
# 11. RAID REPORT TABLE
# ============================================================

print("=" * 70)
print("BUILDING RAID REPORT TABLE")
print("=" * 70)
print()


report_groups = []

for report_code, group in raid_df.groupby(
    "report_code",
    sort=False
):

    report_groups.append({

        "report_code": report_code,

        "report_date": group[
            "report_date"
        ].min(),

        "raid_fights": len(group),

        "kills": int(
            group["kill"].sum()
        ),

        "wipes": int(
            (~group["kill"]).sum()
        ),

        "kill_rate_pct": round(

            group["kill"].mean()
            * 100,

            2

        ),

        "total_raid_time_minutes": round(

            group[
                "duration_minutes"
            ].sum(),

            2

        ),

        "avg_fight_minutes": round(

            group[
                "duration_minutes"
            ].mean(),

            2

        ),

        "max_raid_size": (

            group[
                "raid_size"
            ]
            .max()
        ),

        "avg_player_count": round(

            group[
                "player_count"
            ]
            .mean(),

            2

        )

    })


raid_reports = pd.DataFrame(
    report_groups
)


print(
    f"Reports created: "
    f"{len(raid_reports):,}"
)

print()


# ============================================================
# 12. BOSS SUMMARY
# ============================================================

print("=" * 70)
print("BUILDING BOSS SUMMARY")
print("=" * 70)
print()


boss_groups = []

for fight_name, group in raid_df.groupby(
    "fight_name",
    sort=True
):

    boss_groups.append({

        "fight_name": fight_name,

        "encounter_id": (
            group[
                "encounter_id"
            ]
            .dropna()
            .iloc[0]
            if not group[
                "encounter_id"
            ]
            .dropna()
            .empty
            else None
        ),

        "attempts": len(group),

        "kills": int(
            group["kill"].sum()
        ),

        "wipes": int(
            (~group["kill"]).sum()
        ),

        "kill_rate_pct": round(

            group["kill"].mean()
            * 100,

            2

        ),

        "avg_duration_minutes": round(

            group[
                "duration_minutes"
            ].mean(),

            2

        ),

        "fastest_kill_minutes": (

            round(

                group.loc[
                    group["kill"],
                    "duration_minutes"
                ].min(),

                2

            )

            if group["kill"].any()

            else None

        ),

        "slowest_attempt_minutes": round(

            group[
                "duration_minutes"
            ].max(),

            2

        )

    })


boss_summary = pd.DataFrame(
    boss_groups
)


boss_summary = boss_summary.sort_values(

    [
        "kill_rate_pct",
        "attempts"
    ],

    ascending=[
        False,
        False
    ]

).reset_index(
    drop=True
)


print(
    f"Bosses identified: "
    f"{len(boss_summary):,}"
)

print()


# ============================================================
# 13. PROGRESSION TABLE
# ============================================================

print("=" * 70)
print("BUILDING RAID PROGRESSION")
print("=" * 70)
print()


progression = raid_df[

    [
        "report_code",
        "report_date",
        "fight_id",
        "fight_name",
        "encounter_id",
        "kill",
        "fight_result",
        "duration_minutes",
        "raid_size",
        "player_count"

    ]

].copy()


progression = progression.sort_values(

    [
        "report_date",
        "report_code",
        "fight_id"
    ]

).reset_index(
    drop=True
)


progression[
    "attempt_number"
] = (

    progression

    .groupby(
        [
            "fight_name"
        ]
    )

    .cumcount()

    + 1

)


progression[
    "kill_number"
] = (

    progression[
        "kill"
    ]

    .groupby(
        progression[
            "fight_name"
        ]
    )

    .cumsum()

)


# ============================================================
# 14. ATTEMPTS TABLE
# ============================================================

print("=" * 70)
print("BUILDING RAID ATTEMPTS")
print("=" * 70)
print()


attempts = raid_df[

    [
        "report_code",
        "report_date",
        "fight_id",
        "fight_name",
        "encounter_id",
        "fight_result",
        "kill",
        "duration_seconds",
        "duration_minutes",
        "raid_size",
        "player_count",
        "raid_size_difference",
        "difficulty",
        "report_fight_key"

    ]

].copy()


attempts[
    "attempt_number"
] = (

    attempts

    .groupby(
        [
            "fight_name"
        ]
    )

    .cumcount()

    + 1

)


# ============================================================
# 15. DATA QUALITY CHECKS
# ============================================================

print("=" * 70)
print("V8 DATA QUALITY CHECKS")
print("=" * 70)
print()


print(
    f"Raid fights: "
    f"{len(raid_df):,}"
)

print(
    f"Raid reports: "
    f"{raid_df['report_code'].nunique():,}"
)

print(
    f"Unique bosses: "
    f"{raid_df['fight_name'].nunique():,}"
)

print(
    f"Kills: "
    f"{int(raid_df['kill'].sum()):,}"
)

print(
    f"Wipes: "
    f"{int((~raid_df['kill']).sum()):,}"
)

print()


missing_report_codes = raid_df[
    "report_code"
].isna().sum()

missing_fight_names = raid_df[
    "fight_name"
].isna().sum()

missing_dates = raid_df[
    "report_date"
].isna().sum()

missing_durations = raid_df[
    "duration_seconds"
].isna().sum()


print(
    f"Missing report codes: "
    f"{missing_report_codes:,}"
)

print(
    f"Missing fight names: "
    f"{missing_fight_names:,}"
)

print(
    f"Missing report dates: "
    f"{missing_dates:,}"
)

print(
    f"Missing durations: "
    f"{missing_durations:,}"
)

print()


# ============================================================
# 16. DUPLICATE CHECK
# ============================================================

duplicate_keys = raid_df[
    "report_fight_key"
].duplicated().sum()


print(
    f"Duplicate report/fight keys: "
    f"{duplicate_keys:,}"
)

print()


# ============================================================
# 17. INVENTORY TABLE
# ============================================================

inventory = pd.DataFrame({

    "dataset": [

        "raid_fights",
        "raid_reports",
        "raid_boss_summary",
        "raid_progression",
        "raid_attempts"

    ],

    "records": [

        len(raid_df),
        len(raid_reports),
        len(boss_summary),
        len(progression),
        len(attempts)

    ]

})


# ============================================================
# 18. SAVE OUTPUTS
# ============================================================

print("=" * 70)
print("SAVING V8 DATASETS")
print("=" * 70)
print()


raid_df.to_csv(
    RAID_FIGHTS_FILE,
    index=False,
    encoding="utf-8"
)

print(
    f"Saved raid_fights.csv: "
    f"{len(raid_df):,} records"
)


raid_reports.to_csv(
    RAID_REPORTS_FILE,
    index=False,
    encoding="utf-8"
)

print(
    f"Saved raid_reports.csv: "
    f"{len(raid_reports):,} records"
)


boss_summary.to_csv(
    BOSS_SUMMARY_FILE,
    index=False,
    encoding="utf-8"
)

print(
    f"Saved raid_boss_summary.csv: "
    f"{len(boss_summary):,} records"
)


progression.to_csv(
    PROGRESSION_FILE,
    index=False,
    encoding="utf-8"
)

print(
    f"Saved raid_progression.csv: "
    f"{len(progression):,} records"
)


attempts.to_csv(
    ATTEMPTS_FILE,
    index=False,
    encoding="utf-8"
)

print(
    f"Saved raid_attempts.csv: "
    f"{len(attempts):,} records"
)


inventory.to_csv(
    INVENTORY_FILE,
    index=False,
    encoding="utf-8"
)

print(
    f"Saved raid_analytics_inventory.csv: "
    f"{len(inventory):,} records"
)


# ============================================================
# 19. FINAL SUMMARY
# ============================================================

print()
print("=" * 70)
print("V8 RAID ANALYTICS BUILD COMPLETE")
print("=" * 70)
print()

print(
    "Output folder:"
)

print(
    OUTPUT_FOLDER
)

print()

print(
    "Datasets created:"
)

print(
    "- raid_fights.csv"
)

print(
    "- raid_reports.csv"
)

print(
    "- raid_boss_summary.csv"
)

print(
    "- raid_progression.csv"
)

print(
    "- raid_attempts.csv"
)

print(
    "- raid_analytics_inventory.csv"
)

print()

print(
    "V7 source data was NOT modified."
)

print()

print(
    "NEXT STEP:"
)

print(
    "Validate the V8 analytical layer before building"
)

print(
    "the Power BI model."
)

print()

print(
    "Process finished with exit code 0"
)