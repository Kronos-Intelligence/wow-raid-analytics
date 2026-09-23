import os

import csv
import json
import re
from pathlib import Path
from collections import defaultdict

# ============================================================
# KRONOS INTELLIGENCE
# WORLD OF WARCRAFT RAID ANALYTICS
#
# FINAL MASTER COMPLETION PASS
#
# PURPOSE
#   - Calculate HEALING RECEIVED from Healing target records.
#   - Add ACTIVE TIME to the final player/fight master.
#   - Calculate ACTIVE TIME % of fight duration.
#   - Preserve player_name as the cross-report longitudinal key.
#   - Preserve/refresh fight metadata where raw metadata provides it.
#   - Preserve existing interrupts, dispels, deaths, damage, etc.
#
# IMPORTANT
#   Warcraft Logs does NOT provide the exact player-level
#   "healing received" value we want as a direct field.
#
#   Instead:
#
#       healer record
#          -> targets[]
#             -> target player
#                -> total healing received
#
#   We aggregate target.total by TARGET PLAYER, not by healer.
#
#   This script never modifies the existing master files.
# ============================================================

BASE = Path(
    r"${WOW_RAID_ANALYTICS_BASE}"
)

MASTER = BASE / "Wow_Analytics_Master_copies"
RAW = BASE / "detailed_raw"

PLAYER_MASTER = MASTER / "player_fight_master_FINAL.csv"
FIGHT_MASTER = MASTER / "fight_inventory_master_FINAL.csv"

# If the FINAL files do not exist, fall back to the original masters.
if not PLAYER_MASTER.exists():
    PLAYER_MASTER = MASTER / "player_fight_master.csv"

if not FIGHT_MASTER.exists():
    FIGHT_MASTER = MASTER / "fight_inventory_master.csv"

OUT_PLAYER = MASTER / "player_fight_master_COMPLETE.csv"
OUT_FIGHTS = MASTER / "fight_inventory_master_COMPLETE.csv"
OUT_HEALING = MASTER / "player_healing_received_events_COMPLETE.csv"


EXPECTED_RAID_FIGHTS = 205

VALID_CLASSES = {
    "DeathKnight",
    "DemonHunter",
    "Druid",
    "Evoker",
    "Hunter",
    "Mage",
    "Monk",
    "Paladin",
    "Priest",
    "Rogue",
    "Shaman",
    "Warlock",
    "Warrior",
}

NON_PLAYER_TYPES = {
    "Pet",
    "NPC",
    "Boss",
    "Environment",
    "Object",
}


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
            f"Refusing to write an empty CSV: {path}"
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
    try:
        with path.open(
            "r",
            encoding="utf-8-sig"
        ) as f:
            return json.load(f)

    except Exception as error:
        print(
            f"WARNING: Could not read {path}: {error}"
        )
        return None


