
import csv
import json
import os
import re
from collections import defaultdict
from pathlib import Path

try:
    import requests
except ImportError:
    requests = None

# ============================================================
# KRONOS INTELLIGENCE
# WORLD OF WARCRAFT RAID ANALYTICS
# FINAL UTILITY + WIPE PROGRESS PATCH
#
# FIXES:
#   1. Rebuilds interrupt/dispel detail tables WITHOUT
#      incorrectly deduplicating repeated ability rows.
#      This reconciles detail totals to the Warcraft Logs
#      player/fight aggregate counts.
#
#   2. Retrieves Warcraft Logs fightPercentage and
#      bossPercentage directly from the Warcraft Logs API.
#      These values are NOT present in detailed_raw metadata.
#
# IMPORTANT:
#   player_name remains the longitudinal player key.
#   Existing COMPLETE player/fight and healing data is not rebuilt.
# ============================================================

BASE = Path(
    r"${WOW_RAID_ANALYTICS_BASE}"
)

MASTER = BASE / "Wow_Analytics_Master_copies"
RAW = BASE / "detailed_raw"

# The detailed_raw ZIP can also be used if the extracted folder
# is not present.
RAW_ZIP = BASE / "detailed_raw.zip"

PLAYER_MASTER = MASTER / "player_fight_master_COMPLETE.csv"
FIGHT_MASTER = MASTER / "fight_inventory_master_COMPLETE.csv"

OUT_PLAYER = MASTER / "player_fight_master_FINAL_COMPLETE.csv"
OUT_FIGHTS = MASTER / "fight_inventory_master_FINAL_COMPLETE.csv"
OUT_INTERRUPTS = MASTER / "player_interrupt_events_FINAL_COMPLETE.csv"
OUT_DISPELS = MASTER / "player_dispel_events_FINAL_COMPLETE.csv"

EXPECTED_FIGHTS = 205


# ============================================================
# HELPERS
# ============================================================

