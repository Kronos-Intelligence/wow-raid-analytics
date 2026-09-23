import os
import json
import re
import hashlib
import unicodedata
from collections import defaultdict
from pathlib import Path

import pandas as pd


# ============================================================
# KRONOS INTELLIGENCE
# WORLD OF WARCRAFT RAID ANALYTICS
#
# MASTER WARCRAFT LOGS EXTRACTION
#
# Scope:
#   23 reports
#   220 total fights
#   205 raid fights
#   15 non-raid fights excluded
#
# Outputs:
#   player_fight_master.csv
#   player_death_events.csv
#   player_ability_events.csv
#   fight_inventory_master.csv
#
# IMPORTANT:
#   detailed_raw is treated as READ ONLY.
# ============================================================


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(
    r"${WOW_RAID_ANALYTICS_BASE}"
)

RAW_DIR = BASE_DIR / "detailed_raw"

# Existing validated 205-raid-fight inventory.
# This keeps the master build aligned with the raid scope already
# established in the project.
V8_DIR = BASE_DIR / "raid_analytics_v8"
FIGHTS_FILE = V8_DIR / "raid_fights.csv"

# Existing fight inventory is used when available for exact
# fight-start timestamps needed for death timing.
FIGHT_INVENTORY_FILE = BASE_DIR / "fight_inventory.csv"

OUTPUT_DIR = (
    BASE_DIR / "Wow_Analytics_Master_copies"
)

PLAYER_FIGHT_OUTPUT = (
    OUTPUT_DIR / "player_fight_master.csv"
)

DEATH_OUTPUT = (
    OUTPUT_DIR / "player_death_events.csv"
)

ABILITY_OUTPUT = (
    OUTPUT_DIR / "player_ability_events.csv"
)

FIGHT_OUTPUT = (
    OUTPUT_DIR / "fight_inventory_master.csv"
)

EXPECTED_TOTAL_FIGHTS = 220
EXPECTED_RAID_FIGHTS = 205
EXPECTED_REPORTS = 23


# ============================================================
# ENTITY / CLASS CONSTANTS
# ============================================================

EXCLUDED_ENTITIES = {
    "Ezzorak",
    "War Chaplain Senn",
    "Environment",
}

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


# ============================================================
# SPEC -> ROLE MAP
# ============================================================

SPEC_ROLE_MAP = {
    "Blood": "Tank",
    "Frost": "DPS",
    "Unholy": "DPS",

    "Havoc": "DPS",
    "Vengeance": "Tank",

    "Balance": "DPS",
    "Feral": "DPS",
    "Guardian": "Tank",
    "Restoration": "Healer",

    "Devastation": "DPS",
    "Preservation": "Healer",
    "Augmentation": "DPS",

    "Beast Mastery": "DPS",
    "Marksmanship": "DPS",
    "Survival": "DPS",

    "Arcane": "DPS",
    "Fire": "DPS",
    "Frost Mage": "DPS",

    "Brewmaster": "Tank",
    "Mistweaver": "Healer",
    "Windwalker": "DPS",

    "Holy Paladin": "Healer",
    "Protection": "Tank",
    "Retribution": "DPS",

    "Discipline": "Healer",
    "Holy Priest": "Healer",
    "Shadow": "DPS",

    "Assassination": "DPS",
    "Outlaw": "DPS",
    "Subtlety": "DPS",

    "Elemental": "DPS",
    "Enhancement": "DPS",
    "Restoration Shaman": "Healer",

    "Affliction": "DPS",
    "Demonology": "DPS",
    "Destruction": "DPS",

    "Arms": "DPS",
    "Fury": "DPS",
    "Protection Warrior": "Tank",
}


# ============================================================
# HELPERS
# ============================================================

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def safe_float(value, default=0.0):
    if value is None:
        return default

    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_int(value, default=0):
    if value is None:
        return default

    try:
        return int(float(value))
    except (ValueError, TypeError):
        return default


def normalize_id(value):
    if value is None:
        return None
    return str(value)


def normalize_text(value):
    if value is None:
        return ""
    return str(value).strip()


def normalize_player_name(name):
    if name is None:
        return ""

    value = unicodedata.normalize(
        "NFKC",
        str(name)
    )

    value = " ".join(
        value.strip().split()
    )

    return value.casefold()


def build_stable_player_id(name):
    normalized = normalize_player_name(name)

    if not normalized:
        return None

    digest = hashlib.sha1(
        normalized.encode("utf-8")
    ).hexdigest()[:16]

    return f"P-{digest}"


def get_entries(data):
    """
    Handles the Warcraft Logs structures found in this project.

    Standard:
        data -> entries

    Also supports:
        entries

    And common nested activity form:
        data -> entries -> entries
    """

    if not isinstance(data, dict):
        return []

    root = data.get("data")

    if isinstance(root, dict):
        entries = root.get("entries")

        if isinstance(entries, list):
            return entries

    entries = data.get("entries")

    if isinstance(entries, list):
        return entries

    return []


def find_entries(data):
    """
    Same basic behavior as get_entries, retained as a separate
    function because some raw files use slightly different
    wrappers.
    """

    if not isinstance(data, dict):
        return []

    root = data.get("data")

    if isinstance(root, dict):
        entries = root.get("entries")

        if isinstance(entries, list):

            if (
                entries
                and isinstance(entries[0], dict)
                and "name" not in entries[0]
                and isinstance(entries[0].get("entries"), list)
            ):
                return entries[0]["entries"]

            return entries

    entries = data.get("entries")

    if isinstance(entries, list):
        return entries

    return []


def get_total(record):
    if not isinstance(record, dict):
        return 0.0

    for field in (
        "total",
        "totalAmount",
        "amount",
        "value",
    ):
        if field in record and record[field] is not None:
            return safe_float(record[field])

    return 0.0