def safe_number(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def safe_int(value):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def norm(value):
    return str(value or "").strip().lower()


def fight_id_from_filename(filename):
    match = re.match(
        r"fight_(\d+)_",
        filename,
        flags=re.IGNORECASE
    )

    if match:
        return match.group(1)

    return ""


def report_code_from_path(path, report_codes):
    parent = path.parent.name

    if parent in report_codes:
        return parent

    lower_map = {
        norm(code): code
        for code in report_codes
    }

    if norm(parent) in lower_map:
        return lower_map[norm(parent)]

    for part in path.parts:
        if part in report_codes:
            return part

    for part in path.parts:
        if norm(part) in lower_map:
            return lower_map[norm(part)]

    return ""


def find_entries(data):
    """
    Handles the standard Warcraft Logs table structure:

        data
          -> entries

    Also tolerates the nested wrapper structure used by the
    interrupt/dispel exports.
    """

    if not isinstance(data, dict):
        return []

    root = data.get("data")

    if not isinstance(root, dict):
        return []

    entries = root.get("entries")

    if isinstance(entries, list):
        return entries

    return []


def is_player_target(target):
    """
    Healing target records include actual players and pets.
    We only want player characters for the player-level
    'healing received' metric.
    """

    if not isinstance(target, dict):
        return False

    name = target.get("name")

    if not name:
        return False

    target_type = str(
        target.get("type", "")
    ).strip()

    if target_type in NON_PLAYER_TYPES:
        return False

    if target_type in VALID_CLASSES:
        return True

    # Some exports may omit/alter the type. If a target has a
    # normal character name but no type, retain it rather than
    # silently losing legitimate healing.
    if not target_type:
        return True

    return False


def dedupe(rows):
    seen = set()
    output = []

    for row in rows:
        key = tuple(
            sorted(row.items())
        )

        if key not in seen:
            seen.add(key)
            output.append(row)

    return output


# ============================================================
# START
# ============================================================

print("=" * 70)
print("KRONOS INTELLIGENCE")
print("WORLD OF WARCRAFT RAID ANALYTICS")
print("FINAL MASTER COMPLETION PASS")
print("=" * 70)

MASTER.mkdir(
    parents=True,
    exist_ok=True
)

players = load_csv(PLAYER_MASTER)
fights = load_csv(FIGHT_MASTER)

print()
print(
    f"Player/fight master rows: {len(players):,}"
)
print(
    f"Fight inventory rows:     {len(fights):,}"
)

if len(fights) != EXPECTED_RAID_FIGHTS:
    raise RuntimeError(
        f"Expected {EXPECTED_RAID_FIGHTS} raid fights, "
        f"but found {len(fights)}. "
        "Stopping before creating final files."
    )


# ============================================================
# BUILD AUTHORITATIVE FIGHT LOOKUPS
# ============================================================

report_codes = {
    str(row.get("report_code", ""))
    for row in fights
    if row.get("report_code")
}

fight_lookup = {
    (
        str(row.get("report_code", "")),
        str(row.get("fight_id", ""))
    ): row
    for row in fights
}


# ============================================================
# ACTIVE TIME FROM DAMAGE DONE
# ============================================================

print()
print("=" * 70)
print("EXTRACTING ACTIVE TIME")
print("=" * 70)

damage_files = sorted(
    p
    for p in RAW.rglob("*_DamageDone.json")
)

print(
    f"DamageDone files found: {len(damage_files):,}"
)

active_time_lookup = defaultdict(float)

active_files_used = 0
active_player_records = 0

for path in damage_files:

    fight_id = fight_id_from_filename(
        path.name
    )

    if not fight_id:
        continue

    report_code = report_code_from_path(
        path,
        report_codes
    )

    fight_key = (
        report_code,
        str(fight_id)
    )

    if fight_key not in fight_lookup:
        continue

    data = load_json(path)

    if data is None:
        continue

    entries = find_entries(data)

    if not entries:
        continue

    active_files_used += 1

    for player in entries:

        if not isinstance(player, dict):
            continue

        name = str(
            player.get("name", "")
        ).strip()

        if not name:
            continue

        # Only recognized player records.
        if (
            player.get("type")
            and player.get("type") not in VALID_CLASSES
        ):
            continue

        active_time = safe_number(
            player.get("activeTime")
        )

        key = (
            report_code,
            str(fight_id),
            norm(name)
        )

        active_time_lookup[key] = active_time

        active_player_records += 1


print(
    f"DamageDone files used:   {active_files_used:,}"
)
print(
    f"Active-time player rows:  {active_player_records:,}"
)


# ============================================================
# CALCULATE ACTIVE TIME % ON PLAYER MASTER
# ============================================================

for row in players:

    report = str(
        row.get("report_code", "")
    )

    fight_id = str(
        row.get("fight_id", "")
    )

    name = norm(
        row.get("player_name")
    )

    key = (
        report,
        fight_id,
        name
    )

    active_ms = active_time_lookup.get(
        key,
        safe_number(
            row.get("active_time_ms")
        )
    )

    # Warcraft Logs activeTime is milliseconds.
    active_seconds = (
        active_ms / 1000.0
    )

    duration_seconds = safe_number(
        row.get("fight_duration_seconds")
    )

    if duration_seconds <= 0:
        # Try alternate column names if the current master
        # uses a slightly different naming convention.
        duration_seconds = safe_number(
            row.get("duration_seconds")
        )

    if duration_seconds > 0:
        active_percent = (
            active_seconds
            / duration_seconds
        ) * 100.0

        # Protect against malformed values.
        active_percent = max(
            0.0,
            min(
                active_percent,
                100.0
            )
        )

    else:
        active_percent = 0.0

    row["active_time_ms"] = round(
        active_ms,
        3
    )

    row["active_time_seconds"] = round(
        active_seconds,
        3
    )

    row["active_time_percent"] = round(
        active_percent,
        2
    )


# ============================================================
# HEALING RECEIVED
#
# RAW STRUCTURE:
#
#   Healing entry = healer
#       targets = [
#           {
#               name: target player,
#               total: healing amount,
#               type: player class
#           }
#       ]
#
# We aggregate target.total by TARGET PLAYER.
# ============================================================

print()
print("=" * 70)
print("CALCULATING HEALING RECEIVED FROM TARGET RECORDS")
print("=" * 70)

healing_files = sorted(
    p
    for p in RAW.rglob("*_Healing.json")
)

print(
    f"Healing files found: {len(healing_files):,}"
)

healing_received = defaultdict(float)

healing_detail_rows = []

healing_files_used = 0
healing_target_rows = 0
healing_player_targets = 0
healing_pet_targets_excluded = 0

for path in healing_files:

    fight_id = fight_id_from_filename(
        path.name
    )

    if not fight_id:
        continue

    report_code = report_code_from_path(
        path,
        report_codes
    )

    fight_key = (
        report_code,
        str(fight_id)
    )

    if fight_key not in fight_lookup:
        continue

    data = load_json(path)

    if data is None:
        continue

    entries = find_entries(data)

    if not entries:
        continue

    healing_files_used += 1

    for healer in entries:

        if not isinstance(healer, dict):
            continue

        healer_name = str(
            healer.get("name", "")
        ).strip()

        if not healer_name:
            continue

        targets = healer.get(
            "targets"
        )

        if not isinstance(
            targets,
            list
        ):
            continue

        for target in targets:

            if not isinstance(target, dict):
                continue

            healing_target_rows += 1

            target_name = str(
                target.get("name", "")
            ).strip()

            if not target_name:
                continue

            target_type = str(
                target.get("type", "")
            ).strip()

            if target_type in {
                "Pet",
                "NPC",
                "Boss",
                "Environment",
                "Object",
            }:
                healing_pet_targets_excluded += 1
                continue

            if not is_player_target(target):
                continue

            amount = safe_number(
                target.get("total")
            )

            if amount <= 0:
                continue

            healing_player_targets += 1

            key = (
                report_code,
                str(fight_id),
                norm(target_name)
            )

            healing_received[key] += amount

            healing_detail_rows.append({
                "report_code": report_code,
                "fight_id": fight_id,
                "recipient_player_name": target_name,
                "recipient_type": target_type,
                "healer_player_name": healer_name,
                "healing_received": round(
                    amount,
                    3
                )
            })


print(
    f"Healing files used:             {healing_files_used:,}"
)
print(
    f"Target records examined:        {healing_target_rows:,}"
)
print(
    f"Player target records used:     {healing_player_targets:,}"
)
print(
    f"Pet/NPC target records excluded:{healing_pet_targets_excluded:,}"
)


# ============================================================
# APPLY HEALING RECEIVED TO PLAYER MASTER
# ============================================================

for row in players:

    report = str(
        row.get("report_code", "")
    )

    fight_id = str(
        row.get("fight_id", "")
    )

    player_name = norm(
        row.get("player_name")
    )

    key = (
        report,
        fight_id,
        player_name
    )

    received = healing_received.get(
        key,
        0.0
    )

    duration_seconds = safe_number(
        row.get("fight_duration_seconds")
    )

    if duration_seconds <= 0:
        duration_seconds = safe_number(
            row.get("duration_seconds")
        )

    if duration_seconds > 0:
        received_per_second = (
            received
            / duration_seconds
        )

    else:
        received_per_second = 0.0

    row["healing_received"] = round(
        received,
        3
    )

    row["healing_received_per_second"] = round(
        received_per_second,
        3
    )


# ============================================================
# OPTIONAL RAW FIGHT METADATA REFRESH
#
# This does NOT overwrite existing values with blanks.
# If metadata contains boss/fight percentages or other fields,
# preserve them in the fight inventory.
# ============================================================

print()
print("=" * 70)
print("CHECKING RAW FIGHT METADATA")
print("=" * 70)

metadata_files = sorted(
    p
    for p in RAW.rglob("*_metadata.json")
)

metadata_used = 0
metadata_fields_found = set()

for path in metadata_files:

    fight_id = fight_id_from_filename(
        path.name
    )

    if not fight_id:
        continue

    report_code = report_code_from_path(
        path,
        report_codes
    )

    fight_key = (
        report_code,
        str(fight_id)
    )

    fight_row = fight_lookup.get(
        fight_key
    )

    if fight_row is None:
        continue

    data = load_json(path)

    if data is None:
        continue

    # Metadata exports can wrap the fight object several ways.
    candidate = None

    if isinstance(data, dict):

        root = data.get("data")

        if isinstance(root, dict):

            entries = root.get(
                "entries"
            )

            if isinstance(
                entries,
                list
            ) and entries:

                candidate = entries[0]

            elif isinstance(
                entries,
                dict
            ):

                candidate = entries

            elif any(
                key in root
                for key in (
                    "fightPercentage",
                    "bossPercentage",
                    "difficulty",
                    "raidSize",
                    "playerCount",
                )
            ):

                candidate = root

        if candidate is None:
            candidate = data

    if not isinstance(
        candidate,
        dict
    ):
        continue

    metadata_used += 1

    field_map = {
        "fightPercentage":
            "fight_percentage",

        "bossPercentage":
            "boss_percentage",

        "difficulty":
            "difficulty",

        "raidSize":
            "raid_size",

        "playerCount":
            "player_count",

        "fightName":
            "fight_name",

        "encounterID":
            "encounter_id",

        "encounterId":
            "encounter_id",
    }

    for raw_key, output_key in field_map.items():

        if raw_key not in candidate:
            continue

        value = candidate.get(
            raw_key
        )

        if value in (
            None,
            "",
            [],
            {}
        ):
            continue

        # Do not replace a good existing value with
        # an empty or null raw value.
        fight_row[output_key] = value
        metadata_fields_found.add(
            output_key
        )


print(
    f"Metadata files used: {metadata_used:,}"
)

print(
    "Metadata fields found: "
    + (
        ", ".join(
            sorted(metadata_fields_found)
        )
        if metadata_fields_found
        else "none"
    )
)


# ============================================================
# PROPAGATE FIGHT METADATA TO PLAYER MASTER
# ============================================================

for row in players:

    key = (
        str(row.get("report_code", "")),
        str(row.get("fight_id", ""))
    )

    fight = fight_lookup.get(
        key
    )

    if not fight:
        continue

    for field in (
        "fight_percentage",
        "boss_percentage",
        "difficulty",
        "raid_size",
        "player_count",
        "fight_name",
        "encounter_id",
    ):

        if field not in fight:
            continue

        value = fight.get(
            field
        )

        if value not in (
            None,
            "",
        ):
            row[field] = value


# ============================================================
# VALIDATION
# ============================================================

print()
print("=" * 70)
print("FINAL DATA VALIDATION")
print("=" * 70)

if len(fights) != EXPECTED_RAID_FIGHTS:
    raise RuntimeError(
        "Final fight count is not 205."
    )

blank_names = sum(
    1
    for row in players
    if not str(
        row.get("player_name", "")
    ).strip()
)

if blank_names:
    raise RuntimeError(
        f"{blank_names} player/fight rows have blank player names."
    )

total_healing_received = sum(
    safe_number(
        row.get("healing_received")
    )
    for row in players
)

players_with_healing_received = sum(
    1
    for row in players
    if safe_number(
        row.get("healing_received")
    ) > 0
)

avg_active = (
    sum(
        safe_number(
            row.get("active_time_percent")
        )
        for row in players
    )
    / len(players)
)

print(
    f"Raid fights:                    {len(fights):,}"
)
print(
    f"Player/fight rows:              {len(players):,}"
)
print(
    f"Total healing received:         {total_healing_received:,.0f}"
)
print(
    f"Player/fight rows with healing: {players_with_healing_received:,}"
)
print(
    f"Average active time %:          {avg_active:.2f}%"
)

if total_healing_received <= 0:
    raise RuntimeError(
        "Healing received is zero. "
        "Stopping rather than creating a false final dataset."
    )

if players_with_healing_received <= 0:
    raise RuntimeError(
        "No players have calculated healing received. "
        "Stopping rather than creating a false final dataset."
    )


# ============================================================
# CLEAN DETAIL TABLE
# ============================================================

healing_detail_rows = dedupe(
    healing_detail_rows
)

# ============================================================
# WRITE FINAL FILES
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
    OUT_HEALING,
    healing_detail_rows
)

print()
print("=" * 70)
print("MASTER DATA COMPLETION COMPLETE")
print("=" * 70)

print()
print("FILES CREATED:")

print(
    f"  {OUT_PLAYER}"
)

print(
    f"  {OUT_FIGHTS}"
)

print(
    f"  {OUT_HEALING}"
)

print()
print("ORIGINAL MASTER FILES WERE NOT MODIFIED.")

print()
print("HEALING LOGIC:")
print(
    "  Healing Done = healing performed by the healer."
)
print(
    "  Healing Received = sum of Healing target totals "
    "assigned to the recipient player."
)
print(
    "  Player Name is the longitudinal cross-report key."
)
print(
    "  Player ID is retained as source data only."
)

print()
print("=" * 70)
print("DONE")
print("=" * 70)
