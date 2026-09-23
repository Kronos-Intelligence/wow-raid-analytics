import os
import pandas as pd

# ============================================================
# WOW RAID ANALYTICS - V8 VALIDATOR
# ============================================================

BASE_DIR = os.path.join(os.getenv("WOW_RAID_ANALYTICS_BASE", os.getcwd()), "raid_analytics_v8")

FILES = {
    "raid_fights": "raid_fights.csv",
    "raid_reports": "raid_reports.csv",
    "raid_boss_summary": "raid_boss_summary.csv",
    "raid_progression": "raid_progression.csv",
    "raid_attempts": "raid_attempts.csv",
    "raid_analytics_inventory": "raid_analytics_inventory.csv",
}


def load_file(key):
    path = os.path.join(BASE_DIR, FILES[key])

    print(f"\nLoading {FILES[key]}...")
    print(path)

    if not os.path.exists(path):
        print("ERROR: File not found.")
        return None

    df = pd.read_csv(path)

    print(f"Rows: {len(df):,}")
    print(f"Columns: {len(df.columns)}")

    return df


# ============================================================
# LOAD DATASETS
# ============================================================

print("=" * 70)
print("WOW RAID ANALYTICS V8 VALIDATION")
print("=" * 70)

data = {}

for key in FILES:
    data[key] = load_file(key)


# ============================================================
# BASIC FILE VALIDATION
# ============================================================

print("\n" + "=" * 70)
print("STEP 1: FILE VALIDATION")
print("=" * 70)

missing_files = []

for key, filename in FILES.items():

    if data[key] is None:
        missing_files.append(filename)

if missing_files:
    print("\nERROR: Missing files:")

    for filename in missing_files:
        print(f" - {filename}")

    raise SystemExit(1)

print("\nAll V8 datasets loaded successfully.")


# ============================================================
# ROW COUNTS
# ============================================================

print("\n" + "=" * 70)
print("STEP 2: DATASET COUNTS")
print("=" * 70)

for key, df in data.items():
    print(f"{FILES[key]:35} {len(df):,} rows")


# ============================================================
# STEP 3: RAID FIGHT VALIDATION
# ============================================================

print()
print("=" * 70)
print("STEP 3: RAID FIGHT VALIDATION")
print("=" * 70)

fights = data["raid_fights"]

print(f"Raid fights: {len(fights):,}")

# Warcraft Logs fight IDs are only unique within a report.
# Therefore the true fight key is:
#
#     report_code + fight_id
#
# A fight_id appearing in multiple reports is normal.

required_fight_columns = {
    "report_code",
    "fight_id"
}

missing_fight_columns = required_fight_columns - set(fights.columns)

if missing_fight_columns:

    print(
        "ERROR: raid_fights is missing required columns:"
    )

    for column in sorted(missing_fight_columns):
        print(f" - {column}")

    raise SystemExit(1)


fight_keys = (
    fights["report_code"].astype(str)
    + "_"
    + fights["fight_id"].astype(str)
)

unique_fight_keys = fight_keys.nunique()

print(
    f"Unique report/fight keys: "
    f"{unique_fight_keys:,}"
)

if unique_fight_keys != len(fights):

    duplicate_count = (
        len(fights) - unique_fight_keys
    )

    print(
        f"WARNING: {duplicate_count:,} "
        "duplicate report/fight key(s) detected."
    )

else:

    print(
        "PASS: All report/fight keys are unique."
    )


# ============================================================
# REPORT VALIDATION
# ============================================================

print("\n" + "=" * 70)
print("STEP 4: REPORT VALIDATION")
print("=" * 70)

reports = data["raid_reports"]

print(f"Reports: {len(reports):,}")

if "report_code" in reports.columns:

    print(
        f"Unique reports: "
        f"{reports['report_code'].nunique():,}"
    )


# ============================================================
# BOSS SUMMARY VALIDATION
# ============================================================

print("\n" + "=" * 70)
print("STEP 5: BOSS SUMMARY VALIDATION")
print("=" * 70)

boss = data["raid_boss_summary"]

print(
    f"Boss summary rows: "
    f"{len(boss):,}"
)