def get_active_time(record):
    if not isinstance(record, dict):
        return 0.0

    for field in (
        "activeTime",
        "active_time",
        "active",
    ):
        if field in record and record[field] is not None:
            return safe_float(record[field])

    return 0.0


def get_class(record):
    if not isinstance(record, dict):
        return ""

    value = record.get("type")

    if value is None:
        return ""

    return str(value)


def get_spec(record):
    if not isinstance(record, dict):
        return ""

    for field in (
        "spec",
        "specName",
        "specialization",
        "specializationName",
    ):
        value = record.get(field)

        if isinstance(value, str) and value.strip():
            return value.strip()

        if isinstance(value, dict):
            for nested_field in (
                "name",
                "specName",
                "specializationName",
            ):
                nested = value.get(nested_field)

                if (
                    isinstance(nested, str)
                    and nested.strip()
                ):
                    return nested.strip()

    icon = record.get("icon")

    if isinstance(icon, str) and "-" in icon:
        _, suffix = icon.rsplit("-", 1)

        if suffix.strip():
            return suffix.strip()

    return ""


def normalize_spec(spec):
    if not spec:
        return ""

    value = " ".join(
        str(spec).strip().split()
    )

    aliases = {
        "Holy (Priest)": "Holy Priest",
        "Restoration (Shaman)": "Restoration Shaman",
        "Protection (Warrior)": "Protection Warrior",
    }

    return aliases.get(value, value)


def get_role_from_spec(spec):
    normalized = normalize_spec(spec)

    role = SPEC_ROLE_MAP.get(
        normalized,
        ""
    )

    # A few raw icons can expose a generic spec name where
    # the class is needed to disambiguate it.
    return role


def is_player_record(record):
    if not isinstance(record, dict):
        return False

    name = record.get("name")

    if not name:
        return False

    if name in EXCLUDED_ENTITIES:
        return False

    player_class = get_class(record)

    return player_class in VALID_CLASSES


def extract_fight_id(filename):
    match = re.match(
        r"fight_(\d+)_",
        filename
    )

    if match:
        return int(match.group(1))

    return None


def classify_file(filename):
    file_types = {
        "casts": "_Casts.json",
        "damage_done": "_DamageDone.json",
        "damage_taken": "_DamageTaken.json",
        "healing": "_Healing.json",
        "deaths": "_Deaths.json",
        "interrupts": "_Interrupts.json",
        "dispels": "_Dispels.json",
        "metadata": "_metadata.json",
    }

    for key, suffix in file_types.items():

        if filename.endswith(suffix):
            return key

    return None


def ensure_player(metrics, record):

    if not is_player_record(record):
        return None

    name = normalize_text(
        record.get("name")
    )

    key = normalize_player_name(name)

    if not key:
        return None

    player_id = build_stable_player_id(name)

    raw_id = normalize_id(
        record.get("id")
    )

    spec = normalize_spec(
        get_spec(record)
    )

    if key not in metrics:

        metrics[key] = {
            "player_name": name,
            "player_id": player_id,
            "warcraft_logs_source_id": raw_id,

            "class": get_class(record),
            "spec": spec,
            "role": get_role_from_spec(spec),

            "item_level": safe_float(
                record.get("itemLevel")
            ),

            "damage_done": 0.0,
            "damage_done_reduced": 0.0,
            "damage_active_time_ms": 0.0,

            "damage_taken": 0.0,
            "damage_taken_reduced": 0.0,
            "damage_taken_active_time_ms": 0.0,

            "healing_done": 0.0,
            "healing_done_reduced": 0.0,
            "overhealing": 0.0,
            "healing_active_time_ms": 0.0,

            "healing_received": 0.0,
            "healing_received_reduced": 0.0,

            "cast_count": 0,

            "death_count": 0,

            "interrupt_count": 0,
            "dispel_count": 0,
        }

    else:

        if (
            metrics[key]["warcraft_logs_source_id"] is None
            and raw_id is not None
        ):
            metrics[key][
                "warcraft_logs_source_id"
            ] = raw_id

        if not metrics[key]["class"]:
            metrics[key]["class"] = get_class(record)

        if not metrics[key]["spec"] and spec:
            metrics[key]["spec"] = spec

        if (
            not metrics[key]["role"]
            and metrics[key]["spec"]
        ):
            metrics[key]["role"] = (
                get_role_from_spec(
                    metrics[key]["spec"]
                )
            )

        if not metrics[key]["item_level"]:
            metrics[key]["item_level"] = safe_float(
                record.get("itemLevel")
            )

    return metrics[key]


def extract_ability_rows(
    report_code,
    fight_id,
    fight_name,
    player,
    source_dataset,
):
    """
    Convert aggregate ability arrays into a tidy player/fight/ability
    table. This is intentionally separate from the master table so
    the master CSV remains one row per player/fight.
    """

    rows = []

    if not isinstance(player, dict):
        return rows

    if not is_player_record(player):
        return rows

    player_name = normalize_text(
        player.get("name")
    )

    player_id = build_stable_player_id(
        player_name
    )

    abilities = player.get("abilities")

    if not isinstance(abilities, list):
        return rows

    for ability in abilities:

        if not isinstance(ability, dict):
            continue

        rows.append({
            "report_code": report_code,
            "fight_id": fight_id,
            "fight_name": fight_name,
            "player_name": player_name,
            "player_id": player_id,
            "source_dataset": source_dataset,

            "ability_id": normalize_id(
                ability.get("guid")
            ),

            "ability_name": normalize_text(
                ability.get("name")
            ),

            "ability_type": safe_int(
                ability.get("type"),
                default=None
            ),

            "count": safe_int(
                ability.get("total")
            ),

            "total_reduced": safe_float(
                ability.get("totalReduced")
            ),

            "overhealing": safe_float(
                ability.get("overheal")
            ),

            "pet_name": normalize_text(
                ability.get("petName")
            ),

            "icon": normalize_text(
                ability.get("icon")
            ),
        })

    return rows


