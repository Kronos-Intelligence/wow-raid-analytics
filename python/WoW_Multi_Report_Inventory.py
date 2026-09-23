import requests
import pandas as pd
import os
import time
from datetime import datetime


# ============================================================
# KRONOS INTELLIGENCE
# WORLD OF WARCRAFT RAID ANALYTICS
#
# MULTI-REPORT INVENTORY BUILDER
#
# STAGE 1
#
# Purpose:
#   Retrieve every fight from a list of Warcraft Logs reports
#   and build one master fight inventory.
# ============================================================


# ============================================================
# 1. WARCRAFT LOGS CREDENTIALS
# ============================================================

# ------------------------------------------------------------
# Read API credentials from environment variables; never hard-code secrets.
# ------------------------------------------------------------

CLIENT_ID = os.getenv("WCL_CLIENT_ID")


# ------------------------------------------------------------

# ------------------------------------------------------------

CLIENT_SECRET = os.getenv("WCL_CLIENT_SECRET")


# ============================================================
# 2. WARCRAFT LOGS API SETTINGS
# ============================================================

TOKEN_URL = (
    "https://www.warcraftlogs.com/oauth/token"
)

API_URL = (
    "https://www.warcraftlogs.com/api/v2/client"
)


# ============================================================
# 3. OUTPUT LOCATION
# ============================================================

OUTPUT_FOLDER = (
    r"${WOW_RAID_ANALYTICS_BASE}"
)

os.makedirs(
    OUTPUT_FOLDER,
    exist_ok=True
)


# ============================================================
# 4. REPORT CODES
# ============================================================

# These are the reports from the document you provided.

REPORT_CODES = [

    "MhK4B7L8VF1rvNw6",

    "bdqfKFjLQXvM1ZJp",

    "7fgDKpMGWzkq8Hbm",

    "1aJTBNphf8C4jGbr",

    "3gymwM9c2Av4Xk6r",

    "g2CL3b8YmcKyGwQD",

    "NQ4D9vqkTjV16MPC",

    "LMnThDVqdjya46v2",

    "DVPfBvHpYFwytd2G",

    "31PjbgTG8KDC9JBh",

    "D6gZPwN8vC1qAXKH",

    "3VrDYLzQHKtTyAFX",

    "wqVm27KgQbYRd8pn",

    "mYTZPFwjfK8xbHQ1",

    "H3WNRQj9wTF2kmc4",

    "2Hn6qhfTFaYytXrD",

    "mYdNtv2y6cRWXB4z",

    "1Pwx2hQvg7cDZbC9",

    "tmpfDPYH8C6vFAzh",

    "hY2VNwq1nWfMKFxm",

    "GBXcvzpjkJAxCH6P",

    "XvwLCVdhJKY73zHr",

    "yFTfaACXnD61KtLY"

]


# ============================================================
# 5. GRAPHQL QUERY
# ============================================================

REPORT_QUERY = """

query GetReport($code: String!) {

    reportData {

        report(code: $code) {

            code
            title
            startTime
            endTime
            visibility

            zone {
                id
                name
            }

            fights {

                id
                name
                encounterID

                startTime
                endTime

                kill
                inProgress

                difficulty

                fightPercentage
                bossPercentage

                averageItemLevel
                size

                friendlyPlayers
                friendlyItemLevels
                friendlySpecs

                enemyPlayers

                originalEncounterID

                lastPhase
                lastPhaseAsAbsoluteIndex
                lastPhaseIsIntermission

            }

        }

    }

}

"""


# ============================================================
# 6. GET ACCESS TOKEN
# ============================================================

def get_access_token():

    print()
    print("=" * 70)
    print("AUTHENTICATING WITH WARCRAFT LOGS")
    print("=" * 70)
    print()

    if (
        CLIENT_ID.startswith("<<<")
        or CLIENT_SECRET.startswith("<<<")
    ):

        print(
            "ERROR: You have not entered your Client ID "
            "and/or Client Secret."
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
            "ERROR: Authentication failed."
        )

        print(
            "Status:",
            response.status_code
        )

        print(
            response.text
        )

        raise SystemExit(1)


    token_data = response.json()

    access_token = token_data.get(
        "access_token"
    )


    if not access_token:

        print(
            "ERROR: No access token returned."
        )

        print(
            response.text
        )

        raise SystemExit(1)


    print(
        "Authentication successful."
    )

    print()

    return access_token


