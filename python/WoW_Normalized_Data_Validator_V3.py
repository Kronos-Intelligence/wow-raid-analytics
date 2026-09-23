import os
import pandas as pd


# ============================================================
# KRONOS INTELLIGENCE
# WORLD OF WARCRAFT RAID ANALYTICS
#
# V3 - NORMALIZED DATA VALIDATOR
#
# Purpose:
#   Validate the normalized CSV data before Power BI modeling.
#
# Checks:
#   1. Required files exist
#   2. Row counts
#   3. Duplicate keys
#   4. Referential integrity
#   5. Damage reconciliation
#   6. Fight coverage
#   7. Player participation
#   8. Date coverage
#   9. Potential data-quality warnings
#
# Output:
#   validation_results.txt
#   player_participation.csv
# ============================================================


# ============================================================
# 1. FOLDER LOCATION
# ============================================================

BASE_FOLDER = os.getenv("WOW_RAID_ANALYTICS_BASE", os.getcwd())
NORMALIZED_FOLDER = os.path.join(BASE_FOLDER, "normalized_v3")


# ============================================================
# 2. REQUIRED TABLES
# ============================================================

REQUIRED_TABLES = [

    "dim_report",

    "dim_fight",

    "dim_player",

    "dim_ability",

    "dim_target",

    "fact_player_performance",

    "fact_damage_abilities",

    "fact_damage_targets",

    "fact_damage_taken",

    "fact_healing",

    "fact_deaths",

    "fact_interrupts",

    "fact_dispels",

    "fact_casts"

]


# ============================================================
# 3. LOAD TABLES
# ============================================================

print("=" * 70)
print("KRONOS INTELLIGENCE")
print("WORLD OF WARCRAFT RAID ANALYTICS")
print("V3 - NORMALIZED DATA VALIDATION")
print("=" * 70)
print()


tables = {}

missing_tables = []


print("STEP 1: CHECKING REQUIRED TABLES")
print("-" * 70)
print()


for table_name in REQUIRED_TABLES:

    path = os.path.join(
        NORMALIZED_FOLDER,
        f"{table_name}.csv"
    )


    if not os.path.exists(path):

        print(
            f"ERROR: Missing {table_name}.csv"
        )

        missing_tables.append(
            table_name
        )

        continue


    try:

        dataframe = pd.read_csv(
            path
        )

        tables[table_name] = dataframe

        print(
            f"{table_name:<30}"
            f"{len(dataframe):>10,} rows"
        )

    except Exception as error:

        print(
            f"ERROR loading {table_name}: "
            f"{error}"
        )

        missing_tables.append(
            table_name
        )


print()


if missing_tables:

    print("=" * 70)
    print("VALIDATION FAILED")
    print("=" * 70)
    print()

    print(
        "Missing or unreadable tables:"
    )

    for table in missing_tables:

        print(
            f"  - {table}"
        )

    raise SystemExit(1)


print("All required tables loaded.")
print()


# ============================================================
# 4. VALIDATION FLAGS
# ============================================================

errors = []
warnings = []


def add_error(message):

    errors.append(
        message
    )


def add_warning(message):

    warnings.append(
        message
    )


# ============================================================
# 5. BASIC TABLE VALIDATION
# ============================================================

print("=" * 70)
print("STEP 2: BASIC TABLE VALIDATION")
print("=" * 70)
print()


for table_name, dataframe in tables.items():

    if dataframe.empty:

        add_warning(
            f"{table_name} contains zero rows."
        )

        print(
            f"WARNING: {table_name} is empty."
        )

    else:

        print(
            f"PASS: {table_name} "
            f"contains {len(dataframe):,} rows."
        )


print()


# ============================================================
# 6. REPORT VALIDATION
# ============================================================

print("=" * 70)
print("STEP 3: REPORT VALIDATION")
print("=" * 70)
print()


reports = tables[
    "dim_report"
]


report_codes = set(
    reports[
        "report_code"
    ].dropna().astype(str)
)


print(
    f"Unique reports: "
    f"{len(report_codes):,}"
)


if reports[
    "report_code"
].duplicated().any():

    add_error(
        "dim_report contains duplicate report_code values."
    )

    print(
        "FAIL: Duplicate report codes found."
    )

else:

    print(
        "PASS: Report codes are unique."
    )


print()


# ============================================================
# 7. FIGHT VALIDATION
# ============================================================

print("=" * 70)
print("STEP 4: FIGHT VALIDATION")
print("=" * 70)
print()


fights = tables[
    "dim_fight"
].copy()


print(
    f"Total fights: "
    f"{len(fights):,}"
)


# ------------------------------------------------------------
# Fight key
# ------------------------------------------------------------