def extract_healing_targets(player):
    """
    Return target-level healing from a healer's raw record.

    The raw Healing dataset exposes target records. The target
    total is summed into healing_received for the target player.

    The function deliberately accepts several possible target
    shapes
    so the extraction is resilient to small Warcraft Logs
    structural differences.
    """

    results = []

    if not isinstance(player, dict):
        return results

    targets = player.get("targets")

    if not isinstance(targets, list):
        return results

    for target in targets:

        if not isinstance(target, dict):
            continue

        target_name = (
            target.get("name")
            or target.get("targetName")
            or target.get("target")
        )

        if isinstance(target_name, dict):
            target_name = (
                target_name.get("name")
            )

        if not target_name:
            continue

        target_id = (
            target.get("id")
            or target.get("targetID")
        )

        total = get_total(target)

        total_reduced = safe_float(
            target.get("totalReduced")
        )

        results.append({
            "target_name": normalize_text(
                target_name
            ),
            "target_id": normalize_id(
                target_id
            ),
            "total": total,
            "total_reduced": total_reduced,
        })

    return results


def find_matching_killing_blow_event(
    death,
):
    """
    Try to find the event corresponding to the reported
    killingBlow so we can retain sourceID when available.
    """

    if not isinstance(death, dict):
        return None

    killing_blow = death.get(
        "killingBlow"
    )

    if not isinstance(killing_blow, dict):
        return None

    target_guid = killing_blow.get(
        "guid"
    )

    target_name = killing_blow.get(
        "name"
    )

    events = death.get("events")

    if not isinstance(events, list):
        return None

    candidates = []

    for event in events:

        if not isinstance(event, dict):
            continue

        ability = event.get(
            "ability"
        )

        if not isinstance(ability, dict):
            continue

        event_guid = ability.get(
            "guid"
        )

        event_name = ability.get(
            "name"
        )

        guid_match = (
            target_guid is not None
            and event_guid is not None
            and str(target_guid)
            == str(event_guid)
        )

        name_match = (
            target_name
            and event_name
            and str(target_name)
            == str(event_name)
        )

        if guid_match or name_match:
            candidates.append(event)

    if not candidates:
        return None

    # The event closest to the death timestamp is the best match.
    death_timestamp = safe_float(
        death.get("timestamp")
    )

    candidates.sort(
        key=lambda event: abs(
            safe_float(
                event.get("timestamp")
            )
            - death_timestamp
        )
    )

    return candidates[0]


def parse_start_timestamp(value):
    """
    Return epoch milliseconds when possible.

    Supports:
      - numeric epoch milliseconds
      - numeric epoch seconds
      - pandas/ISO timestamps
    """

    if value is None:
        return None

    if isinstance(value, (int, float)):
        number = float(value)

        if number > 10_000_000_000:
            return number

        if number > 1_000_000_000:
            return number * 1000

        return number

    text = str(value).strip()

    if not text:
        return None

    try:
        number = float(text)

        if number > 10_000_000_000:
            return number

        if number > 1_000_000_000:
            return number * 1000

    except ValueError:
        pass

    try:
        timestamp = pd.to_datetime(
            text,
            errors="coerce"
        )

        if pd.isna(timestamp):
            return None

        if timestamp.tzinfo is None:
            timestamp = timestamp.tz_localize(
                "UTC"
            )

        return timestamp.timestamp() * 1000

    except Exception:
        return None


# ============================================================
# START
# ============================================================

print("=" * 70)
print("KRONOS INTELLIGENCE")
print("WORLD OF WARCRAFT RAID ANALYTICS")
print("MASTER WARCRAFT LOGS EXTRACTION")
print("=" * 70)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

if not RAW_DIR.exists():
    raise FileNotFoundError(
        f"\nRaw data directory not found:\n{RAW_DIR}"
    )

if not FIGHTS_FILE.exists():
    raise FileNotFoundError(
        f"\nRaid fight inventory not found:\n{FIGHTS_FILE}"
    )


# ============================================================
# LOAD RAID FIGHTS
# ============================================================

print()
print("=" * 70)
print("LOADING RAID FIGHTS")
print("=" * 70)

raid_fights = pd.read_csv(
    FIGHTS_FILE
)

print(
    f"\nRaid fights loaded: "
    f"{len(raid_fights):,}"
)

required_columns = {
    "report_code",
    "fight_id",
    "fight_name",
    "encounter_id",
    "fight_result",
    "duration_seconds",
}

missing_columns = (
    required_columns
    - set(raid_fights.columns)
)

if missing_columns:
    raise ValueError(
        "\nMissing required columns from raid_fights.csv:\n"
        + "\n".join(
            sorted(missing_columns)
        )
    )

if len(raid_fights) != EXPECTED_RAID_FIGHTS:
    raise ValueError(
        f"\nExpected {EXPECTED_RAID_FIGHTS} raid fights "
        f"but found {len(raid_fights):,}."
    )

report_count = (
    raid_fights["report_code"]
    .astype(str)
    .nunique()
)

print(
    f"Reports represented: "
    f"{report_count:,}"
)

if report_count != EXPECTED_REPORTS:
    print(
        f"WARNING: Expected {EXPECTED_REPORTS} "
        f"reports but found {report_count:,}."
    )


# ============================================================
# OPTIONAL FIGHT-START TIMING LOOKUP
# ============================================================

fight_start_lookup = {}

