import os

import csv
import json
import re
from pathlib import Path
from collections import defaultdict

# ============================================================
# KRONOS INTELLIGENCE
# WORLD OF WARCRAFT RAID ANALYTICS
# FINAL UTILITY DATA FIX
#
# FIXED RAW STRUCTURE:
#   data
#     -> entries
#        -> entries
#           -> details
#
# The previous patch searched for obj["player"], but the raw
# Warcraft Logs records use the player directly as:
#   {"name": "...", "id": ..., "total": ...}
#
# This script therefore explicitly follows the verified nested
# structure instead of recursively guessing the structure.
# ============================================================

BASE = Path(os.getenv("WOW_RAID_ANALYTICS_BASE", Path.cwd()))
MASTER = BASE / "Wow_Analytics_Master_copies"
RAW = BASE / "detailed_raw"

PLAYER_MASTER = MASTER / "player_fight_master.csv"
FIGHT_MASTER = MASTER / "fight_inventory_master.csv"

OUT_PLAYER = MASTER / "player_fight_master_FINAL.csv"
OUT_FIGHTS = MASTER / "fight_inventory_master_FINAL.csv"
OUT_INTERRUPTS = MASTER / "player_interrupt_events_FINAL.csv"
OUT_DISPELS = MASTER / "player_dispel_events_FINAL.csv"


def load_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows):
    if not rows:
        print(f"WARNING: No rows to write: {path}")
        return

    fields = []
    seen = set()

    for row in rows:
        for key in row:
            if key not in seen:
                seen.add(key)
                fields.append(key)

    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=fields,
            extrasaction="ignore"
        )
        writer.writeheader()
        writer.writerows(rows)


def safe_int(value):
    try:
        return int(float(value or 0))
    except (TypeError, ValueError):
        return 0


def norm(value):
    return str(value or "").strip().lower()


def corrected_role(row):
    current = str(row.get("role", "") or "").strip()
    spec = norm(row.get("spec"))

    if current.lower() in {"tank", "healer", "dps"}:
        return current

    if spec in {"beastmastery", "beast mastery", "devourer"}:
        return "DPS"

    if spec == "holy":
        return "Healer"

    if spec in {
        "restoration",
        "restoration shaman",
        "restoration druid",
        "mistweaver",
        "mistweaver monk",
        "discipline",
    }:
        return "Healer"

    return current


