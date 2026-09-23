import os
import re
import pandas as pd


# ============================================================
# KRONOS INTELLIGENCE
# WORLD OF WARCRAFT RAID ANALYTICS
#
# V6 - ENCOUNTER / CONTENT CLASSIFIER
#
# Purpose:
#   Classify every fight in the current normalized dataset as:
#
#       RAID
#       MYTHIC+
#       TRASH
#       UNKNOWN
#
#   This script DOES NOT modify the normalized data.
#
#   It creates an audit file that we will use to isolate
#   actual raid encounters before continuing the analytics work.
# ============================================================


# ============================================================
# 1. CONFIGURATION
# ============================================================

BASE_FOLDER = os.getenv("WOW_RAID_ANALYTICS_BASE", os.getcwd())
NORMALIZED_FOLDER = os.path.join(BASE_FOLDER, "normalized_v3")

OUTPUT_FILE = os.path.join(
    NORMALIZED_FOLDER,
    "v6_fight_content_classification.csv"
)


# ============================================================
# 2. LOAD FIGHT TABLE
# ============================================================

print("=" * 70)
print("KRONOS INTELLIGENCE")
print("WORLD OF WARCRAFT RAID ANALYTICS")
print("V6 - ENCOUNTER / CONTENT CLASSIFIER")
print("=" * 70)
print()

fights_path = os.path.join(
    NORMALIZED_FOLDER,
    "dim_fight.csv"
)

if not os.path.exists(fights_path):
    print("ERROR: dim_fight.csv was not found.")
    print(fights_path)
    raise SystemExit(1)

fights = pd.read_csv(
    fights_path
)

print(
    f"Loaded fights: {len(fights):,}"
)

print()


# ============================================================
# 3. DISPLAY AVAILABLE COLUMNS
# ============================================================

print("=" * 70)
print("AVAILABLE FIGHT COLUMNS")
print("=" * 70)
print()

for column in fights.columns:
    print(column)

print()


# ============================================================
# 4. HELPER FUNCTIONS
# ============================================================

def clean_text(value):

    if pd.isna(value):
        return ""

    return str(value).strip()


def normalize_text(value):

    return clean_text(value).lower()


# ============================================================
# 5. KNOWN MYTHIC+ DUNGEON NAMES
#
# These are used as strong indicators.
# We are intentionally keeping this list broad rather than
# assuming that every non-raid encounter is trash.
# ============================================================

MYTHIC_PLUS_DUNGEONS = [

    "murder row",
    "ruby life pools",
    "kings' rest",
    "king's rest",
    "altar of fangs",
    "den of nalorakk",
    "the blinding vale",

]


# ============================================================
# 6. KNOWN RAID INDICATORS
#
# These are deliberately generic.
# We will use the actual fight names in the dataset as well.
# ============================================================

RAID_KEYWORDS = [

    "raid",
    "boss",

]


# ============================================================
# 7. CLASSIFICATION FUNCTION
# ============================================================

def classify_fight(row):

    fight_name = normalize_text(
        row.get("fight_name", "")
    )

    zone_name = normalize_text(
        row.get("zone_name", "")
    )

    description = normalize_text(
        row.get("description", "")
    )

    combined = " ".join([
        fight_name,
        zone_name,
        description
    ])


    # --------------------------------------------------------
    # Mythic+ detection
    # --------------------------------------------------------

    for dungeon in MYTHIC_PLUS_DUNGEONS:

        if dungeon in combined:

            return "MYTHIC+", "Dungeon name match"


    # --------------------------------------------------------
    # Raid detection
    #
    # We do NOT automatically classify every named encounter
    # as a raid. This is intentionally conservative.
    # --------------------------------------------------------

    if "raid" in combined:

        return "RAID", "Raid keyword"


    # --------------------------------------------------------
    # Trash detection
    #
    # These are only obvious trash indicators.
    # --------------------------------------------------------

    trash_patterns = [

        r"\btrash\b",
        r"\bpack\b",
        r"\btrash pack\b",
        r"\bgroup\b"

    ]

    for pattern in trash_patterns:

        if re.search(
            pattern,
            combined
        ):

            return "TRASH", "Trash indicator"


    # --------------------------------------------------------
    # Unknown
    # --------------------------------------------------------

    return "UNKNOWN", "No confident classification"