if FIGHT_INVENTORY_FILE.exists():

    print()
    print("=" * 70)
    print("LOADING FIGHT START TIMING")
    print("=" * 70)

    inventory = pd.read_csv(
        FIGHT_INVENTORY_FILE
    )

    print(
        f"Fight inventory rows: "
        f"{len(inventory):,}"
    )

    start_column = None

    for candidate in (
        "fight_start_timestamp",
        "fight_start_time",
        "start_timestamp",
        "start_time",
    ):

        if candidate in inventory.columns:
            start_column = candidate
            break

    if start_column:

        for _, row in inventory.iterrows():

            key = (
                str(row.get("report_code")),
                safe_int(row.get("fight_id"))
            )

            start_ms = parse_start_timestamp(
                row.get(start_column)
            )

            if start_ms is not None:
                fight_start_lookup[key] = start_ms

        print(
            f"Fight timing records loaded: "
            f"{len(fight_start_lookup):,}"
        )
        print(
            f"Timing column: {start_column}"
        )

    else:

        print(
            "WARNING: No recognized fight-start "
            "timestamp column found."
        )

else:

    print()
    print(
        "WARNING: fight_inventory.csv not found."
    )

    print(
        "Death time in seconds will be calculated "
        "only when a fight-start timestamp is available."
    )


# ============================================================
# INDEX RAW JSON
# ============================================================

print()
print("=" * 70)
print("INDEXING RAW DETAILED DATA")
print("=" * 70)

raw_file_index = {}

json_files = list(
    RAW_DIR.rglob("*.json")
)

print(
    f"\nJSON files discovered: "
    f"{len(json_files):,}"
)

for path in json_files:

    fight_id = extract_fight_id(
        path.name
    )

    if fight_id is None:
        continue

    try:
        relative = path.relative_to(
            RAW_DIR
        )

        if len(relative.parts) < 2:
            continue

        report_code = relative.parts[0]

    except ValueError:
        continue

    file_type = classify_file(
        path.name
    )

    if file_type is None:
        continue

    key = (
        str(report_code),
        fight_id
    )

    raw_file_index.setdefault(
        key,
        {}
    )[file_type] = path

print(
    f"Report/fight combinations indexed: "
    f"{len(raw_file_index):,}"
)


# ============================================================
# RAW COVERAGE VALIDATION
# ============================================================

print()
print("=" * 70)
print("VALIDATING RAW COVERAGE")
print("=" * 70)

missing_fights = []
incomplete_fights = []

expected_datasets = {
    "casts",
    "damage_done",
    "damage_taken",
    "healing",
    "deaths",
    "interrupts",
    "dispels",
    "metadata",
}

for _, fight in raid_fights.iterrows():

    key = (
        str(fight["report_code"]),
        safe_int(fight["fight_id"])
    )

    if key not in raw_file_index:

        missing_fights.append(key)
        continue

    missing_types = (
        expected_datasets
        - set(raw_file_index[key].keys())
    )

    if missing_types:

        incomplete_fights.append(
            (
                key,
                sorted(missing_types)
            )
        )

print(
    f"Raid fights requested: "
    f"{len(raid_fights):,}"
)

print(
    f"Raid fights with raw data: "
    f"{len(raid_fights) - len(missing_fights):,}"
)

print(
    f"Raid fights missing entirely: "
    f"{len(missing_fights):,}"
)

print(
    f"Raid fights with missing dataset types: "
    f"{len(incomplete_fights):,}"
)

if missing_fights:

    print("\nMissing raid fights:")

    for report_code, fight_id in missing_fights:
        print(
            f" - {report_code} / Fight {fight_id}"
        )

    raise RuntimeError(
        "\nRaw coverage is incomplete. "
        "No output CSVs were written."
    )

if incomplete_fights:

    print("\nIncomplete raid fights:")

    for (
        report_code_fight,
        missing_types,
    ) in incomplete_fights[:50]:

        print(
            f" - {report_code_fight}: "
            f"{', '.join(missing_types)}"
        )

    raise RuntimeError(
        "\nAt least one raid fight is missing "
        "one or more expected raw datasets. "
        "No output CSVs were written."
    )


# ============================================================
# OUTPUT COLLECTIONS
# ============================================================

player_records = []
death_records = []
ability_records = []
fight_records = []

processed_fights = 0


# ============================================================
# PROCESS ALL 205 RAID FIGHTS
# ============================================================

print()
print("=" * 70)
print("PROCESSING 205 RAID FIGHTS")
print("=" * 70)