def load_json(path):
    try:
        with path.open("r", encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception as exc:
        print(f"WARNING: Could not read {path}: {exc}")
        return None


def get_nested_spell_records(data):
    """
    Verified Warcraft Logs structure:

    root.data.entries[0].entries

    The first list contains wrapper records; the second list
    contains the actual interrupted/dispelled spell records.
    """
    if not isinstance(data, dict):
        return []

    root_data = data.get("data")
    if not isinstance(root_data, dict):
        return []

    outer_entries = root_data.get("entries")
    if not isinstance(outer_entries, list):
        return []

    records = []

    for outer in outer_entries:
        if not isinstance(outer, dict):
            continue

        nested = outer.get("entries")

        if isinstance(nested, list):
            for spell_record in nested:
                if isinstance(spell_record, dict):
                    records.append(spell_record)

    return records


def get_fight_id_from_path(path):
    """
    detailed_raw files use the verified naming convention:

        fight_<NUMBER>_Interrupts.json
        fight_<NUMBER>_Dispels.json

    The fight ID is in the filename, not a directory named fight_<NUMBER>.
    """
    match = re.match(
        r"fight_(\d+)_",
        path.name,
        flags=re.IGNORECASE
    )

    if match:
        return match.group(1)

    return ""


def get_report_code_from_path(path, report_codes):
    """
    The verified detailed_raw structure stores each report's raw files
    beneath a report-code directory. Use the immediate parent first,
    then fall back to searching the path.
    """
    parent = path.parent.name

    if parent in report_codes:
        return parent

    lower_map = {norm(x): x for x in report_codes}

    if norm(parent) in lower_map:
        return lower_map[norm(parent)]

    for part in path.parts:
        if part in report_codes:
            return part

    for part in path.parts:
        if norm(part) in lower_map:
            return lower_map[norm(part)]

    return ""


def find_utility_files(keyword):
    return sorted(
        p for p in RAW.rglob("*.json")
        if keyword.lower() in p.name.lower()
    )


print("=" * 70)
print("KRONOS INTELLIGENCE")
print("WORLD OF WARCRAFT RAID ANALYTICS")
print("FINAL NESTED INTERRUPT / DISPEL FIX")
print("=" * 70)

MASTER.mkdir(parents=True, exist_ok=True)

players = load_csv(PLAYER_MASTER)
fights = load_csv(FIGHT_MASTER)

print(f"\nPlayer/fight master rows: {len(players):,}")
print(f"Fight inventory rows:     {len(fights):,}")

if len(fights) != 205:
    raise RuntimeError(
        f"Expected 205 raid fights, found {len(fights)}. "
        "Stopping before writing final files."
    )

# ------------------------------------------------------------
# ROLE FIX
# ------------------------------------------------------------

blank_before = sum(
    1 for row in players
    if not str(row.get("role", "") or "").strip()
)

for row in players:
    row["role"] = corrected_role(row)

blank_after = sum(
    1 for row in players
    if not str(row.get("role", "") or "").strip()
)

print("\nROLE CORRECTION")
print(f"Blank roles before: {blank_before:,}")
print(f"Blank roles after:  {blank_after:,}")

# ------------------------------------------------------------
# ATTEMPT NUMBER
# ------------------------------------------------------------

def fight_sort_key(row):
    return (
        row.get("report_date", ""),
        row.get("fight_start_timestamp", ""),
        safe_int(row.get("fight_id"))
    )


groups = defaultdict(list)

for fight in fights:
    key = (
        fight.get("report_code", ""),
        fight.get("encounter_id", ""),
        fight.get("fight_name", "")
    )
    groups[key].append(fight)

for group in groups.values():
    group.sort(key=fight_sort_key)

    for attempt, fight in enumerate(group, start=1):
        fight["attempt_number"] = attempt


fight_lookup = {
    (
        row.get("report_code", ""),
        str(row.get("fight_id", ""))
    ): row
    for row in fights
}

for row in players:
    key = (
        row.get("report_code", ""),
        str(row.get("fight_id", ""))
    )

    fight = fight_lookup.get(key)

    row["attempt_number"] = (
        fight.get("attempt_number", "")
        if fight
        else ""
    )

# ------------------------------------------------------------
# RAW FILE DISCOVERY
# ------------------------------------------------------------

interrupt_files = find_utility_files("interrupts")
dispel_files = find_utility_files("dispels")

print("\nRAW UTILITY FILES")
print(f"Interrupt files found: {len(interrupt_files):,}")
print(f"Dispel files found:    {len(dispel_files):,}")

if not interrupt_files:
    raise RuntimeError("No interrupt JSON files found.")

if not dispel_files:
    raise RuntimeError("No dispel JSON files found.")

report_codes = {
    str(row.get("report_code", ""))
    for row in fights
    if row.get("report_code")
}

if interrupt_files:
    sample = interrupt_files[0]
    print("\nInterrupt mapping sample:")
    print(f"  File:        {sample.name}")
    print(f"  Report code: {get_report_code_from_path(sample, report_codes)}")
    print(f"  Fight ID:    {get_fight_id_from_path(sample)}")

if dispel_files:
    sample = dispel_files[0]
    print("\nDispel mapping sample:")
    print(f"  File:        {sample.name}")
    print(f"  Report code: {get_report_code_from_path(sample, report_codes)}")
    print(f"  Fight ID:    {get_fight_id_from_path(sample)}")

# ------------------------------------------------------------
# PLAYER MASTER LOOKUPS
# ------------------------------------------------------------

player_rows_by_key = {}

for row in players:
    key = (
        str(row.get("report_code", "")),
        str(row.get("fight_id", "")),
        str(row.get("player_id", "")),
        norm(row.get("player_name"))
    )

    player_rows_by_key[key] = row


# Also create a fallback lookup by report/fight/name.
player_rows_by_name = {}

for row in players:
    key = (
        str(row.get("report_code", "")),
        str(row.get("fight_id", "")),
        norm(row.get("player_name"))
    )

    player_rows_by_name[key] = row


# ------------------------------------------------------------
# PROCESS INTERRUPTS
# ------------------------------------------------------------

interrupt_totals = defaultdict(int)
interrupt_details = []

interrupt_files_with_records = 0
interrupt_player_records = 0

for path in interrupt_files:

    data = load_json(path)

    if data is None:
        continue

    spell_records = get_nested_spell_records(data)

    if not spell_records:
        continue

    report_code = get_report_code_from_path(
        path,
        report_codes
    )

    fight_id = get_fight_id_from_path(path)

    # Only process the 205 raid fights represented in our
    # authoritative fight inventory.
    if not fight_id:
        continue

    fight_key = (report_code, str(fight_id))

    if fight_key not in fight_lookup:
        continue

    interrupt_files_with_records += 1

    for spell in spell_records:

        interrupted_ability = str(
            spell.get("name", "") or ""
        )

        details = spell.get("details")

        if not isinstance(details, list):
            continue

        for player in details:

            if not isinstance(player, dict):
                continue

            player_name = str(
                player.get("name", "") or ""
            )

            if not player_name:
                continue

            player_id = str(
                player.get("id", "") or ""
            )

            count = safe_int(
                player.get("total")
            )

            if count <= 0:
                continue

            interrupt_player_records += 1

            key = (
                report_code,
                str(fight_id),
                player_id,
                norm(player_name)
            )

            # Use ID + name when available.
            if key in player_rows_by_key:
                interrupt_totals[key] += count
            else:
                # Fall back to report/fight/name.
                name_key = (
                    report_code,
                    str(fight_id),
                    norm(player_name)
                )

                interrupt_totals[name_key] += count

            abilities = player.get("abilities")

            if isinstance(abilities, list):
                for ability in abilities:

                    if not isinstance(ability, dict):
                        continue

                    ability_name = str(
                        ability.get("name", "") or ""
                    )

                    ability_count = safe_int(
                        ability.get("total")
                    )

                    if ability_count <= 0:
                        continue

                    interrupt_details.append({
                        "report_code": report_code,
                        "fight_id": fight_id,
                        "player_id": player_id,
                        "player_name": player_name,
                        "interrupted_ability": interrupted_ability,
                        "interrupting_ability": ability_name,
                        "count": ability_count
                    })


# ------------------------------------------------------------
# PROCESS DISPELS
# ------------------------------------------------------------

dispel_totals = defaultdict(int)
dispel_details = []

dispel_files_with_records = 0
dispel_player_records = 0

for path in dispel_files:

    data = load_json(path)

    if data is None:
        continue

    spell_records = get_nested_spell_records(data)

    if not spell_records:
        continue

    report_code = get_report_code_from_path(
        path,
        report_codes
    )

    fight_id = get_fight_id_from_path(path)

    if not fight_id:
        continue

    fight_key = (report_code, str(fight_id))

    if fight_key not in fight_lookup:
        continue

    dispel_files_with_records += 1

    for spell in spell_records:

        dispelled_ability = str(
            spell.get("name", "") or ""
        )

        details = spell.get("details")

        if not isinstance(details, list):
            continue

        for player in details:

            if not isinstance(player, dict):
                continue

            player_name = str(
                player.get("name", "") or ""
            )

            if not player_name:
                continue

            player_id = str(
                player.get("id", "") or ""
            )

            count = safe_int(
                player.get("total")
            )

            if count <= 0:
                continue

            dispel_player_records += 1

            key = (
                report_code,
                str(fight_id),
                player_id,
                norm(player_name)
            )

            if key in player_rows_by_key:
                dispel_totals[key] += count
            else:
                name_key = (
                    report_code,
                    str(fight_id),
                    norm(player_name)
                )

                dispel_totals[name_key] += count

            abilities = player.get("abilities")

            if isinstance(abilities, list):
                for ability in abilities:

                    if not isinstance(ability, dict):
                        continue

                    ability_name = str(
                        ability.get("name", "") or ""
                    )

                    ability_count = safe_int(
                        ability.get("total")
                    )

                    if ability_count <= 0:
                        continue

                    dispel_details.append({
                        "report_code": report_code,
                        "fight_id": fight_id,
                        "player_id": player_id,
                        "player_name": player_name,
                        "dispelled_ability": dispelled_ability,
                        "dispelling_ability": ability_name,
                        "count": ability_count
                    })


# ------------------------------------------------------------
# APPLY COUNTS TO PLAYER MASTER
# ------------------------------------------------------------

for row in players:

    report = str(row.get("report_code", ""))
    fight = str(row.get("fight_id", ""))
    pid = str(row.get("player_id", ""))
    name = norm(row.get("player_name"))

    exact_key = (
        report,
        fight,
        pid,
        name
    )

    name_key = (
        report,
        fight,
        name
    )

    row["interrupt_count"] = (
        interrupt_totals.get(
            exact_key,
            interrupt_totals.get(name_key, 0)
        )
    )

    row["dispel_count"] = (
        dispel_totals.get(
            exact_key,
            dispel_totals.get(name_key, 0)
        )
    )


# ------------------------------------------------------------
# VALIDATION
# ------------------------------------------------------------

total_interrupts = sum(
    safe_int(row.get("interrupt_count"))
    for row in players
)

total_dispels = sum(
    safe_int(row.get("dispel_count"))
    for row in players
)

players_with_interrupts = sum(
    1
    for row in players
    if safe_int(row.get("interrupt_count")) > 0
)

players_with_dispels = sum(
    1
    for row in players
    if safe_int(row.get("dispel_count")) > 0
)

print("\n" + "=" * 70)
print("UTILITY VALIDATION")
print("=" * 70)

print(f"Interrupt files with usable records: {interrupt_files_with_records:,}")
print(f"Interrupt player records found:      {interrupt_player_records:,}")
print(f"Total interrupts:                    {total_interrupts:,}")
print(f"Players with interrupts:             {players_with_interrupts:,}")

print()

print(f"Dispel files with usable records:    {dispel_files_with_records:,}")
print(f"Dispel player records found:         {dispel_player_records:,}")
print(f"Total dispels:                       {total_dispels:,}")
print(f"Players with dispels:                {players_with_dispels:,}")

print()

if total_interrupts == 0:
    raise RuntimeError(
        "Interrupt extraction is still zero. "
        "Stopping rather than producing another false final file."
    )

if total_dispels == 0:
    raise RuntimeError(
        "Dispel extraction is still zero. "
        "Stopping rather than producing another false final file."
    )

# ------------------------------------------------------------
# DEDUPE DETAIL TABLES
# ------------------------------------------------------------

def dedupe(rows):
    seen = set()
    output = []

    for row in rows:
        key = tuple(sorted(row.items()))

        if key not in seen:
            seen.add(key)
            output.append(row)

    return output


interrupt_details = dedupe(interrupt_details)
dispel_details = dedupe(dispel_details)

# ------------------------------------------------------------
# FINAL VALIDATION
# ------------------------------------------------------------

missing_attempts = sum(
    1
    for row in fights
    if not str(row.get("attempt_number", "") or "").strip()
)

missing_roles = sum(
    1
    for row in players
    if not str(row.get("role", "") or "").strip()
)

print("FINAL STRUCTURE VALIDATION")
print(f"Raid fights:           {len(fights):,}")
print(f"Player/fight rows:     {len(players):,}")
print(f"Blank roles:           {missing_roles:,}")
print(f"Missing attempt nums:  {missing_attempts:,}")
print(f"Interrupt detail rows: {len(interrupt_details):,}")
print(f"Dispel detail rows:    {len(dispel_details):,}")

if len(fights) != 205:
    raise RuntimeError("Final fight count is not 205.")

if missing_roles != 0:
    raise RuntimeError("Some roles are still blank.")

if missing_attempts != 0:
    raise RuntimeError("Some fights are missing attempt numbers.")

# ------------------------------------------------------------
# WRITE FINAL FILES
# ------------------------------------------------------------

write_csv(OUT_PLAYER, players)
write_csv(OUT_FIGHTS, fights)
write_csv(OUT_INTERRUPTS, interrupt_details)
write_csv(OUT_DISPELS, dispel_details)

print("\n" + "=" * 70)
print("FINAL NESTED UTILITY FIX COMPLETE")
print("=" * 70)

print("\nFILES CREATED:")
print(f"  {OUT_PLAYER}")
print(f"  {OUT_FIGHTS}")
print(f"  {OUT_INTERRUPTS}")
print(f"  {OUT_DISPELS}")

print("\nOriginal master CSVs were NOT modified.")
print("=" * 70)
