import requests
import pandas as pd
import os
import json
import time


# ============================================================
# KRONOS INTELLIGENCE
# WORLD OF WARCRAFT RAID ANALYTICS
#
# V3 - STAGE 2
# DETAILED FIGHT EXTRACTOR
#
# Reads fight_inventory.csv
# Finds actual boss encounters
# Pulls detailed Warcraft Logs TABLE data
# Saves raw JSON for each fight
#
# We will normalize this data in the next step.
# ============================================================


# ============================================================
# 1. YOUR WARCRAFT LOGS CREDENTIALS
# ============================================================

# ------------------------------------------------------------
# Read API credentials from environment variables; never hard-code secrets.
# ------------------------------------------------------------

CLIENT_ID = os.getenv("WCL_CLIENT_ID")


# ------------------------------------------------------------

# ------------------------------------------------------------

CLIENT_SECRET = os.getenv("WCL_CLIENT_SECRET")


# ============================================================
# 2. API SETTINGS
# ============================================================

TOKEN_URL = (
    "https://www.warcraftlogs.com/oauth/token"
)

API_URL = (
    "https://www.warcraftlogs.com/api/v2/client"
)


# ============================================================
# 3. FILE LOCATIONS
# ============================================================

BASE_FOLDER = os.getenv("WOW_RAID_ANALYTICS_BASE", os.getcwd())
INVENTORY_PATH = os.path.join(BASE_FOLDER, "fight_inventory.csv")


OUTPUT_FOLDER = os.path.join(BASE_FOLDER, "detailed_raw")


os.makedirs(
    OUTPUT_FOLDER,
    exist_ok=True
)


# ============================================================
# 4. DATA TYPES WE WANT
# ============================================================

DATA_TYPES = [

    "DamageDone",

    "DamageTaken",

    "Healing",

    "Deaths",

    "Interrupts",

    "Dispels",

    "Casts"

]


# ============================================================
# 5. GRAPHQL QUERY
# ============================================================

TABLE_QUERY = """

query GetFightTable(
    $code: String!,
    $fightIDs: [Int!],
    $dataType: TableDataType!
) {

    reportData {

        report(code: $code) {

            code
            title
            startTime
            endTime

            table(
                dataType: $dataType
                fightIDs: $fightIDs
                translate: true
            )

        }

    }

}

"""


# ============================================================
# 6. AUTHENTICATION
# ============================================================

def get_access_token():

    print()
    print("=" * 70)
    print("AUTHENTICATING")
    print("=" * 70)
    print()

    if (
        CLIENT_ID.startswith("<<<")
        or CLIENT_SECRET.startswith("<<<")
    ):

        print(
            "ERROR: Enter your Client ID and Client Secret."
        )

        raise SystemExit(1)


    response = requests.post(

        TOKEN_URL,

        data={
            "grant_type":
                "client_credentials"
        },

        auth=(
            CLIENT_ID,
            CLIENT_SECRET
        ),

        timeout=30

    )


    if response.status_code != 200:

        print(
            "Authentication failed."
        )

        print(
            "Status:",
            response.status_code
        )

        print(
            response.text
        )

        raise SystemExit(1)


    token = response.json().get(
        "access_token"
    )


    if not token:

        print(
            "ERROR: No access token returned."
        )

        raise SystemExit(1)


    print(
        "Authentication successful."
    )

    print()

    return token


# ============================================================
# 7. REQUEST TABLE DATA
# ============================================================

def get_table_data(
    access_token,
    report_code,
    fight_id,
    data_type
):

    headers = {

        "Authorization":
            f"Bearer {access_token}",

        "Content-Type":
            "application/json",

        "Accept":
            "application/json"

    }


    variables = {

        "code":
            report_code,

        "fightIDs":
            [int(fight_id)],

        "dataType":
            data_type

    }


    payload = {

        "query":
            TABLE_QUERY,

        "variables":
            variables

    }


    response = requests.post(

        API_URL,

        headers=headers,

        json=payload,

        timeout=120

    )


    if response.status_code != 200:

        print(
            f"HTTP ERROR: "
            f"{response.status_code}"
        )

        print(
            response.text[:1000]
        )

        return None


    result = response.json()


    if "errors" in result:

        print(
            "GRAPHQL ERROR:"
        )

        for error in result["errors"]:

            print(
                error.get(
                    "message",
                    error
                )
            )

        return None


    report_data = (
        result
        .get("data", {})
        .get("reportData", {})
        .get("report")
    )


    if report_data is None:

        print(
            "ERROR: Report was not returned."
        )

        return None


    return report_data.get(
        "table"
    )


# ============================================================
# 8. SAFE FILE NAME
# ============================================================

def safe_filename(value):

    invalid = (
        '<>:"/\\|?*'
    )

    for char in invalid:

        value = value.replace(
            char,
            "_"
        )

    return value


# ============================================================
# 9. LOAD INVENTORY
# ============================================================

print("=" * 70)
print("KRONOS INTELLIGENCE")
print("WORLD OF WARCRAFT RAID ANALYTICS")
print("V3 - STAGE 2")
print("=" * 70)
print()


if not os.path.exists(
    INVENTORY_PATH
):

    print(
        "ERROR: fight_inventory.csv was not found."
    )

    print()

    print(
        "Expected location:"
    )

    print(
        INVENTORY_PATH
    )

    raise SystemExit(1)


inventory = pd.read_csv(
    INVENTORY_PATH
)