# ============================================================
# 7. GRAPHQL REQUEST
# ============================================================

def get_report(
    access_token,
    report_code
):

    headers = {

        "Authorization":
            f"Bearer {access_token}",

        "Content-Type":
            "application/json",

        "Accept":
            "application/json"

    }


    payload = {

        "query":
            REPORT_QUERY,

        "variables": {

            "code":
                report_code

        }

    }


    response = requests.post(

        API_URL,

        headers=headers,

        json=payload,

        timeout=60

    )


    if response.status_code != 200:

        print(
            f"HTTP ERROR for {report_code}: "
            f"{response.status_code}"
        )

        print(
            response.text[:500]
        )

        return None


    result = response.json()


    if "errors" in result:

        print(
            f"GRAPHQL ERROR for {report_code}:"
        )

        for error in result["errors"]:

            print(
                error.get("message")
            )

        return None


    return result.get(
        "data",
        {}
    ).get(
        "reportData",
        {}
    ).get(
        "report"
    )


# ============================================================
# 8. CONVERT FIGHT TO INVENTORY RECORD
# ============================================================

def create_fight_record(
    report,
    fight
):

    report_start = report.get(
        "startTime"
    )


    fight_start = fight.get(
        "startTime"
    )


    fight_end = fight.get(
        "endTime"
    )


    duration_seconds = None


    if (
        fight_start is not None
        and fight_end is not None
    ):

        duration_seconds = (
            fight_end
            - fight_start
        ) / 1000


    report_date = None


    if report_start:

        report_date = (
            datetime.fromtimestamp(
                report_start / 1000
            ).strftime(
                "%Y-%m-%d"
            )
        )


    friendly_players = (
        fight.get(
            "friendlyPlayers"
        )
        or []
    )


    return {

        "report_code":
            report.get("code"),

        "report_title":
            report.get("title"),

        "report_date":
            report_date,

        "report_start_time":
            report_start,

        "report_end_time":
            report.get("endTime"),

        "visibility":
            report.get("visibility"),

        "zone_id":
            (
                report.get("zone")
                or {}
            ).get("id"),

        "zone_name":
            (
                report.get("zone")
                or {}
            ).get("name"),

        "fight_id":
            fight.get("id"),

        "fight_name":
            fight.get("name"),

        "encounter_id":
            fight.get("encounterID"),

        "original_encounter_id":
            fight.get(
                "originalEncounterID"
            ),

        "fight_start_time":
            fight_start,

        "fight_end_time":
            fight_end,

        "duration_seconds":
            duration_seconds,

        "kill":
            fight.get("kill"),

        "in_progress":
            fight.get("inProgress"),

        "difficulty":
            fight.get("difficulty"),

        "fight_percentage":
            fight.get(
                "fightPercentage"
            ),

        "boss_percentage":
            fight.get(
                "bossPercentage"
            ),

        "average_item_level":
            fight.get(
                "averageItemLevel"
            ),

        "raid_size":
            fight.get("size"),

        "player_count":
            len(friendly_players),

        "player_ids":
            ",".join(
                str(x)
                for x in friendly_players
            ),

        "friendly_item_levels":
            ",".join(
                str(x)
                for x in (
                    fight.get(
                        "friendlyItemLevels"
                    )
                    or []
                )
            ),

        "friendly_specs":
            ",".join(
                str(x)
                for x in (
                    fight.get(
                        "friendlySpecs"
                    )
                    or []
                )
            ),

        "enemy_player_count":
            len(
                fight.get(
                    "enemyPlayers"
                )
                or []
            ),

        "last_phase":
            fight.get("lastPhase"),

        "last_phase_absolute":
            fight.get(
                "lastPhaseAsAbsoluteIndex"
            ),

        "last_phase_intermission":
            fight.get(
                "lastPhaseIsIntermission"
            )

    }


# ============================================================
# 9. MAIN PROCESS
# ============================================================