for _, fight in raid_fights.iterrows():

    report_code = str(
        fight["report_code"]
    )

    fight_id = safe_int(
        fight["fight_id"]
    )

    fight_name = normalize_text(
        fight["fight_name"]
    )

    encounter_id = safe_int(
        fight["encounter_id"],
        default=None
    )

    fight_result = normalize_text(
        fight["fight_result"]
    )

    duration_seconds = safe_float(
        fight["duration_seconds"]
    )

    key = (
        report_code,
        fight_id
    )

    raw_files = raw_file_index[key]

    processed_fights += 1

    print(
        f"[{processed_fights:03}/{EXPECTED_RAID_FIGHTS:03}] "
        f"{report_code} | Fight {fight_id} | "
        f"{fight_name}"
    )

    # --------------------------------------------------------
    # FIGHT MASTER RECORD
    # --------------------------------------------------------

    fight_records.append({
        "report_code": report_code,
        "fight_id": fight_id,
        "fight_name": fight_name,
        "encounter_id": encounter_id,
        "fight_result": fight_result,
        "duration_seconds": duration_seconds,

        "report_date": (
            fight.get("report_date")
            if "report_date" in fight.index
            else ""
        ),

        "difficulty": (
            fight.get("difficulty")
            if "difficulty" in fight.index
            else ""
        ),

        "raid_size": (
            fight.get("raid_size")
            if "raid_size" in fight.index
            else ""
        ),

        "player_count": (
            fight.get("player_count")
            if "player_count" in fight.index
            else ""
        ),

        "fight_start_timestamp": (
            fight_start_lookup.get(key)
        ),
    })

    # --------------------------------------------------------
    # PLAYER METRICS
    # --------------------------------------------------------

    metrics = {}

    # --------------------------------------------------------
    # DAMAGE DONE
    # --------------------------------------------------------

    data = load_json(
        raw_files["damage_done"]
    )

    for player in find_entries(data):

        p = ensure_player(
            metrics,
            player
        )

        if p is None:
            continue

        p["damage_done"] = get_total(
            player
        )

        p["damage_done_reduced"] = safe_float(
            player.get("totalReduced")
        )

        p["damage_active_time_ms"] = (
            get_active_time(player)
        )

        ability_records.extend(
            extract_ability_rows(
                report_code,
                fight_id,
                fight_name,
                player,
                "DamageDone"
            )
        )

    # --------------------------------------------------------
    # DAMAGE TAKEN
    # --------------------------------------------------------

    data = load_json(
        raw_files["damage_taken"]
    )

    for player in find_entries(data):

        p = ensure_player(
            metrics,
            player
        )

        if p is None:
            continue

        p["damage_taken"] = get_total(
            player
        )

        p["damage_taken_reduced"] = safe_float(
            player.get("totalReduced")
        )

        p["damage_taken_active_time_ms"] = (
            get_active_time(player)
        )

        ability_records.extend(
            extract_ability_rows(
                report_code,
                fight_id,
                fight_name,
                player,
                "DamageTaken"
            )
        )

    # --------------------------------------------------------
    # HEALING DONE + HEALING RECEIVED
    # --------------------------------------------------------

    data = load_json(
        raw_files["healing"]
    )

    for player in find_entries(data):

        p = ensure_player(
            metrics,
            player
        )

        if p is None:
            continue

        p["healing_done"] = get_total(
            player
        )

        p["healing_done_reduced"] = safe_float(
            player.get("totalReduced")
        )

        p["overhealing"] = safe_float(
            player.get("overheal")
        )

        p["healing_active_time_ms"] = (
            get_active_time(player)
        )

        ability_records.extend(
            extract_ability_rows(
                report_code,
                fight_id,
                fight_name,
                player,
                "Healing"
            )
        )

        for target in extract_healing_targets(
            player
        ):

            target_name = target[
                "target_name"
            ]

            target_key = normalize_player_name(
                target_name
            )

            # Only count actual player targets.
            # If the target is not present in our player
            # metrics yet, it will be created here only if
            # the target has a recognizable player-like name.
            if target_key in EXCLUDED_ENTITIES:
                continue

            # Match against known players by normalized name.
            # We deliberately do not invent class/spec from a
            # healing target record.
            if target_key in metrics:

                metrics[target_key][
                    "healing_received"
                ] += target["total"]

                metrics[target_key][
                    "healing_received_reduced"
                ] += target["total_reduced"]

    # --------------------------------------------------------
    # DEATHS
    # --------------------------------------------------------

    data = load_json(
        raw_files["deaths"]
    )

    death_entries = find_entries(data)

    for death in death_entries:

        if not is_player_record(death):
            continue

        p = ensure_player(
            metrics,
            death
        )

        if p is None:
            continue

        p["death_count"] += 1

        player_name = normalize_text(
            death.get("name")
        )

        player_id = build_stable_player_id(
            player_name
        )

        timestamp = safe_float(
            death.get("timestamp")
        )

        fight_start_ms = (
            fight_start_lookup.get(key)
        )

        death_time_seconds = None

        if (
            timestamp
            and fight_start_ms is not None
        ):

            death_time_seconds = (
                timestamp - fight_start_ms
            ) / 1000.0

        killing_blow = death.get(
            "killingBlow"
        )

        if not isinstance(
            killing_blow,
            dict
        ):
            killing_blow = {}

        matching_event = (
            find_matching_killing_blow_event(
                death
            )
        )

        death_records.append({

            "report_code":
                report_code,

            "fight_id":
                fight_id,

            "fight_name":
                fight_name,

            "encounter_id":
                encounter_id,

            "fight_result":
                fight_result,

            "duration_seconds":
                duration_seconds,

            "player_name":
                player_name,

            "player_id":
                player_id,

            "warcraft_logs_source_id":
                normalize_id(
                    death.get("id")
                ),

            "death_timestamp":
                timestamp,

            "death_time_seconds":
                death_time_seconds,

            "death_percent":
                (
                    death_time_seconds
                    / duration_seconds
                    * 100
                    if (
                        death_time_seconds is not None
                        and duration_seconds > 0
                    )
                    else None
                ),

            "death_damage":
                safe_float(
                    death.get("damage")
                ),

            "death_healing":
                safe_float(
                    death.get("healing")
                ),

            "death_overkill":
                safe_float(
                    death.get("overkill")
                ),

            "death_window":
                safe_float(
                    death.get("deathWindow")
                ),

            "killing_blow_name":
                normalize_text(
                    killing_blow.get("name")
                ),

            "killing_blow_guid":
                normalize_id(
                    killing_blow.get("guid")
                ),

            "killing_blow_type":
                safe_int(
                    killing_blow.get("type"),
                    default=None
                ),

            "killing_blow_icon":
                normalize_text(
                    killing_blow.get("abilityIcon")
                ),

            "killing_blow_source_id":
                (
                    normalize_id(
                        matching_event.get(
                            "sourceID"
                        )
                    )
                    if matching_event
                    else None
                ),

            "killing_blow_source_friendly":
                (
                    matching_event.get(
                        "sourceIsFriendly"
                    )
                    if matching_event
                    else None
                ),

            "killing_blow_amount":
                (
                    safe_float(
                        matching_event.get(
                            "amount"
                        )
                    )
                    if matching_event
                    else None
                ),

            "killing_blow_mitigated":
                (
                    safe_float(
                        matching_event.get(
                            "mitigated"
                        )
                    )
                    if matching_event
                    else None
                ),

            "killing_blow_unmitigated":
                (
                    safe_float(
                        matching_event.get(
                            "unmitigatedAmount"
                        )
                    )
                    if matching_event
                    else None
                ),

            "killing_blow_absorbed":
                (
                    safe_float(
                        matching_event.get(
                            "absorbed"
                        )
                    )
                    if matching_event
                    else None
                ),
        })

    # --------------------------------------------------------
    # INTERRUPTS
    # --------------------------------------------------------

    data = load_json(
        raw_files["interrupts"]
    )

    for player in find_entries(data):

        p = ensure_player(
            metrics,
            player
        )

        if p is None:
            continue

        value = player.get(
            "spellsInterrupted"
        )

        if value is None:
            value = player.get(
                "total"
            )

        p["interrupt_count"] += safe_int(
            value
        )

    # --------------------------------------------------------
    # DISPELS
    # --------------------------------------------------------

    data = load_json(
        raw_files["dispels"]
    )

    for player in find_entries(data):

        p = ensure_player(
            metrics,
            player
        )

        if p is None:
            continue

        value = player.get(
            "spellsCompleted"
        )

        if value is None:
            value = player.get(
                "total"
            )

        p["dispel_count"] += safe_int(
            value
        )

    # --------------------------------------------------------
    # CASTS
    # --------------------------------------------------------

    data = load_json(
        raw_files["casts"]
    )

    for player in find_entries(data):

        p = ensure_player(
            metrics,
            player
        )

        if p is None:
            continue

        cast_count = 0

        abilities = player.get(
            "abilities"
        )

        if isinstance(
            abilities,
            list
        ):

            for ability in abilities:

                if not isinstance(
                    ability,
                    dict
                ):
                    continue

                cast_count += safe_int(
                    ability.get("total")
                )

        if cast_count == 0:
            cast_count = safe_int(
                player.get("total")
            )

        p["cast_count"] = cast_count

        ability_records.extend(
            extract_ability_rows(
                report_code,
                fight_id,
                fight_name,
                player,
                "Casts"
            )
        )

    # --------------------------------------------------------
    # BUILD PLAYER x FIGHT ROWS
    # --------------------------------------------------------

    for p in metrics.values():

        duration = duration_seconds

        active_seconds = (
            p["active_time_ms"] / 1000.0
            if "active_time_ms" in p
            else 0.0
        )

        # Use DamageDone active time as the primary
        # activity measure because it directly describes
        # active combat output in the raw dataset.
        #
        # Cast active time is retained separately when
        # available below.
        damage_active_seconds = (
            p["damage_active_time_ms"]
            / 1000.0
        )

        damage_active_percent = (
            damage_active_seconds
            / duration
            * 100
            if duration > 0
            else None
        )

        damage_per_second = (
            p["damage_done"] / duration
            if duration > 0
            else 0.0
        )

        healing_per_second = (
            p["healing_done"] / duration
            if duration > 0
            else 0.0
        )

        healing_received_per_second = (
            p["healing_received"] / duration
            if duration > 0
            else 0.0
        )

        damage_taken_per_second = (
            p["damage_taken"] / duration
            if duration > 0
            else 0.0
        )

        casts_per_minute = (
            p["cast_count"]
            / (duration / 60.0)
            if duration > 0
            else 0.0
        )

        player_records.append({

            "report_code":
                report_code,

            "report_date":
                (
                    fight.get("report_date")
                    if "report_date"
                    in fight.index
                    else ""
                ),

            "fight_id":
                fight_id,

            "fight_name":
                fight_name,

            "encounter_id":
                encounter_id,

            "fight_result":
                fight_result,

            "duration_seconds":
                duration,

            "fight_start_timestamp":
                fight_start_lookup.get(
                    key
                ),

            "difficulty":
                (
                    fight.get("difficulty")
                    if "difficulty"
                    in fight.index
                    else ""
                ),

            "raid_size":
                (
                    fight.get("raid_size")
                    if "raid_size"
                    in fight.index
                    else ""
                ),

            "player_name":
                p["player_name"],

            "player_id":
                p["player_id"],

            "warcraft_logs_source_id":
                p["warcraft_logs_source_id"],

            "class":
                p["class"],

            "spec":
                p["spec"],

            "role":
                p["role"],

            "item_level":
                p["item_level"],

            "damage_done":
                p["damage_done"],

            "damage_done_reduced":
                p["damage_done_reduced"],

            "damage_per_second":
                damage_per_second,

            "damage_active_time_seconds":
                damage_active_seconds,

            "damage_active_time_percent":
                damage_active_percent,

            "damage_taken":
                p["damage_taken"],

            "damage_taken_reduced":
                p["damage_taken_reduced"],

            "damage_taken_per_second":
                damage_taken_per_second,

            "damage_taken_active_time_seconds":
                p["damage_taken_active_time_ms"]
                / 1000.0,

            "healing_done":
                p["healing_done"],

            "healing_done_reduced":
                p["healing_done_reduced"],

            "healing_per_second":
                healing_per_second,

            "overhealing":
                p["overhealing"],

            "healing_active_time_seconds":
                p["healing_active_time_ms"]
                / 1000.0,

            "healing_received":
                p["healing_received"],

            "healing_received_reduced":
                p["healing_received_reduced"],

            "healing_received_per_second":
                healing_received_per_second,

            "cast_count":
                p["cast_count"],

            "casts_per_minute":
                casts_per_minute,

            "death_count":
                p["death_count"],

            "interrupt_count":
                p["interrupt_count"],

            "dispel_count":
                p["dispel_count"],
        })


