import json
import os


# ============================================================
# KRONOS INTELLIGENCE
# WORLD OF WARCRAFT RAID ANALYTICS
#
# V3 - STAGE 2A
# RAW DATA VALIDATOR
#
# Purpose:
# Validate the structure of the Warcraft Logs JSON files
# BEFORE we build the full normalization pipeline.
# ============================================================


# ============================================================
# 1. FILE LOCATIONS
# ============================================================

BASE_FOLDER = os.getenv("WOW_RAID_ANALYTICS_BASE", os.getcwd())
RAW_DATA_FOLDER = os.path.join(BASE_FOLDER, "detailed_raw")


# Find the first Damage Done and Damage Taken files
# anywhere underneath detailed_raw.

DAMAGE_DONE_FILE = None
DAMAGE_TAKEN_FILE = None


for root, folders, files in os.walk(RAW_DATA_FOLDER):

    for filename in files:

        if (
            filename.endswith(
                "_DamageDone.json"
            )
            and DAMAGE_DONE_FILE is None
        ):

            DAMAGE_DONE_FILE = os.path.join(
                root,
                filename
            )


        if (
            filename.endswith(
                "_DamageTaken.json"
            )
            and DAMAGE_TAKEN_FILE is None
        ):

            DAMAGE_TAKEN_FILE = os.path.join(
                root,
                filename
            )


# Make sure we actually found them.

if DAMAGE_DONE_FILE is None:

    print(
        "ERROR: Could not find a DamageDone JSON file."
    )

    print(
        "Search location:"
    )

    print(
        RAW_DATA_FOLDER
    )

    raise SystemExit(1)


if DAMAGE_TAKEN_FILE is None:

    print(
        "ERROR: Could not find a DamageTaken JSON file."
    )

    print(
        "Search location:"
    )

    print(
        RAW_DATA_FOLDER
    )

    raise SystemExit(1)


print()
print("Validation files located:")
print()
print(
    "Damage Done:"
)
print(
    DAMAGE_DONE_FILE
)
print()
print(
    "Damage Taken:"
)
print(
    DAMAGE_TAKEN_FILE
)


# ============================================================
# 2. HELPER FUNCTIONS
# ============================================================

