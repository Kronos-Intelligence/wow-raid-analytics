import os
import pandas as pd


# ============================================================
# KRONOS INTELLIGENCE
# WORLD OF WARCRAFT RAID ANALYTICS
#
# V7 - CONTENT CLASSIFICATION ENGINE
#
# Purpose:
#   Classify normalized fights into:
#
#       RAID
#       MYTHIC+
#       PVP
#       TRASH
#       UNKNOWN
#
#   Classification priority:
#
#       1. Difficulty ID
#       2. Encounter metadata
#       3. Existing V6 classification
#
#   IMPORTANT:
#       This script does NOT modify normalized data.
# ============================================================


# ============================================================
# 1. CONFIGURATION
# ============================================================

BASE_FOLDER = os.getenv("WOW_RAID_ANALYTICS_BASE", os.getcwd())
NORMALIZED_FOLDER = os.path.join(BASE_FOLDER, "normalized_v3")

INPUT_FILE = os.path.join(
    NORMALIZED_FOLDER,
    "v6_fight_content_classification.csv"
)

OUTPUT_FILE = os.path.join(
    NORMALIZED_FOLDER,
    "v7_content_classification.csv"
)

UNKNOWN_FILE = os.path.join(
    NORMALIZED_FOLDER,
    "v7_unknown_fights.csv"
)

SUMMARY_FILE = os.path.join(
    NORMALIZED_FOLDER,
    "v7_content_summary.csv"
)


# ============================================================
# 2. START
# ============================================================

print("=" * 70)
print("KRONOS INTELLIGENCE")
print("WORLD OF WARCRAFT RAID ANALYTICS")
print("V7 - CONTENT CLASSIFICATION ENGINE")
print("=" * 70)
print()


# ============================================================
# 3. CHECK INPUT
# ============================================================

if not os.path.exists(INPUT_FILE):

    print("ERROR: V6 classification file was not found.")
    print()
    print(INPUT_FILE)
    raise SystemExit(1)


# ============================================================
# 4. LOAD DATA
# ============================================================

df = pd.read_csv(
    INPUT_FILE
)

print(
    f"Loaded fights: {len(df):,}"
)

print()


# ============================================================
# 5. CHECK REQUIRED COLUMNS
# ============================================================

required_columns = [
    "fight_id",
    "fight_name",
]

missing_columns = [
    column
    for column in required_columns
    if column not in df.columns
]

if missing_columns:

    print("ERROR: Required columns are missing:")

    for column in missing_columns:
        print(f" - {column}")

    raise SystemExit(1)


# ============================================================
# 6. SAFE TEXT FUNCTION
# ============================================================

def clean_text(value):

    if pd.isna(value):
        return ""

    return str(value).strip()


# ============================================================
# 7. DIFFICULTY CLASSIFICATION
#
# Warcraft Logs difficulty IDs observed in this dataset:
#
#   3   = Raid
#   4   = Raid
#   5   = Raid
#   10  = Mythic+
#   108 = PvP/Arena
#
# We intentionally preserve anything outside these values
# as UNKNOWN until verified.
# ============================================================

def classify_by_difficulty(value):

    try:
        difficulty = int(value)
    except:

        return None

    if difficulty in [3, 4, 5]:

        return (
            "RAID",
            f"difficulty_{difficulty}"
        )

    if difficulty == 10:

        return (
            "MYTHIC+",
            "difficulty_10"
        )

    if difficulty == 108:

        return (
            "PVP",
            "difficulty_108"
        )

    return None


# ============================================================
# 8. RAID ENCOUNTER NAME VALIDATION
#
# These names were observed in the current dataset and are
# being used only as a secondary validation layer.
#
# Difficulty remains the primary classification method.
# ============================================================

KNOWN_RAID_ENCOUNTERS = {

    "imperator averzian",
    "vorasius",
    "fallen-king salhadaar",
    "vaelgor & ezzorak",
    "lightblinded vanguard",
    "chimaerus, the undreamt god",
    "crown of the cosmos",
    "belo'ren, child of al'ar",
    "midnight falls",
    "rotmire",
    "sszorak",
    "the twin fangs",
    "the coiled altar",
    "entombed sentinels",
    "vashnik the malignant",
    "the lost explorers",
    "nek'zali the soulcoiler",
    "ula'tek",
}