# ============================================================
# BUILD DATAFRAMES
# ============================================================

print()
print("=" * 70)
print("BUILDING OUTPUT DATASETS")
print("=" * 70)

player_df = pd.DataFrame(
    player_records
)

death_df = pd.DataFrame(
    death_records
)

ability_df = pd.DataFrame(
    ability_records
)

fight_df = pd.DataFrame(
    fight_records
)


# ============================================================
# REMOVE DUPLICATE MASTER PLAYER/FIGHT ROWS
# ============================================================

if not player_df.empty:

    key_columns = [
        "report_code",
        "fight_id",
        "player_id",
    ]

    before = len(player_df)

    player_df = player_df.drop_duplicates(
        subset=key_columns,
        keep="first"
    )

    removed = (
        before - len(player_df)
    )

    if removed:
        print(
            f"Removed duplicate player/fight rows: "
            f"{removed:,}"
        )


# ============================================================
# ROUND NUMERIC FIELDS
# ============================================================

if not player_df.empty:

    numeric_columns = [
        "damage_done",
        "damage_done_reduced",
        "damage_per_second",
        "damage_active_time_seconds",
        "damage_active_time_percent",
        "damage_taken",
        "damage_taken_reduced",
        "damage_taken_per_second",
        "damage_taken_active_time_seconds",
        "healing_done",
        "healing_done_reduced",
        "healing_per_second",
        "overhealing",
        "healing_active_time_seconds",
        "healing_received",
        "healing_received_reduced",
        "healing_received_per_second",
        "casts_per_minute",
    ]

    for column in numeric_columns:

        if column in player_df.columns:

            player_df[column] = pd.to_numeric(
                player_df[column],
                errors="coerce"
            )

    player_df[
        "damage_active_time_percent"
    ] = player_df[
        "damage_active_time_percent"
    ].round(2)

    for column in numeric_columns:

        if column in player_df.columns:
            player_df[column] = player_df[
                column
            ].round(3)