def load_csv(path):
    with path.open(
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as f:
        return list(csv.DictReader(f))


def write_csv(path, rows):
    if not rows:
        raise RuntimeError(
            f"Refusing to write empty output: {path}"
        )

    fields = []
    seen = set()

    for row in rows:
        for key in row:
            if key not in seen:
                seen.add(key)
                fields.append(key)

    with path.open(
        "w",
        encoding="utf-8-sig",
        newline=""
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=fields,
            extrasaction="ignore"
        )
        writer.writeheader()
        writer.writerows(rows)


def load_json(path):
    with path.open(
        "r",
        encoding="utf-8-sig"
    ) as f:
        return json.load(f)


def safe_int(value):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def norm(value):
    return str(value or "").strip().lower()


def fight_id_from_filename(name):
    match = re.match(
        r"fight_(\d+)_",
        name,
        flags=re.IGNORECASE
    )
    return match.group(1) if match else ""


def report_from_path(path, report_codes):
    parent = path.parent.name

    if parent in report_codes:
        return parent

    lower = {
        norm(x): x
        for x in report_codes
    }

    if norm(parent) in lower:
        return lower[norm(parent)]

    for part in path.parts:
        if part in report_codes:
            return part

    for part in path.parts:
        if norm(part) in lower:
            return lower[norm(part)]

    return ""


def find_raw_files(pattern):
    if RAW.exists():
        return sorted(
            RAW.rglob(pattern)
        )

    return []


# ============================================================
# LOAD MASTER DATA
# ============================================================

print("=" * 70)
print("KRONOS INTELLIGENCE")
print("WORLD OF WARCRAFT RAID ANALYTICS")
print("FINAL UTILITY + WIPE PROGRESS PATCH")
print("=" * 70)

if not PLAYER_MASTER.exists():
    raise FileNotFoundError(
        f"Missing: {PLAYER_MASTER}"
    )

if not FIGHT_MASTER.exists():
    raise FileNotFoundError(
        f"Missing: {FIGHT_MASTER}"
    )

players = load_csv(
    PLAYER_MASTER
)

fights = load_csv(
    FIGHT_MASTER
)

print()
print(
    f"Player/fight rows: {len(players):,}"
)
print(
    f"Fight inventory rows: {len(fights):,}"
)

if len(fights) != EXPECTED_FIGHTS:
    raise RuntimeError(
        f"Expected {EXPECTED_FIGHTS} raid fights; "
        f"found {len(fights)}."
    )

report_codes = {
    str(row.get("report_code", ""))
    for row in fights
    if row.get("report_code")
}


# ============================================================
# 1. REBUILD INTERRUPTS WITHOUT LOSING REPEATED ROWS
# ============================================================

print()
print("=" * 70)
print("REBUILDING INTERRUPT DETAIL")
print("=" * 70)

interrupt_files = find_raw_files(
    "fight_*_Interrupts.json"
)

print(
    f"Interrupt raw files found: {len(interrupt_files):,}"
)

interrupt_agg = defaultdict(int)

for path in interrupt_files:

    report = report_from_path(
        path,
        report_codes
    )

    fight_id = fight_id_from_filename(
        path.name
    )

    if not report or not fight_id:
        continue

    data = load_json(path)

    try:
        outer_entries = data["data"]["entries"]
    except (KeyError, TypeError):
        continue

    if not isinstance(
        outer_entries,
        list
    ):
        continue

    for outer in outer_entries:

        if not isinstance(
            outer,
            dict
        ):
            continue

        interrupted_ability = str(
            outer.get("name", "")
        ).strip()

        nested = outer.get(
            "entries",
            []
        )

        if not isinstance(
            nested,
            list
        ):
            continue

        for spell_group in nested:

            if not isinstance(
                spell_group,
                dict
            ):
                continue

            details = spell_group.get(
                "details",
                []
            )

            if not isinstance(
                details,
                list
            ):
                continue

            for player in details:

                if not isinstance(
                    player,
                    dict
                ):
                    continue

                player_name = str(
                    player.get("name", "")
                ).strip()

                if not player_name:
                    continue

                abilities = player.get(
                    "abilities",
                    []
                )

                if not isinstance(
                    abilities,
                    list
                ):
                    continue

                for ability in abilities:

                    if not isinstance(
                        ability,
                        dict
                    ):
                        continue

                    interrupting_ability = str(
                        ability.get("name", "")
                    ).strip()

                    count = safe_int(
                        ability.get("total")
                    )

                    if (
                        not interrupting_ability
                        or count <= 0
                    ):
                        continue

                    key = (
                        report,
                        str(fight_id),
                        player_name,
                        interrupted_ability,
                        interrupting_ability,
                    )

                    interrupt_agg[key] += count


interrupt_rows = []

for key, count in sorted(
    interrupt_agg.items()
):

    (
        report,
        fight_id,
        player_name,
        interrupted_ability,
        interrupting_ability,
    ) = key

    interrupt_rows.append({
        "report_code": report,
        "fight_id": fight_id,
        "player_name": player_name,
        "interrupted_ability":
            interrupted_ability,
        "interrupting_ability":
            interrupting_ability,
        "count": count,
    })

print(
    f"Interrupt detail rows: {len(interrupt_rows):,}"
)
print(
    f"Interrupt detail total: "
    f"{sum(r['count'] for r in interrupt_rows):,}"
)


# ============================================================
# 2. REBUILD DISPELS WITHOUT LOSING REPEATED ROWS
# ============================================================

print()
print("=" * 70)
print("REBUILDING DISPEL DETAIL")
print("=" * 70)

dispel_files = find_raw_files(
    "fight_*_Dispels.json"
)

print(
    f"Dispel raw files found: {len(dispel_files):,}"
)

dispel_agg = defaultdict(int)

for path in dispel_files:

    report = report_from_path(
        path,
        report_codes
    )

    fight_id = fight_id_from_filename(
        path.name
    )

    if not report or not fight_id:
        continue

    data = load_json(path)

    try:
        outer_entries = data["data"]["entries"]
    except (KeyError, TypeError):
        continue

    if not isinstance(
        outer_entries,
        list
    ):
        continue

    for outer in outer_entries:

        if not isinstance(
            outer,
            dict
        ):
            continue

        dispelled_ability = str(
            outer.get("name", "")
        ).strip()

        nested = outer.get(
            "entries",
            []
        )

        if not isinstance(
            nested,
            list
        ):
            continue

        for spell_group in nested:

            if not isinstance(
                spell_group,
                dict
            ):
                continue

            details = spell_group.get(
                "details",
                []
            )

            if not isinstance(
                details,
                list
            ):
                continue

            for player in details:

                if not isinstance(
                    player,
                    dict
                ):
                    continue

                player_name = str(
                    player.get("name", "")
                ).strip()

                if not player_name:
                    continue

                abilities = player.get(
                    "abilities",
                    []
                )

                if not isinstance(
                    abilities,
                    list
                ):
                    continue

                for ability in abilities:

                    if not isinstance(
                        ability,
                        dict
                    ):
                        continue

                    dispelling_ability = str(
                        ability.get("name", "")
                    ).strip()

                    count = safe_int(
                        ability.get("total")
                    )

                    if (
                        not dispelling_ability
                        or count <= 0
                    ):
                        continue

                    key = (
                        report,
                        str(fight_id),
                        player_name,
                        dispelled_ability,
                        dispelling_ability,
                    )

                    dispel_agg[key] += count


dispel_rows = []

for key, count in sorted(
    dispel_agg.items()
):

    (
        report,
        fight_id,
        player_name,
        dispelled_ability,
        dispelling_ability,
    ) = key

    dispel_rows.append({
        "report_code": report,
        "fight_id": fight_id,
        "player_name": player_name,
        "dispelled_ability":
            dispelled_ability,
        "dispelling_ability":
            dispelling_ability,
        "count": count,
    })

print(
    f"Dispel detail rows: {len(dispel_rows):,}"
)
print(
    f"Dispel detail total: "
    f"{sum(r['count'] for r in dispel_rows):,}"
)


# ============================================================
# 3. RECONCILE UTILITY TOTALS TO PLAYER/FIGHT MASTER
# ============================================================

master_interrupt_total = sum(
    safe_int(
        row.get("interrupt_count")
    )
    for row in players
)

master_dispel_total = sum(
    safe_int(
        row.get("dispel_count")
    )
    for row in players
)

detail_interrupt_total = sum(
    r["count"]
    for r in interrupt_rows
)

detail_dispel_total = sum(
    r["count"]
    for r in dispel_rows
)

print()
print("=" * 70)
print("UTILITY RECONCILIATION")
print("=" * 70)

print(
    f"Master interrupt total: {master_interrupt_total:,}"
)
print(
    f"Detail interrupt total: {detail_interrupt_total:,}"
)

print(
    f"Master dispel total:    {master_dispel_total:,}"
)
print(
    f"Detail dispel total:    {detail_dispel_total:,}"
)

if master_interrupt_total != detail_interrupt_total:
    raise RuntimeError(
        "Interrupt detail does not reconcile to the "
        "player/fight master."
    )

if master_dispel_total != detail_dispel_total:
    raise RuntimeError(
        "Dispel detail does not reconcile to the "
        "player/fight master."
    )

print()
print("UTILITY TOTALS RECONCILE: YES")


# ============================================================
# 4. WARCRAFT LOGS API CREDENTIALS
#
# Preferred:
#   WCL_CLIENT_ID
#   WCL_CLIENT_SECRET
#
# If those are not set, this script will try to read the
# existing local "Wow Analytics.py" file and extract the
# credentials already used by the user's prior API script.
#
# The credentials are never written to an output file.
# ============================================================

def load_credentials():

    client_id = os.getenv(
        "WCL_CLIENT_ID"
    )

    client_secret = os.getenv(
        "WCL_CLIENT_SECRET"
    )

    if client_id and client_secret:
        return client_id, client_secret

    candidates = [
        BASE / "Wow Analytics.py",
        Path.cwd() / "Wow Analytics.py",
    ]

    for candidate in candidates:

        if not candidate.exists():
            continue

        text = candidate.read_text(
            encoding="utf-8",
            errors="ignore"
        )

        id_match = re.search(
            r'CLIENT_ID\s*=\s*["\']([^"\']+)["\']',
            text
        )

        secret_match = re.search(
            r'CLIENT_SECRET\s*=\s*["\']([^"\']+)["\']',
            text
        )

        if id_match and secret_match:
            print(
                f"Using Warcraft Logs credentials from: "
                f"{candidate}"
            )

            return (
                id_match.group(1),
                secret_match.group(1)
            )

    return None, None


# ============================================================
# 5. FETCH FIGHT PERCENTAGES FROM WARCRAFT LOGS
#
# detailed_raw metadata does not contain these fields.
# The Warcraft Logs fight object does.
# ============================================================

print()
print("=" * 70)
print("RETRIEVING WIPE PROGRESS FROM WARCRAFT LOGS")
print("=" * 70)

if requests is None:
    raise RuntimeError(
        "The 'requests' package is required. "
        "Install it in the same Python environment used "
        "for the analytics scripts."
    )

client_id, client_secret = load_credentials()

if not client_id or not client_secret:
    raise RuntimeError(
        "Warcraft Logs API credentials were not found.\n\n"
        "Set WCL_CLIENT_ID and WCL_CLIENT_SECRET as "
        "environment variables, or place the existing "
        "Wow Analytics.py API script in the project folder."
    )

TOKEN_URL = (
    "https://www.warcraftlogs.com/oauth/token"
)

API_URL = (
    "https://www.warcraftlogs.com/api/v2/client"
)

token_response = requests.post(
    TOKEN_URL,
    auth=(
        client_id,
        client_secret
    ),
    data={
        "grant_type":
            "client_credentials"
    },
    timeout=60
)

if token_response.status_code != 200:
    raise RuntimeError(
        "Warcraft Logs authentication failed:\n"
        + token_response.text
    )

access_token = token_response.json()[
    "access_token"
]

headers = {
    "Authorization":
        f"Bearer {access_token}",
    "Content-Type":
        "application/json",
}


query = """
query($code: String!, $fightIDs: [Int!]) {
    reportData {
        report(code: $code) {
            code
            fights(fightIDs: $fightIDs) {
                id
                name
                kill
                fightPercentage
                bossPercentage
                difficulty
                size
            }
        }
    }
}
"""


fights_by_report = defaultdict(list)

for row in fights:

    fights_by_report[
        str(row.get("report_code", ""))
    ].append(
        safe_int(
            row.get("fight_id")
        )
    )


api_fights_found = {}

for report, fight_ids in fights_by_report.items():

    if not report:
        continue

    variables = {
        "code": report,
        "fightIDs": fight_ids,
    }

    response = requests.post(
        API_URL,
        headers=headers,
        json={
            "query": query,
            "variables": variables,
        },
        timeout=60
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"Warcraft Logs API HTTP error for "
            f"{report}: {response.text}"
        )

    payload = response.json()

    if payload.get("errors"):
        raise RuntimeError(
            f"Warcraft Logs API GraphQL error for "
            f"{report}: {payload['errors']}"
        )

    report_data = (
        payload
        .get("data", {})
        .get("reportData", {})
        .get("report")
    )

    if not report_data:
        raise RuntimeError(
            f"No report data returned for {report}."
        )

    returned_fights = report_data.get(
        "fights",
        []
    )

    for fight in returned_fights:

        if not isinstance(
            fight,
            dict
        ):
            continue

        fight_id = safe_int(
            fight.get("id")
        )

        api_fights_found[
            (
                report,
                str(fight_id)
            )
        ] = fight


print(
    f"API fight records returned: "
    f"{len(api_fights_found):,}"
)

if len(api_fights_found) != EXPECTED_FIGHTS:
    missing = []

    for row in fights:

        key = (
            str(row.get("report_code", "")),
            str(row.get("fight_id", ""))
        )

        if key not in api_fights_found:
            missing.append(key)

    raise RuntimeError(
        "Warcraft Logs did not return all 205 fights.\n"
        f"Missing records: {missing[:20]}"
    )


# ============================================================
# 6. APPLY FIGHT/FIGHT PERCENTAGES
# ============================================================

for row in fights:

    key = (
        str(row.get("report_code", "")),
        str(row.get("fight_id", ""))
    )

    api_fight = api_fights_found[key]

    # Preserve the raw Warcraft Logs values.
    row["fight_percentage"] = (
        api_fight.get(
            "fightPercentage"
        )
    )

    row["boss_percentage"] = (
        api_fight.get(
            "bossPercentage"
        )
    )

    # Keep the existing fight metadata, but refresh these
    # directly from the authoritative fight object.
    if api_fight.get("difficulty") is not None:
        row["difficulty"] = (
            api_fight.get("difficulty")
        )

    if api_fight.get("size") is not None:
        row["raid_size"] = (
            api_fight.get("size")
        )


# Propagate fight-level fields to player/fight master.
for row in players:

    key = (
        str(row.get("report_code", "")),
        str(row.get("fight_id", ""))
    )

    fight = next(
        (
            f
            for f in fights
            if (
                str(f.get("report_code", "")),
                str(f.get("fight_id", ""))
            ) == key
        ),
        None
    )

    if not fight:
        continue

    row["fight_percentage"] = (
        fight.get("fight_percentage")
    )

    row["boss_percentage"] = (
        fight.get("boss_percentage")
    )

    row["difficulty"] = (
        fight.get("difficulty")
    )

    row["raid_size"] = (
        fight.get("raid_size")
    )


# ============================================================
# 7. VALIDATE WIPE PROGRESS
# ============================================================

wipe_rows = [
    row
    for row in fights
    if str(
        row.get("fight_result", "")
    ).upper() == "WIPE"
    or str(
        row.get("kill", "")
    ).lower() in {
        "false",
        "0",
    }
]

missing_wipe_progress = [
    row
    for row in wipe_rows
    if row.get("boss_percentage") is None
    and row.get("fight_percentage") is None
]

print()
print("=" * 70)
print("WIPE PROGRESS VALIDATION")
print("=" * 70)

print(
    f"Total raid fights: {len(fights):,}"
)
print(
    f"Wipe fights:       {len(wipe_rows):,}"
)
print(
    f"Missing wipe %:     {len(missing_wipe_progress):,}"
)

if missing_wipe_progress:
    print(
        "WARNING: Some wipe fights do not have a "
        "fightPercentage/bossPercentage value from Warcraft Logs."
    )

# This is acceptable if WCL itself returns null for a fight.
# What we must NOT do is fabricate a value.
else:
    print(
        "All wipe fights have Warcraft Logs percentage data."
    )


# ============================================================
# 8. WRITE OUTPUTS
# ============================================================

write_csv(
    OUT_PLAYER,
    players
)

write_csv(
    OUT_FIGHTS,
    fights
)

write_csv(
    OUT_INTERRUPTS,
    interrupt_rows
)

write_csv(
    OUT_DISPELS,
    dispel_rows
)


# ============================================================
# FINAL VALIDATION
# ============================================================

print()
print("=" * 70)
print("FINAL PATCH VALIDATION")
print("=" * 70)

print(
    f"Raid fights:             {len(fights):,}"
)

print(
    f"Player/fight rows:       {len(players):,}"
)

print(
    f"Interrupt detail rows:   {len(interrupt_rows):,}"
)

print(
    f"Interrupt detail total:  {detail_interrupt_total:,}"
)

print(
    f"Dispel detail rows:      {len(dispel_rows):,}"
)

print(
    f"Dispel detail total:     {detail_dispel_total:,}"
)

print(
    f"Wipe rows:               {len(wipe_rows):,}"
)

print(
    f"Wipe rows missing %:     {len(missing_wipe_progress):,}"
)

print()
print("FILES CREATED:")
print(
    f"  {OUT_PLAYER}"
)
print(
    f"  {OUT_FIGHTS}"
)
print(
    f"  {OUT_INTERRUPTS}"
)
print(
    f"  {OUT_DISPELS}"
)

print()
print("ORIGINAL COMPLETE FILES WERE NOT MODIFIED.")

print()
print("=" * 70)
print("FINAL UTILITY + WIPE PROGRESS PATCH COMPLETE")
print("=" * 70)