# ============================================================
# 9. MYTHIC+ ENCOUNTERS
# ============================================================

KNOWN_MYTHIC_DUNGEONS = {

    "murder row",
    "ruby life pools",
    "kings' rest",
    "king's rest",
    "altar of fangs",
    "den of nalorakk",
    "the blinding vale",
}


# ============================================================
# 10. CLASSIFY EACH FIGHT
# ============================================================

def classify_fight(row):

    fight_name = clean_text(
        row.get("fight_name", "")
    ).lower()

    difficulty = row.get(
        "difficulty"
    )

    # --------------------------------------------------------
    # PRIMARY: DIFFICULTY
    # --------------------------------------------------------

    difficulty_result = classify_by_difficulty(
        difficulty
    )

    if difficulty_result is not None:

        content_type, method = difficulty_result

        # Secondary name validation
        if (
            content_type == "RAID"
            and fight_name in KNOWN_RAID_ENCOUNTERS
        ):

            method = (
                f"{method}+known_raid_encounter"
            )

        if (
            content_type == "MYTHIC+"
            and fight_name in KNOWN_MYTHIC_DUNGEONS
        ):

            method = (
                f"{method}+known_mythic_encounter"
            )

        return content_type, method


    # --------------------------------------------------------
    # SECONDARY: KNOWN RAID ENCOUNTER
    # --------------------------------------------------------

    if fight_name in KNOWN_RAID_ENCOUNTERS:

        return (
            "RAID",
            "known_raid_encounter"
        )


    # --------------------------------------------------------
    # SECONDARY: KNOWN MYTHIC+ ENCOUNTER
    # --------------------------------------------------------

    if fight_name in KNOWN_MYTHIC_DUNGEONS:

        return (
            "MYTHIC+",
            "known_mythic_encounter"
        )


    # --------------------------------------------------------
    # UNKNOWN
    # --------------------------------------------------------

    return (
        "UNKNOWN",
        "no_verified_classification"
    )


# ============================================================
# 11. APPLY CLASSIFICATION
# ============================================================

results = df.apply(
    classify_fight,
    axis=1
)


df[
    "content_type"
] = results.apply(
    lambda x: x[0]
)


df[
    "classification_method"
] = results.apply(
    lambda x: x[1]
)


# ============================================================
# 12. CONTENT INVENTORY
# ============================================================

print("=" * 70)
print("V7 CONTENT INVENTORY")
print("=" * 70)
print()

counts = (
    df["content_type"]
    .value_counts()
)


for content_type in [
    "RAID",
    "MYTHIC+",
    "PVP",
    "TRASH",
    "UNKNOWN"
]:

    count = counts.get(
        content_type,
        0
    )

    print(
        f"{content_type:<12} {count:,}"
    )


print()


# ============================================================
# 13. CLASSIFICATION METHOD SUMMARY
# ============================================================

print("=" * 70)
print("CLASSIFICATION METHODS")
print("=" * 70)
print()

method_counts = (
    df[
        "classification_method"
    ]
    .value_counts()
)


for method, count in method_counts.items():

    print(
        f"{method:<40} {count:,}"
    )


print()


# ============================================================
# 14. RAID INVENTORY
# ============================================================

print("=" * 70)
print("RAID ENCOUNTER INVENTORY")
print("=" * 70)
print()

raid_df = df[
    df["content_type"] == "RAID"
].copy()


print(
    f"Raid fights: {len(raid_df):,}"
)

print()


if not raid_df.empty:

    raid_columns = [
        column
        for column in [
            "report_code",
            "fight_id",
            "fight_name",
            "difficulty",
            "content_type",
            "classification_method",
        ]
        if column in raid_df.columns
    ]

    print(
        raid_df[
            raid_columns
        ].to_string(
            index=False
        )
    )


print()


# ============================================================
# 15. MYTHIC+ INVENTORY
# ============================================================