# ============================================================
# 8. APPLY CLASSIFICATION
# ============================================================

print("=" * 70)
print("CLASSIFYING FIGHTS")
print("=" * 70)
print()

classification_results = (

    fights.apply(
        classify_fight,
        axis=1
    )

)


fights[
    "content_type"
] = classification_results.apply(
    lambda x: x[0]
)


fights[
    "classification_reason"
] = classification_results.apply(
    lambda x: x[1]
)


# ============================================================
# 9. CONTENT SUMMARY
# ============================================================

print("=" * 70)
print("CONTENT INVENTORY")
print("=" * 70)
print()

content_counts = (

    fights[
        "content_type"
    ]

    .value_counts()

)


for content_type, count in content_counts.items():

    print(
        f"{content_type:<15} {count:,}"
    )


print()


# ============================================================
# 10. REPORT-LEVEL SUMMARY
# ============================================================

print("=" * 70)
print("REPORT-LEVEL CONTENT SUMMARY")
print("=" * 70)
print()


if "report_code" in fights.columns:

    report_summary = (

        fights

        .groupby(
            "report_code"
        )

        .agg(

            fights=(
                "fight_id",
                "count"
            ),

            content_types=(
                "content_type",
                lambda x:
                    ", ".join(
                        sorted(
                            set(x)
                        )
                    )
            )

        )

        .reset_index()

    )


    print(
        report_summary.to_string(
            index=False
        )
    )


print()


# ============================================================
# 11. SHOW UNKNOWN FIGHTS
# ============================================================

print("=" * 70)
print("UNKNOWN FIGHTS")
print("=" * 70)
print()


unknown_fights = fights[
    fights[
        "content_type"
    ] == "UNKNOWN"
].copy()


print(
    f"Unknown fights: "
    f"{len(unknown_fights):,}"
)


if not unknown_fights.empty:

    display_columns = [

        column

        for column in [

            "report_code",
            "fight_id",
            "fight_name",
            "zone_name",
            "description",
            "classification_reason"

        ]

        if column in unknown_fights.columns

    ]


    print()

    print(
        unknown_fights[
            display_columns
        ].to_string(
            index=False
        )
    )


print()


# ============================================================
# 12. SHOW RAID CANDIDATES
# ============================================================

print("=" * 70)
print("RAID CANDIDATES")
print("=" * 70)
print()


raid_fights = fights[
    fights[
        "content_type"
    ] == "RAID"
].copy()


print(
    f"Raid fights currently classified: "
    f"{len(raid_fights):,}"
)


if not raid_fights.empty:

    display_columns = [

        column

        for column in [

            "report_code",
            "fight_id",
            "fight_name",
            "zone_name",
            "content_type"

        ]

        if column in raid_fights.columns

    ]


    print()

    print(
        raid_fights[
            display_columns
        ].to_string(
            index=False
        )
    )


print()


# ============================================================
# 13. SHOW MYTHIC+ FIGHTS
# ============================================================

print("=" * 70)
print("MYTHIC+ FIGHTS")
print("=" * 70)
print()


mythic_fights = fights[
    fights[
        "content_type"
    ] == "MYTHIC+"
].copy()


print(
    f"Mythic+ fights classified: "
    f"{len(mythic_fights):,}"
)


if not mythic_fights.empty:

    display_columns = [

        column

        for column in [

            "report_code",
            "fight_id",
            "fight_name",
            "zone_name",
            "content_type"

        ]

        if column in mythic_fights.columns

    ]


    print()

    print(
        mythic_fights[
            display_columns
        ].to_string(
            index=False
        )
    )


print()


# ============================================================
# 14. SAVE CLASSIFICATION
# ============================================================

fights.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8"
)


print("=" * 70)
print("V6 COMPLETE")
print("=" * 70)
print()

print(
    "Classification file saved:"
)

print(
    OUTPUT_FILE
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
    "Review the UNKNOWN and RAID CANDIDATE sections."
)

print()

print(
    "Process finished with exit code 0"
)