fights[
    "fight_key"
] = (

    fights[
        "report_code"
    ].astype(str)

    + "|"

    + fights[
        "fight_id"
    ].astype(str)

)


duplicate_fights = fights[
    "fight_key"
].duplicated()


if duplicate_fights.any():

    count = duplicate_fights.sum()

    add_error(
        f"dim_fight contains {count} duplicate fight keys."
    )

    print(
        f"FAIL: {count} duplicate fight keys."
    )

else:

    print(
        "PASS: Fight keys are unique."
    )


# ------------------------------------------------------------
# Fight -> Report
# ------------------------------------------------------------

fight_reports = set(
    fights[
        "report_code"
    ].dropna().astype(str)
)


orphan_fight_reports = (
    fight_reports
    - report_codes
)


if orphan_fight_reports:

    add_error(
        "dim_fight contains report codes "
        "not found in dim_report."
    )

    print(
        "FAIL: Orphan report references found."
    )

else:

    print(
        "PASS: Every fight maps to a report."
    )


print()


# ============================================================
# 8. PLAYER VALIDATION
# ============================================================

print("=" * 70)
print("STEP 5: PLAYER VALIDATION")
print("=" * 70)
print()


players = tables[
    "dim_player"
].copy()


player_ids = set(
    players[
        "player_id"
    ].dropna()
)


print(
    f"Unique players: "
    f"{len(player_ids):,}"
)


if players[
    "player_id"
].duplicated().any():

    count = players[
        "player_id"
    ].duplicated().sum()

    add_error(
        f"dim_player contains {count} "
        f"duplicate player IDs."
    )

    print(
        f"FAIL: {count} duplicate player IDs."
    )

else:

    print(
        "PASS: Player IDs are unique."
    )


# ============================================================
# 9. PLAYER PERFORMANCE REFERENTIAL INTEGRITY
# ============================================================

print("=" * 70)
print("STEP 6: PLAYER PERFORMANCE RELATIONSHIPS")
print("=" * 70)
print()


performance = tables[
    "fact_player_performance"
].copy()


performance_player_ids = set(
    performance[
        "player_id"
    ].dropna()
)


orphan_players = (
    performance_player_ids
    - player_ids
)


if orphan_players:

    add_error(
        f"{len(orphan_players)} player IDs in "
        f"fact_player_performance do not exist "
        f"in dim_player."
    )

    print(
        f"FAIL: {len(orphan_players)} "
        f"orphan player IDs."
    )

else:

    print(
        "PASS: Player relationships valid."
    )


# ------------------------------------------------------------
# Performance fight relationships
# ------------------------------------------------------------

performance_fights = set(

    zip(

        performance[
            "report_code"
        ].astype(str),

        performance[
            "fight_id"
        ].astype(str)

    )

)


valid_fights = set(

    zip(

        fights[
            "report_code"
        ].astype(str),

        fights[
            "fight_id"
        ].astype(str)

    )

)


orphan_performance_fights = (
    performance_fights
    - valid_fights
)


if orphan_performance_fights:

    add_error(
        f"{len(orphan_performance_fights)} "
        f"fight references in performance "
        f"data do not exist in dim_fight."
    )

    print(
        f"FAIL: "
        f"{len(orphan_performance_fights)} "
        f"orphan fight references."
    )

else:

    print(
        "PASS: Performance records map "
        "to valid fights."
    )


print()


# ============================================================
# 10. DAMAGE RECONCILIATION
# ============================================================

print("=" * 70)
print("STEP 7: DAMAGE RECONCILIATION")
print("=" * 70)
print()


damage_targets = tables[
    "fact_damage_targets"
].copy()


player_damage = performance[
    "total_damage"
].fillna(0).sum()


target_damage = damage_targets[
    "total"
].fillna(0).sum()


difference = (
    player_damage
    - target_damage
)


print(
    f"Player performance damage: "
    f"{player_damage:,.0f}"
)


print(
    f"Target damage: "
    f"{target_damage:,.0f}"
)


print(
    f"Difference: "
    f"{difference:,.0f}"
)


# ------------------------------------------------------------
# Reconciliation tolerance
# ------------------------------------------------------------

if abs(difference) <= 1:

    print(
        "PASS: Damage reconciles."
    )

else:

    add_warning(
        "Overall damage does not exactly reconcile "
        "between player performance and target data."
    )

    print(
        "WARNING: Damage does not exactly reconcile."
    )


print()


# ============================================================
# 11. FIGHT COVERAGE
# ============================================================

print("=" * 70)
print("STEP 8: FIGHT COVERAGE")
print("=" * 70)
print()


total_fights = len(
    fights
)


performance_fights_count = len(
    performance_fights
)


print(
    f"Fights in dim_fight: "
    f"{total_fights:,}"
)


print(
    f"Fights represented in performance: "
    f"{performance_fights_count:,}"
)