print(
    "Inventory loaded."
)

print(
    f"Total inventory rows: "
    f"{len(inventory)}"
)

print()


# ============================================================
# 10. IDENTIFY REAL BOSS ENCOUNTERS
# ============================================================

# encounter_id > 0 identifies actual encounters.
#
# This intentionally excludes:
#
#   - trash
#   - training dummies
#   - miscellaneous NPCs
#   - short transition records
#
# We also require a positive duration.

boss_fights = inventory[
    (
        inventory["encounter_id"]
        .fillna(0)
        > 0
    )
    &
    (
        inventory["duration_seconds"]
        .fillna(0)
        > 5
    )
].copy()


print(
    "Boss fights selected:"
)

print(
    len(boss_fights)
)

print()


# ============================================================
# 11. SHOW WHAT WILL BE PROCESSED
# ============================================================

print("=" * 70)
print("BOSS FIGHTS SELECTED")
print("=" * 70)
print()


summary = (

    boss_fights

    .groupby(
        [
            "report_date",
            "fight_name"
        ]
    )

    .agg(
        attempts=(
            "fight_id",
            "count"
        ),

        kills=(
            "kill",
            "sum"
        )
    )

    .reset_index()

)


print(
    summary.to_string(
        index=False
    )
)

print()


# ============================================================
# 12. AUTHENTICATE
# ============================================================

access_token = get_access_token()


# ============================================================
# 13. EXTRACTION COUNTERS
# ============================================================

successful = 0

failed = 0

total_requests = 0


# ============================================================
# 14. PROCESS EACH FIGHT
# ============================================================

for index, row in boss_fights.iterrows():

    report_code = str(
        row["report_code"]
    )

    fight_id = int(
        row["fight_id"]
    )

    fight_name = str(
        row["fight_name"]
    )

    report_date = str(
        row["report_date"]
    )


    print()
    print("=" * 70)

    print(
        f"FIGHT "
        f"{index + 1} / "
        f"{len(boss_fights)}"
    )

    print(
        f"Date: {report_date}"
    )

    print(
        f"Report: {report_code}"
    )

    print(
        f"Fight ID: {fight_id}"
    )

    print(
        f"Boss: {fight_name}"
    )

    print(
        f"Result: "
        f"{'KILL' if row['kill'] else 'WIPE'}"
    )

    print("=" * 70)


    # --------------------------------------------------------
    # Folder for this report
    # --------------------------------------------------------

    report_folder = os.path.join(

        OUTPUT_FOLDER,

        safe_filename(
            report_code
        )

    )


    os.makedirs(
        report_folder,
        exist_ok=True
    )


    # --------------------------------------------------------
    # Metadata about the fight
    # --------------------------------------------------------

    fight_metadata = {

        "report_code":
            report_code,

        "report_date":
            report_date,

        "report_title":
            row["report_title"],

        "fight_id":
            fight_id,

        "fight_name":
            fight_name,

        "encounter_id":
            int(row["encounter_id"]),

        "kill":
            bool(row["kill"]),

        "duration_seconds":
            float(
                row["duration_seconds"]
            ),

        "difficulty":
            row["difficulty"],

        "raid_size":
            row["raid_size"],

        "player_count":
            row["player_count"]

    }


    metadata_path = os.path.join(

        report_folder,

        f"fight_{fight_id}_metadata.json"

    )


    with open(
        metadata_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            fight_metadata,
            file,
            indent=2
        )


    # --------------------------------------------------------
    # Pull each data type
    # --------------------------------------------------------

    fight_success = True


    for data_type in DATA_TYPES:

        print(
            f"  Pulling {data_type}..."
        )


        table = get_table_data(

            access_token,

            report_code,

            fight_id,

            data_type

        )


        total_requests += 1


        if table is None:

            print(
                f"    FAILED: "
                f"{data_type}"
            )

            fight_success = False

            continue


        output_file = os.path.join(

            report_folder,

            (
                f"fight_"
                f"{fight_id}_"
                f"{data_type}.json"
            )

        )


        with open(
            output_file,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                table,
                file,
                indent=2
            )


        print(
            f"    Saved."
        )


        time.sleep(
            0.20
        )


    if fight_success:

        successful += 1

    else:

        failed += 1


# ============================================================
# 15. SAVE SELECTED FIGHT INVENTORY
# ============================================================

selected_inventory_path = os.path.join(

    OUTPUT_FOLDER,

    "selected_boss_fights.csv"

)


boss_fights.to_csv(

    selected_inventory_path,

    index=False,

    encoding="utf-8"

)


# ============================================================
# 16. FINAL SUMMARY
# ============================================================

print()
print("=" * 70)
print("STAGE 2 EXTRACTION COMPLETE")
print("=" * 70)
print()

print(
    f"Boss fights selected: "
    f"{len(boss_fights)}"
)

print(
    f"Successful fights: "
    f"{successful}"
)

print(
    f"Fights with failures: "
    f"{failed}"
)

print(
    f"API table requests attempted: "
    f"{total_requests}"
)

print()

print(
    "Output folder:"
)

print(
    os.path.abspath(
        OUTPUT_FOLDER
    )
)

print()

print(
    "Selected fight inventory:"
)

print(
    os.path.abspath(
        selected_inventory_path
    )
)

print()

print(
    "STAGE 2 COMPLETE"
)

print(
    "Do not normalize the JSON yet."
)

print(
    "We will validate the raw extraction first."
)