if "boss_name" in boss.columns:

    print(
        f"Unique bosses: "
        f"{boss['boss_name'].nunique():,}"
    )

    print("\nBosses:")

    for name in boss["boss_name"].dropna().unique():
        print(f" - {name}")


# ============================================================
# PROGRESSION VALIDATION
# ============================================================

print("\n" + "=" * 70)
print("STEP 6: PROGRESSION VALIDATION")
print("=" * 70)

progression = data["raid_progression"]

print(
    f"Progression rows: "
    f"{len(progression):,}"
)

if "report_code" in progression.columns:

    print(
        f"Reports represented: "
        f"{progression['report_code'].nunique():,}"
    )


# ============================================================
# ATTEMPT VALIDATION
# ============================================================

print("\n" + "=" * 70)
print("STEP 7: ATTEMPT VALIDATION")
print("=" * 70)

attempts = data["raid_attempts"]

print(
    f"Attempt rows: "
    f"{len(attempts):,}"
)

if "result" in attempts.columns:

    print("\nAttempt results:")

    for result, count in attempts[
        "result"
    ].value_counts(dropna=False).items():

        print(
            f" - {result}: "
            f"{count:,}"
        )


# ============================================================
# CROSS-DATASET RECONCILIATION
# ============================================================

print("\n" + "=" * 70)
print("STEP 8: CROSS-DATASET RECONCILIATION")
print("=" * 70)

fight_count = len(fights)
progression_count = len(progression)

print(
    f"Fight records:       "
    f"{fight_count:,}"
)

print(
    f"Progression records: "
    f"{progression_count:,}"
)

if progression_count == fight_count:

    print(
        "PASS: Fight and progression "
        "counts match."
    )

else:

    print(
        "WARNING: Fight and progression "
        "counts differ."
    )


# ============================================================
# REPORT COVERAGE
# ============================================================

print("\n" + "=" * 70)
print("STEP 9: REPORT COVERAGE")
print("=" * 70)

fight_reports = set()

if "report_code" in fights.columns:

    fight_reports = set(
        fights["report_code"]
        .dropna()
        .astype(str)
    )

report_records = set()

if "report_code" in reports.columns:

    report_records = set(
        reports["report_code"]
        .dropna()
        .astype(str)
    )

missing_report_records = (
    fight_reports - report_records
)

print(
    f"Reports referenced by fights: "
    f"{len(fight_reports):,}"
)

print(
    f"Reports in report table:      "
    f"{len(report_records):,}"
)

if missing_report_records:

    print(
        f"WARNING: "
        f"{len(missing_report_records):,} "
        "fight reports are missing "
        "from raid_reports."
    )

else:

    print(
        "PASS: All fight reports "
        "exist in raid_reports."
    )


# ============================================================
# NULL CHECK
# ============================================================

print("\n" + "=" * 70)
print("STEP 10: NULL CHECK")
print("=" * 70)

for key, df in data.items():

    total_nulls = int(
        df.isna().sum().sum()
    )

    print(
        f"{FILES[key]:35} "
        f"{total_nulls:,} null values"
    )


# ============================================================
# INVENTORY VALIDATION
# ============================================================

print("\n" + "=" * 70)
print("STEP 11: ANALYTICS INVENTORY")
print("=" * 70)

inventory = data[
    "raid_analytics_inventory"
]

print(
    f"Inventory rows: "
    f"{len(inventory):,}"
)

print("\nInventory columns:")

for column in inventory.columns:
    print(f" - {column}")


# ============================================================
# FINAL SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("V8 VALIDATION SUMMARY")
print("=" * 70)

print(
    f"\nReports:              "
    f"{len(reports):,}"
)

print(
    f"Raid fights:          "
    f"{len(fights):,}"
)

print(
    f"Boss summary rows:    "
    f"{len(boss):,}"
)

print(
    f"Progression rows:     "
    f"{len(progression):,}"
)

print(
    f"Attempt rows:         "
    f"{len(attempts):,}"
)

print(
    f"Inventory rows:       "
    f"{len(inventory):,}"
)

print("\n" + "=" * 70)
print("V8 VALIDATION COMPLETE")
print("=" * 70)

print(
    "\nNo V8 datasets were modified."
)

print(
    "Review the validation output "
    "before building the Power BI model."
)