if not death_df.empty:

    death_numeric = [
        "death_timestamp",
        "death_time_seconds",
        "death_percent",
        "death_damage",
        "death_healing",
        "death_overkill",
        "death_window",
        "killing_blow_amount",
        "killing_blow_mitigated",
        "killing_blow_unmitigated",
        "killing_blow_absorbed",
    ]

    for column in death_numeric:

        if column in death_df.columns:

            death_df[column] = pd.to_numeric(
                death_df[column],
                errors="coerce"
            )

    death_df[
        "death_percent"
    ] = death_df[
        "death_percent"
    ].round(2)

    death_df[
        "death_time_seconds"
    ] = death_df[
        "death_time_seconds"
    ].round(3)


# ============================================================
# FORCE PLAYER COLUMN ORDER
# ============================================================

player_columns = [
    "report_code",
    "report_date",
    "fight_id",
    "fight_name",
    "encounter_id",
    "fight_result",
    "duration_seconds",
    "fight_start_timestamp",
    "difficulty",
    "raid_size",

    "player_name",
    "player_id",
    "warcraft_logs_source_id",
    "class",
    "spec",
    "role",
    "item_level",

    "damage_done",
    "damage_done_reduced",
    "damage_per_second",
    "damage_active_time_seconds",
    "damage_active_time_percent",

    "damage_taken",
    "damage_taken_reduced",
    "damage_taken_per_second",
    "damage_taken_active_time_seconds",

    "healing_done",
    "healing_done_reduced",
    "healing_per_second",
    "overhealing",
    "healing_active_time_seconds",

    "healing_received",
    "healing_received_reduced",
    "healing_received_per_second",

    "cast_count",
    "casts_per_minute",

    "death_count",

    "interrupt_count",
    "dispel_count",
]

player_df = player_df[
    [
        column
        for column in player_columns
        if column in player_df.columns
    ]
]


# ============================================================
# FORCE DEATH COLUMN ORDER
# ============================================================

death_columns = [
    "report_code",
    "fight_id",
    "fight_name",
    "encounter_id",
    "fight_result",
    "duration_seconds",

    "player_name",
    "player_id",
    "warcraft_logs_source_id",

    "death_timestamp",
    "death_time_seconds",
    "death_percent",

    "death_damage",
    "death_healing",
    "death_overkill",
    "death_window",

    "killing_blow_name",
    "killing_blow_guid",
    "killing_blow_type",
    "killing_blow_icon",

    "killing_blow_source_id",
    "killing_blow_source_friendly",

    "killing_blow_amount",
    "killing_blow_mitigated",
    "killing_blow_unmitigated",
    "killing_blow_absorbed",
]

if not death_df.empty:
    death_df = death_df[
        [
            column
            for column in death_columns
            if column in death_df.columns
        ]
    ]


# ============================================================
# SORT OUTPUTS
# ============================================================

if not player_df.empty:

    player_df = player_df.sort_values(
        by=[
            "report_code",
            "fight_id",
            "player_name",
        ]
    )


if not death_df.empty:

    death_df = death_df.sort_values(
        by=[
            "report_code",
            "fight_id",
            "death_time_seconds",
            "player_name",
        ],
        na_position="last"
    )


if not ability_df.empty:

    ability_df = ability_df.sort_values(
        by=[
            "report_code",
            "fight_id",
            "player_name",
            "source_dataset",
            "ability_name",
        ]
    )


if not fight_df.empty:

    fight_df = fight_df.sort_values(
        by=[
            "report_code",
            "fight_id",
        ]
    )


# ============================================================
# VALIDATION
# ============================================================

print()
print("=" * 70)
print("MASTER EXTRACTION VALIDATION")
print("=" * 70)

actual_fights = (
    player_df[
        [
            "report_code",
            "fight_id",
        ]
    ]
    .drop_duplicates()
    .shape[0]
)

unique_players = (
    player_df["player_name"].nunique()
    if not player_df.empty
    else 0
)

print()
print(
    f"Expected raid fights:        "
    f"{EXPECTED_RAID_FIGHTS:,}"
)