def load_json(path):

    print()
    print("Loading:")
    print(path)

    if not os.path.exists(path):

        print("ERROR: File not found.")

        return None

    try:

        with open(
            path,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    except Exception as error:

        print(
            "ERROR reading JSON:",
            error
        )

        return None


def get_entries(data):

    if not isinstance(data, dict):

        return []

    if "data" not in data:

        return []

    inner = data["data"]

    if not isinstance(inner, dict):

        return []

    entries = inner.get(
        "entries",
        []
    )

    if not isinstance(entries, list):

        return []

    return entries


def check_file(
    path,
    expected_type
):

    print()
    print("=" * 70)

    print(
        f"VALIDATING {expected_type}"
    )

    print("=" * 70)

    data = load_json(path)

    if data is None:

        return False


    # --------------------------------------------------------
    # Top level
    # --------------------------------------------------------

    print()
    print("Top-level structure:")

    print(
        list(data.keys())
    )


    if "data" not in data:

        print(
            "FAIL: Missing 'data'."
        )

        return False


    # --------------------------------------------------------
    # Data structure
    # --------------------------------------------------------

    inner = data["data"]

    print()
    print("Data structure:")

    print(
        list(inner.keys())
    )


    required_data_fields = [

        "entries",
        "totalTime",
        "logVersion",
        "gameVersion"

    ]


    print()
    print("Required fields:")


    for field in required_data_fields:

        if field in inner:

            print(
                f"  PASS: {field}"
            )

        else:

            print(
                f"  WARNING: {field} missing"
            )


    # --------------------------------------------------------
    # Entries
    # --------------------------------------------------------

    entries = get_entries(data)

    print()
    print(
        f"Player entries: {len(entries)}"
    )


    if not entries:

        print(
            "FAIL: No player entries."
        )

        return False


    # --------------------------------------------------------
    # Player fields
    # --------------------------------------------------------

    first = entries[0]

    print()
    print("First player:")

    print(
        first.get("name")
    )


    print()
    print("Player fields:")

    expected_player_fields = [

        "name",
        "id",
        "guid",
        "type",
        "icon",
        "itemLevel",
        "total",
        "activeTime",
        "abilities"

    ]


    for field in expected_player_fields:

        if field in first:

            print(
                f"  PASS: {field}"
            )

        else:

            print(
                f"  WARNING: {field} missing"
            )


    # --------------------------------------------------------
    # Numeric validation
    # --------------------------------------------------------

    numeric_fields = [

        "id",
        "itemLevel",
        "total",
        "activeTime"

    ]


    print()
    print("Numeric field validation:")


    for field in numeric_fields:

        values = []

        for entry in entries:

            value = entry.get(
                field
            )

            if value is not None:

                values.append(value)


        if not values:

            print(
                f"  WARNING: No values for {field}"
            )

            continue


        numeric_count = 0


        for value in values:

            if isinstance(
                value,
                (int, float)
            ):

                numeric_count += 1


        print(
            f"  {field}: "
            f"{numeric_count}/{len(values)} numeric"
        )


    # --------------------------------------------------------
    # Ability validation
    # --------------------------------------------------------

    ability_count = 0

    ability_records = 0


    for entry in entries:

        abilities = entry.get(
            "abilities",
            []
        )


        if isinstance(
            abilities,
            list
        ):

            ability_count += 1

            ability_records += len(
                abilities
            )


    print()
    print(
        "Ability validation:"
    )

    print(
        f"  Players with abilities: "
        f"{ability_count}/{len(entries)}"
    )

    print(
        f"  Total ability records: "
        f"{ability_records}"
    )


    # --------------------------------------------------------
    # Damage Done specific checks
    # --------------------------------------------------------

    if expected_type == "Damage Done":

        target_count = 0

        target_records = 0


        for entry in entries:

            targets = entry.get(
                "targets",
                []
            )


            if isinstance(
                targets,
                list
            ):

                target_count += 1

                target_records += len(
                    targets
                )


        print()
        print(
            "Target validation:"
        )

        print(
            f"  Players with targets: "
            f"{target_count}/{len(entries)}"
        )

        print(
            f"  Target records: "
            f"{target_records}"
        )


    # --------------------------------------------------------
    # Damage Taken specific checks
    # --------------------------------------------------------

    if expected_type == "Damage Taken":

        source_count = 0

        source_records = 0


        for entry in entries:

            sources = entry.get(
                "sources",
                []
            )


            if isinstance(
                sources,
                list
            ):

                source_count += 1

                source_records += len(
                    sources
                )


        print()
        print(
            "Source validation:"
        )

        print(
            f"  Players with sources: "
            f"{source_count}/{len(entries)}"
        )

        print(
            f"  Source records: "
            f"{source_records}"
        )


    # --------------------------------------------------------
    # Total calculations
    # --------------------------------------------------------

    total_amount = 0

    total_reduced = 0


    for entry in entries:

        total_amount += (
            entry.get(
                "total",
                0
            ) or 0
        )

        total_reduced += (
            entry.get(
                "totalReduced",
                0
            ) or 0
        )


    print()
    print("Aggregate totals:")

    print(
        f"  Total: {total_amount:,}"
    )

    print(
        f"  Total Reduced: "
        f"{total_reduced:,}"
    )


    # --------------------------------------------------------
    # Sample player records
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("SAMPLE PLAYER DATA")
    print("=" * 70)


    for entry in entries[:5]:

        print()

        print(
            "Player:",
            entry.get("name")
        )

        print(
            "ID:",
            entry.get("id")
        )

        print(
            "Spec/Class:",
            entry.get("type")
        )

        print(
            "Item Level:",
            entry.get("itemLevel")
        )

        print(
            "Total:",
            f"{entry.get('total', 0):,}"
        )

        print(
            "Active Time:",
            entry.get("activeTime")
        )

        print(
            "Abilities:",
            len(
                entry.get(
                    "abilities",
                    []
                )
            )
        )


    print()
    print(
        f"{expected_type} validation complete."
    )

    return True


# ============================================================
# 3. RUN VALIDATION
# ============================================================

print("=" * 70)
print("KRONOS INTELLIGENCE")
print("WORLD OF WARCRAFT RAID ANALYTICS")
print("V3 - STAGE 2A RAW DATA VALIDATOR")
print("=" * 70)


damage_done_ok = check_file(

    DAMAGE_DONE_FILE,

    "Damage Done"

)


damage_taken_ok = check_file(

    DAMAGE_TAKEN_FILE,

    "Damage Taken"

)


# ============================================================
# 4. FINAL RESULT
# ============================================================

print()
print("=" * 70)
print("VALIDATION SUMMARY")
print("=" * 70)

print()

print(
    "Damage Done:",
    "PASS" if damage_done_ok else "FAIL"
)

print(
    "Damage Taken:",
    "PASS" if damage_taken_ok else "FAIL"
)

print()

if (
    damage_done_ok
    and damage_taken_ok
):

    print(
        "RAW DATA VALIDATION PASSED"
    )

    print()

    print(
        "The Warcraft Logs JSON structure "
        "is suitable for normalization."
    )

else:

    print(
        "RAW DATA VALIDATION FAILED"
    )

    print(
        "Do not proceed to normalization yet."
    )

print()
print("=" * 70)