if total_fights == performance_fights_count:

    print(
        "PASS: Every fight has performance data."
    )

else:

    missing_count = (
        total_fights
        - performance_fights_count
    )

    add_warning(
        f"{missing_count} fights do not have "
        f"player performance records."
    )

    print(
        f"WARNING: {missing_count} "
        f"fights lack performance data."
    )


print()


# ============================================================
# 12. PLAYER PARTICIPATION ANALYSIS
# ============================================================

print("=" * 70)
print("STEP 9: PLAYER PARTICIPATION")
print("=" * 70)
print()


participation = (

    performance

    .groupby(
        [
            "player_id",
            "player_name"
        ],
        dropna=False
    )

    .agg(

        reports=(
            "report_code",
            "nunique"
        ),

        fights=(
            "fight_id",
            "count"
        ),

        total_damage=(
            "total_damage",
            "sum"
        ),

        average_damage=(
            "total_damage",
            "mean"
        ),

        average_active_time_pct=(
            "active_time_pct",
            "mean"
        ),

        average_item_level=(
            "item_level",
            "mean"
        )

    )

    .reset_index()

)


# ------------------------------------------------------------
# First and last report dates
# ------------------------------------------------------------

if "report_date" in fights.columns:

    fight_dates = fights[
        [
            "report_code",
            "report_date"
        ]
    ].drop_duplicates()


    participation = participation.merge(

        performance[
            [
                "player_id",
                "report_code"
            ]
        ].drop_duplicates()

        .merge(
            fight_dates,
            on="report_code",
            how="left"
        )

        .groupby(
            "player_id"
        )["report_date"]

        .agg(
            first_seen="min",
            last_seen="max"
        )

        .reset_index(),

        on="player_id",

        how="left"

    )


# ------------------------------------------------------------
# Participation percentage
# ------------------------------------------------------------

participation[
    "fight_participation_pct"
] = (

    participation[
        "fights"
    ]

    / total_fights

    * 100

)


participation = participation.sort_values(

    "fights",

    ascending=False

)


participation_path = os.path.join(

    NORMALIZED_FOLDER,

    "player_participation.csv"

)


participation.to_csv(

    participation_path,

    index=False,

    encoding="utf-8"

)


print(
    f"Player participation records: "
    f"{len(participation):,}"
)


print(
    f"Saved:"
)


print(
    participation_path
)


print()


print(
    "Top players by fight count:"
)


print()


print(

    participation[
        [
            "player_name",
            "reports",
            "fights",
            "fight_participation_pct"
        ]
    ]

    .head(20)

    .to_string(
        index=False
    )

)


print()


# ============================================================
# 13. DEATH VALIDATION
# ============================================================

print("=" * 70)
print("STEP 10: DEATH DATA")
print("=" * 70)
print()


deaths = tables[
    "fact_deaths"
]


print(
    f"Total death records: "
    f"{len(deaths):,}"
)


death_player_ids = set(
    deaths[
        "player_id"
    ].dropna()
)


orphan_death_players = (
    death_player_ids
    - player_ids
)


if orphan_death_players:

    add_warning(
        f"{len(orphan_death_players)} "
        f"death records reference players "
        f"not found in dim_player."
    )

    print(
        f"WARNING: {len(orphan_death_players)} "
        f"orphan death player IDs."
    )

else:

    print(
        "PASS: Death player relationships valid."
    )


print()


# ============================================================
# 14. SPECIAL ACTIVITY TABLE CHECKS
# ============================================================

print("=" * 70)
print("STEP 11: SPECIAL ACTIVITY TABLES")
print("=" * 70)
print()


special_tables = [

    "fact_interrupts",

    "fact_dispels",

    "fact_casts"

]


for table_name in special_tables:

    count = len(
        tables[
            table_name
        ]
    )


    print(
        f"{table_name:<30}"
        f"{count:>10,} records"
    )


    if count == total_fights:

        add_warning(
            f"{table_name} contains exactly one "
            f"record per fight. Verify that the "
            f"Warcraft Logs endpoint returned the "
            f"complete event set."
        )

        print(
            "  WARNING: Exactly one record per fight."
        )


print()


# ============================================================
# 15. DATE COVERAGE
# ============================================================

print("=" * 70)
print("STEP 12: DATE COVERAGE")
print("=" * 70)
print()


if "report_date" in fights.columns:

    dates = pd.to_datetime(

        fights[
            "report_date"
        ],

        errors="coerce"

    ).dropna()


    if not dates.empty:

        print(
            f"First fight date: "
            f"{dates.min()}"
        )


        print(
            f"Last fight date: "
            f"{dates.max()}"
        )


        print(
            f"Calendar span: "
            f"{(dates.max() - dates.min()).days} days"
        )


    else:

        add_warning(
            "No valid report dates were found."
        )

        print(
            "WARNING: No valid report dates."
        )