print(
    f"Processed raid fights:       "
    f"{processed_fights:,}"
)

print(
    f"Fights represented:          "
    f"{actual_fights:,}"
)

print(
    f"Player/fight rows:            "
    f"{len(player_df):,}"
)

print(
    f"Unique players:              "
    f"{unique_players:,}"
)

print(
    f"Death events:                "
    f"{len(death_df):,}"
)

print(
    f"Ability rows:                "
    f"{len(ability_df):,}"
)


# ------------------------------------------------------------
# DEATH VALIDATION
# ------------------------------------------------------------

if not death_df.empty:

    killing_blow_found = (
        death_df[
            "killing_blow_name"
        ]
        .fillna("")
        .astype(str)
        .str.strip()
        .ne("")
        .sum()
    )

    killing_blow_missing = (
        len(death_df)
        - killing_blow_found
    )

    print()
    print(
        "Killing blow records:"
    )

    print(
        f"  Found:                    "
        f"{killing_blow_found:,}"
    )

    print(
        f"  Missing:                  "
        f"{killing_blow_missing:,}"
    )


# ------------------------------------------------------------
# HEALING VALIDATION
# ------------------------------------------------------------

if not player_df.empty:

    healing_received_nonzero = (
        (
            player_df[
                "healing_received"
            ].fillna(0)
            > 0
        )
        .sum()
    )

    print()
    print(
        "Healing received:"
    )

    print(
        f"  Player/fight rows > 0:    "
        f"{healing_received_nonzero:,}"
    )

    print(
        f"  Total healing received:   "
        f"{player_df['healing_received'].sum():,.0f}"
    )


# ------------------------------------------------------------
# ACTIVE TIME VALIDATION
# ------------------------------------------------------------

if not player_df.empty:

    active_rows = (
        player_df[
            "damage_active_time_seconds"
        ]
        .fillna(0)
        .gt(0)
        .sum()
    )

    print()
    print(
        "Active time:"
    )

    print(
        f"  Rows with active time:    "
        f"{active_rows:,}"
    )


# ------------------------------------------------------------
# NULL CHECKS
# ------------------------------------------------------------

print()
print(
    "Critical null checks:"
)

critical_columns = [
    "fight_id",
    "duration_seconds",
    "player_name",
    "player_id",
]

for column in critical_columns:

    if column in player_df.columns:

        null_count = (
            player_df[column]
            .isna()
            .sum()
        )

        print(
            f"  {column}: "
            f"{null_count:,} nulls"
        )


# ============================================================
# HARD VALIDATION
# ============================================================

if processed_fights != EXPECTED_RAID_FIGHTS:
    raise RuntimeError(
        "\nProcessing did not cover all 205 raid fights. "
        "No output CSVs were written."
    )

if actual_fights != EXPECTED_RAID_FIGHTS:
    raise RuntimeError(
        "\nPlayer master does not contain all 205 raid fights. "
        "No output CSVs were written."
    )

if player_df.empty:
    raise RuntimeError(
        "\nPlayer master is empty. "
        "No output CSVs were written."
    )


# ============================================================
# SAVE OUTPUTS
# ============================================================

print()
print("=" * 70)
print("SAVING MASTER CSV FILES")
print("=" * 70)

player_df.to_csv(
    PLAYER_FIGHT_OUTPUT,
    index=False,
    encoding="utf-8-sig"
)

death_df.to_csv(
    DEATH_OUTPUT,
    index=False,
    encoding="utf-8-sig"
)

ability_df.to_csv(
    ABILITY_OUTPUT,
    index=False,
    encoding="utf-8-sig"
)

fight_df.to_csv(
    FIGHT_OUTPUT,
    index=False,
    encoding="utf-8-sig"
)


# ============================================================
# FINAL SUMMARY
# ============================================================

print()
print("=" * 70)
print("MASTER EXTRACTION COMPLETE")
print("=" * 70)

print()
print(
    f"Reports:                    "
    f"{report_count:,}"
)

print(
    f"Total raid fights:          "
    f"{EXPECTED_RAID_FIGHTS:,}"
)

print(
    f"Player/fight rows:           "
    f"{len(player_df):,}"
)

print(
    f"Death events:                "
    f"{len(death_df):,}"
)

print(
    f"Ability rows:                "
    f"{len(ability_df):,}"
)

print()
print("OUTPUT DIRECTORY:")
print(OUTPUT_DIR)

print()
print("FILES CREATED:")

print(
    f"  {PLAYER_FIGHT_OUTPUT.name}"
)

print(
    f"  {DEATH_OUTPUT.name}"
)

print(
    f"  {ABILITY_OUTPUT.name}"
)

print(
    f"  {FIGHT_OUTPUT.name}"
)

print()
print("=" * 70)
print("IMPORTANT")
print("=" * 70)

print("""
This extraction intentionally keeps detailed information in
separate CSVs instead of flattening every ability/event into the
player/fight table.

PLAYER_FIGHT_MASTER:
    One row per player per raid fight.

PLAYER_DEATH_EVENTS:
    One row per player death, including killing-blow information.

PLAYER_ABILITY_EVENTS:
    Ability-level aggregate data by player/fight/ability.

FIGHT_INVENTORY_MASTER:
    One row per raid fight.

Active Time:
    DamageDone activeTime is retained as the primary activity
    measure. It is descriptive and should not be interpreted by
    itself as a measure of poor play.

Healing Received:
    Calculated from the Healing target records, not from
    healing_done.

Killing Blow:
    Preserved from the raw Warcraft Logs death record. When a
    matching death event is available, the event source ID and
    damage details are also retained.

Time Dead / Resurrections:
    These are NOT fabricated. They are not added to the master
    table unless the raw data provides enough information to
    calculate them reliably.

The detailed_raw source files are never modified.
""")

print()
print("=" * 70)
print("DONE")
print("=" * 70)