print("=" * 70)
print("KRONOS INTELLIGENCE")
print("WORLD OF WARCRAFT RAID ANALYTICS")
print("MULTI-REPORT INVENTORY BUILDER")
print("=" * 70)

print()

print(
    "Reports queued:",
    len(REPORT_CODES)
)

print()

access_token = get_access_token()


all_fights = []

successful_reports = 0

failed_reports = []


# ============================================================
# PROCESS REPORTS
# ============================================================

for index, report_code in enumerate(
    REPORT_CODES,
    start=1
):

    print(
        f"[{index}/{len(REPORT_CODES)}] "
        f"Retrieving report {report_code}..."
    )


    report = get_report(
        access_token,
        report_code
    )


    if report is None:

        print(
            "  FAILED"
        )

        failed_reports.append(
            report_code
        )

        continue


    successful_reports += 1


    fights = report.get(
        "fights"
    ) or []


    print(
        f"  Report: "
        f"{report.get('title')}"
    )


    print(
        f"  Fights found: "
        f"{len(fights)}"
    )


    for fight in fights:

        record = create_fight_record(
            report,
            fight
        )

        all_fights.append(
            record
        )


    print(
        "  SUCCESS"
    )

    print()


    # Small pause to avoid hammering API

    time.sleep(0.25)


# ============================================================
# SAVE INVENTORY
# ============================================================

print()
print("=" * 70)
print("BUILDING FIGHT INVENTORY")
print("=" * 70)
print()


if not all_fights:

    print(
        "ERROR: No fights were retrieved."
    )

    raise SystemExit(1)


inventory = pd.DataFrame(
    all_fights
)


inventory = inventory.sort_values(
    [
        "report_date",
        "report_code",
        "fight_id"
    ]
)


output_path = os.path.join(
    OUTPUT_FOLDER,
    "fight_inventory.csv"
)


inventory.to_csv(
    output_path,
    index=False,
    encoding="utf-8"
)


# ============================================================
# SUMMARY
# ============================================================

print(
    "Reports successful:",
    successful_reports
)

print(
    "Reports failed:",
    len(failed_reports)
)

print(
    "Total fights:",
    len(inventory)
)

print()

print(
    "Inventory saved:"
)

print(
    os.path.abspath(
        output_path
    )
)

print()


# ============================================================
# QUICK BREAKDOWN
# ============================================================

print("=" * 70)
print("FIGHT BREAKDOWN")
print("=" * 70)
print()


boss_fights = inventory[
    inventory["encounter_id"] != 0
]


trash_fights = inventory[
    inventory["encounter_id"] == 0
]


kills = inventory[
    inventory["kill"] == True
]


wipes = inventory[
    inventory["kill"] == False
]


print(
    "Total fights:",
    len(inventory)
)

print(
    "Boss/encounter fights:",
    len(boss_fights)
)

print(
    "Trash fights:",
    len(trash_fights)
)

print(
    "Kills:",
    len(kills)
)

print(
    "Wipes:",
    len(wipes)
)


print()


# ============================================================
# BOSS SUMMARY
# ============================================================

print("=" * 70)
print("BOSS SUMMARY")
print("=" * 70)
print()


if len(boss_fights) > 0:

    boss_summary = (

        boss_fights

        .groupby(
            "fight_name",
            dropna=False
        )

        .agg(

            attempts=(
                "fight_id",
                "count"
            ),

            kills=(
                "kill",
                "sum"
            ),

            average_duration=(
                "duration_seconds",
                "mean"
            ),

            average_ilvl=(
                "average_item_level",
                "mean"
            )

        )

        .reset_index()

    )


    print(
        boss_summary.to_string(
            index=False
        )
    )


# ============================================================
# FAILED REPORTS
# ============================================================

if failed_reports:

    print()
    print("=" * 70)
    print("REPORTS THAT FAILED")
    print("=" * 70)
    print()

    for code in failed_reports:

        print(
            code
        )


# ============================================================
# COMPLETE
# ============================================================

print()
print("=" * 70)
print("INVENTORY BUILD COMPLETE")
print("=" * 70)
print()

print(
    "Next step:"
)

print(
    "Review fight_inventory.csv before pulling detailed data."
)

print()

print(
    "Process finished."
)