else:

    add_warning(
        "dim_fight does not contain report_date."
    )

    print(
        "WARNING: report_date unavailable."
    )


print()


# ============================================================
# 16. NULL CHECK
# ============================================================

print("=" * 70)
print("STEP 13: CRITICAL NULL CHECK")
print("=" * 70)
print()


critical_columns = {

    "dim_report": [
        "report_code"
    ],

    "dim_fight": [
        "report_code",
        "fight_id",
        "fight_name"
    ],

    "dim_player": [
        "player_id",
        "player_name"
    ],

    "fact_player_performance": [
        "report_code",
        "fight_id",
        "player_id"
    ]

}


for table_name, columns in critical_columns.items():

    dataframe = tables[
        table_name
    ]


    for column in columns:

        if column not in dataframe.columns:

            add_error(
                f"{table_name} is missing "
                f"required column {column}."
            )

            print(
                f"FAIL: {table_name}.{column} missing."
            )

            continue


        null_count = dataframe[
            column
        ].isna().sum()


        if null_count > 0:

            add_warning(
                f"{table_name}.{column} contains "
                f"{null_count:,} NULL values."
            )

            print(
                f"WARNING: {table_name}.{column} "
                f"has {null_count:,} NULLs."
            )

        else:

            print(
                f"PASS: {table_name}.{column}"
            )


print()


# ============================================================
# 17. FINAL SUMMARY
# ============================================================

print("=" * 70)
print("VALIDATION SUMMARY")
print("=" * 70)
print()


print(
    f"Reports:                 {len(reports):,}"
)

print(
    f"Fights:                  {len(fights):,}"
)

print(
    f"Players:                 {len(players):,}"
)

print(
    f"Performance records:     {len(performance):,}"
)

print(
    f"Deaths:                  {len(deaths):,}"
)


print()


print(
    f"Errors:                  {len(errors):,}"
)

print(
    f"Warnings:                {len(warnings):,}"
)


print()


# ============================================================
# 18. PRINT ERRORS
# ============================================================

if errors:

    print(
        "ERRORS:"
    )

    print()

    for error in errors:

        print(
            f"  ERROR: {error}"
        )

    print()


# ============================================================
# 19. PRINT WARNINGS
# ============================================================

if warnings:

    print(
        "WARNINGS:"
    )

    print()

    for warning in warnings:

        print(
            f"  WARNING: {warning}"
        )

    print()


# ============================================================
# 20. FINAL STATUS
# ============================================================

if errors:

    status = "FAIL"

else:

    status = "PASS"


print("=" * 70)
print(
    f"FINAL VALIDATION STATUS: {status}"
)
print("=" * 70)
print()


# ============================================================
# 21. SAVE VALIDATION REPORT
# ============================================================

validation_path = os.path.join(

    NORMALIZED_FOLDER,

    "validation_results.txt"

)


with open(

    validation_path,

    "w",

    encoding="utf-8"

) as file:

    file.write(
        "WORLD OF WARCRAFT RAID ANALYTICS\n"
    )

    file.write(
        "V3 NORMALIZED DATA VALIDATION\n"
    )

    file.write(
        "=" * 70 + "\n\n"
    )

    file.write(
        f"Reports: {len(reports):,}\n"
    )

    file.write(
        f"Fights: {len(fights):,}\n"
    )

    file.write(
        f"Players: {len(players):,}\n"
    )

    file.write(
        f"Performance records: "
        f"{len(performance):,}\n"
    )

    file.write(
        f"Deaths: {len(deaths):,}\n\n"
    )

    file.write(
        f"Errors: {len(errors):,}\n"
    )

    file.write(
        f"Warnings: {len(warnings):,}\n\n"
    )


    if errors:

        file.write(
            "ERRORS\n"
        )

        file.write(
            "-" * 70 + "\n"
        )

        for error in errors:

            file.write(
                f"- {error}\n"
            )

        file.write("\n")


    if warnings:

        file.write(
            "WARNINGS\n"
        )

        file.write(
            "-" * 70 + "\n"
        )

        for warning in warnings:

            file.write(
                f"- {warning}\n"
            )

        file.write("\n")


    file.write(
        f"FINAL STATUS: {status}\n"
    )


print(
    "Validation report saved:"
)

print(
    validation_path
)

print()


if status == "PASS":

    print(
        "NORMALIZED DATA VALIDATION PASSED."
    )

    print()

    print(
        "The dataset is ready for analytics-model development."
    )

else:

    print(
        "NORMALIZED DATA VALIDATION FAILED."
    )

    print()

    print(
        "Do not proceed to Power BI yet."
    )


print()
print(
    "Process finished."
)