print("=" * 70)
print("MYTHIC+ INVENTORY")
print("=" * 70)
print()

mythic_df = df[
    df["content_type"] == "MYTHIC+"
].copy()


print(
    f"Mythic+ fights: {len(mythic_df):,}"
)

print()


if not mythic_df.empty:

    mythic_columns = [
        column
        for column in [
            "report_code",
            "fight_id",
            "fight_name",
            "difficulty",
            "content_type",
            "classification_method",
        ]
        if column in mythic_df.columns
    ]

    print(
        mythic_df[
            mythic_columns
        ].to_string(
            index=False
        )
    )


print()


# ============================================================
# 16. PVP INVENTORY
# ============================================================

print("=" * 70)
print("PVP INVENTORY")
print("=" * 70)
print()

pvp_df = df[
    df["content_type"] == "PVP"
].copy()


print(
    f"PvP fights: {len(pvp_df):,}"
)

print()


if not pvp_df.empty:

    pvp_columns = [
        column
        for column in [
            "report_code",
            "fight_id",
            "fight_name",
            "difficulty",
            "content_type",
            "classification_method",
        ]
        if column in pvp_df.columns
    ]

    print(
        pvp_df[
            pvp_columns
        ].to_string(
            index=False
        )
    )


print()


# ============================================================
# 17. UNKNOWN INVENTORY
# ============================================================

print("=" * 70)
print("UNKNOWN FIGHTS")
print("=" * 70)
print()

unknown_df = df[
    df["content_type"] == "UNKNOWN"
].copy()


print(
    f"Unknown fights: {len(unknown_df):,}"
)

print()


if not unknown_df.empty:

    unknown_columns = [
        column
        for column in [
            "report_code",
            "fight_id",
            "fight_name",
            "difficulty",
            "content_type",
            "classification_method",
        ]
        if column in unknown_df.columns
    ]

    print(
        unknown_df[
            unknown_columns
        ].to_string(
            index=False
        )
    )


print()


# ============================================================
# 18. REPORT-LEVEL SUMMARY
# ============================================================

print("=" * 70)
print("REPORT-LEVEL CONTENT SUMMARY")
print("=" * 70)
print()


if "report_code" in df.columns:

    report_summary = (

        df

        .groupby(
            [
                "report_code",
                "content_type"
            ]
        )

        .size()

        .reset_index(
            name="fight_count"
        )

        .sort_values(
            [
                "report_code",
                "content_type"
            ]
        )

    )

    print(
        report_summary.to_string(
            index=False
        )
    )


print()


# ============================================================
# 19. SAVE FULL CLASSIFICATION
# ============================================================

df.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8"
)


# ============================================================
# 20. SAVE UNKNOWN FIGHTS
# ============================================================

unknown_df.to_csv(
    UNKNOWN_FILE,
    index=False,
    encoding="utf-8"
)


# ============================================================
# 21. SAVE SUMMARY
# ============================================================

summary_rows = []

for content_type in [
    "RAID",
    "MYTHIC+",
    "PVP",
    "TRASH",
    "UNKNOWN"
]:

    summary_rows.append({

        "content_type": content_type,

        "fight_count": counts.get(
            content_type,
            0
        )

    })


summary_df = pd.DataFrame(
    summary_rows
)


summary_df.to_csv(
    SUMMARY_FILE,
    index=False,
    encoding="utf-8"
)


# ============================================================
# 22. FINAL STATUS
# ============================================================

print("=" * 70)
print("V7 COMPLETE")
print("=" * 70)
print()

print(
    "Classification file:"
)

print(
    OUTPUT_FILE
)

print()

print(
    "Unknown-fight file:"
)

print(
    UNKNOWN_FILE
)

print()

print(
    "Summary file:"
)

print(
    SUMMARY_FILE
)

print()

print(
    "No normalized data was modified."
)

print()

print(
    "NEXT STEP:"
)

print(
    "Review the RAID, MYTHIC+, PVP, and UNKNOWN inventories."
)

print()

print(
    "Process finished with exit code 0"
)