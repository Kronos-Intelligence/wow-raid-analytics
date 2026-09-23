import os
import json
import pandas as pd
from collections import defaultdict


# ============================================================
# KRONOS INTELLIGENCE
# WORLD OF WARCRAFT RAID ANALYTICS
#
# V3 - STAGE 3
# NORMALIZATION PIPELINE
#
# Input:
#     detailed_raw/
#
# Output:
#     normalized_v3/
#
# This script converts the raw Warcraft Logs JSON files into
# Power BI-friendly relational CSV tables.
# ============================================================


# ============================================================
# 1. FOLDER LOCATIONS
# ============================================================

BASE_FOLDER = os.getenv("WOW_RAID_ANALYTICS_BASE", os.getcwd())
RAW_FOLDER = os.path.join(BASE_FOLDER, "detailed_raw")

OUTPUT_FOLDER = os.path.join(BASE_FOLDER, "normalized_v3")


os.makedirs(
    OUTPUT_FOLDER,
    exist_ok=True
)


# ============================================================
# 2. OUTPUT TABLE CONTAINERS
# ============================================================

dim_reports = []
dim_fights = []
dim_players = []
dim_abilities = []
dim_targets = []

fact_player_performance = []
fact_damage_abilities = []
fact_damage_targets = []
fact_damage_taken = []
fact_healing = []
fact_deaths = []
fact_interrupts = []
fact_dispels = []
fact_casts = []


# ============================================================
# 3. TRACK UNIQUE DIMENSION RECORDS
# ============================================================

seen_reports = set()
seen_fights = set()
seen_players = set()
seen_abilities = set()
seen_targets = set()


# ============================================================
# 4. HELPER FUNCTIONS
# ============================================================

def load_json(path):

    try:

        with open(
            path,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    except Exception as error:

        print(
            f"ERROR loading {path}: {error}"
        )

        return None


def get_entries(data):

    if not isinstance(data, dict):
        return []

    inner = data.get("data", {})

    if not isinstance(inner, dict):
        return []

    entries = inner.get(
        "entries",
        []
    )

    if not isinstance(entries, list):
        return []

    return entries


def safe_number(value):

    if value is None:
        return 0

    if isinstance(
        value,
        (int, float)
    ):
        return value

    try:
        return float(value)

    except (TypeError, ValueError):
        return 0


def add_unique(
    collection,
    seen,
    key,
    record
):

    if key not in seen:

        collection.append(record)

        seen.add(key)


# ============================================================
# 5. FIND REPORT FOLDERS
# ============================================================

print("=" * 70)
print("KRONOS INTELLIGENCE")
print("WORLD OF WARCRAFT RAID ANALYTICS")
print("V3 - STAGE 3 NORMALIZATION")
print("=" * 70)
print()


report_folders = []


for item in os.listdir(
    RAW_FOLDER
):

    full_path = os.path.join(
        RAW_FOLDER,
        item
    )

    if os.path.isdir(full_path):

        report_folders.append(
            full_path
        )


report_folders.sort()


print(
    f"Report folders found: "
    f"{len(report_folders)}"
)

print()


# ============================================================
# 6. PROCESS REPORTS
# ============================================================

processed_fights = 0
failed_fights = 0


for report_folder in report_folders:

    folder_name = os.path.basename(
        report_folder
    )

    print(
        f"Processing report: "
        f"{folder_name}"
    )


    # --------------------------------------------------------
    # Find fight metadata files
    # --------------------------------------------------------

    metadata_files = [

        f for f in os.listdir(
            report_folder
        )

        if (
            f.startswith("fight_")
            and f.endswith(
                "_metadata.json"
            )
        )

    ]


    metadata_files.sort()


    for metadata_filename in metadata_files:

        metadata_path = os.path.join(
            report_folder,
            metadata_filename
        )


        metadata = load_json(
            metadata_path
        )


        if metadata is None:

            failed_fights += 1

            continue


        report_code = str(
            metadata.get(
                "report_code",
                folder_name
            )
        )

        fight_id = int(
            safe_number(
                metadata.get(
                    "fight_id"
                )
            )
        )

        fight_name = str(
            metadata.get(
                "fight_name",
                ""
            )
        )


        # ====================================================
        # REPORT DIMENSION
        # ====================================================

        if report_code not in seen_reports:

            dim_reports.append({

                "report_code":
                    report_code,

                "report_date":
                    metadata.get(
                        "report_date"
                    ),

                "report_title":
                    metadata.get(
                        "report_title"
                    )

            })

            seen_reports.add(
                report_code
            )


        # ====================================================
        # FIGHT DIMENSION
        # ====================================================

        fight_key = (
            report_code,
            fight_id
        )


        if fight_key not in seen_fights:

            dim_fights.append({

                "report_code":
                    report_code,

                "fight_id":
                    fight_id,

                "fight_name":
                    fight_name,

                "encounter_id":
                    metadata.get(
                        "encounter_id"
                    ),

                "kill":
                    metadata.get(
                        "kill"
                    ),

                "duration_seconds":
                    metadata.get(
                        "duration_seconds"
                    ),

                "difficulty":
                    metadata.get(
                        "difficulty"
                    ),

                "raid_size":
                    metadata.get(
                        "raid_size"
                    ),

                "player_count":
                    metadata.get(
                        "player_count"
                    ),

                "report_date":
                    metadata.get(
                        "report_date"
                    )

            })

            seen_fights.add(
                fight_key
            )


        # ====================================================
        # LOAD DATA FILES
        # ====================================================

        prefix = (
            f"fight_{fight_id}_"
        )


        files = {

            "DamageDone":
                f"{prefix}DamageDone.json",

            "DamageTaken":
                f"{prefix}DamageTaken.json",

            "Healing":
                f"{prefix}Healing.json",

            "Deaths":
                f"{prefix}Deaths.json",

            "Interrupts":
                f"{prefix}Interrupts.json",

            "Dispels":
                f"{prefix}Dispels.json",

            "Casts":
                f"{prefix}Casts.json"

        }


        loaded = {}


        for data_type, filename in files.items():

            path = os.path.join(
                report_folder,
                filename
            )


            if os.path.exists(path):

                loaded[data_type] = load_json(
                    path
                )


        # ====================================================
        # DAMAGE DONE
        # ====================================================

        damage_data = loaded.get(
            "DamageDone"
        )


        damage_entries = get_entries(
            damage_data
        )


        for entry in damage_entries:

            player_id = entry.get(
                "id"
            )

            player_name = entry.get(
                "name",
                ""
            )


            # ----------------------------------------------
            # PLAYER DIMENSION
            # ----------------------------------------------

            player_key = str(
                player_id
            )


            if player_key not in seen_players:

                dim_players.append({

                    "player_id":
                        player_id,

                    "player_name":
                        player_name,

                    "player_type":
                        entry.get(
                            "type"
                        ),

                    "icon":
                        entry.get(
                            "icon"
                        )

                })

                seen_players.add(
                    player_key
                )


            # ----------------------------------------------
            # PLAYER PERFORMANCE
            # ----------------------------------------------

            fact_player_performance.append({

                "report_code":
                    report_code,

                "fight_id":
                    fight_id,

                "player_id":
                    player_id,

                "player_name":
                    player_name,

                "player_type":
                    entry.get(
                        "type"
                    ),

                "item_level":
                    entry.get(
                        "itemLevel"
                    ),

                "total_damage":
                    safe_number(
                        entry.get(
                            "total"
                        )
                    ),

                "active_time_ms":
                    safe_number(
                        entry.get(
                            "activeTime"
                        )
                    ),

                "active_time_pct":
                    safe_number(
                        entry.get(
                            "activeTimePercentage"
                        )
                    ),

                "active_downtime_ms":
                    safe_number(
                        entry.get(
                            "activeTime",
                            0
                        )
                    ),

                "fight_name":
                    fight_name

            })


            # ----------------------------------------------
            # ABILITIES
            # ----------------------------------------------

            abilities = entry.get(
                "abilities",
                []
            )


            if isinstance(
                abilities,
                list
            ):

                for ability in abilities:

                    ability_id = ability.get(
                        "guid"
                    )

                    ability_name = ability.get(
                        "name",
                        ""
                    )


                    ability_key = (
                        str(ability_id),
                        ability_name
                    )


                    if ability_key not in seen_abilities:

                        dim_abilities.append({

                            "ability_id":
                                ability_id,

                            "ability_name":
                                ability_name,

                            "ability_icon":
                                ability.get(
                                    "icon"
                                )

                        })

                        seen_abilities.add(
                            ability_key
                        )


                    fact_damage_abilities.append({

                        "report_code":
                            report_code,

                        "fight_id":
                            fight_id,

                        "player_id":
                            player_id,

                        "ability_id":
                            ability_id,

                        "ability_name":
                            ability_name,

                        "total":
                            safe_number(
                                ability.get(
                                    "total"
                                )
                            ),

                        "casts":
                            safe_number(
                                ability.get(
                                    "casts"
                                )
                            ),

                        "active_time":
                            safe_number(
                                ability.get(
                                    "activeTime"
                                )
                            )

                    })


            # ----------------------------------------------
            # TARGETS
            # ----------------------------------------------

            targets = entry.get(
                "targets",
                []
            )


            if isinstance(
                targets,
                list
            ):

                for target in targets:

                    target_id = target.get(
                        "id"
                    )

                    target_name = target.get(
                        "name",
                        ""
                    )


                    target_key = (
                        str(target_id),
                        target_name
                    )


                    if target_key not in seen_targets:

                        dim_targets.append({

                            "target_id":
                                target_id,

                            "target_name":
                                target_name,

                            "target_type":
                                target.get(
                                    "type"
                                )

                        })

                        seen_targets.add(
                            target_key
                        )


                    fact_damage_targets.append({

                        "report_code":
                            report_code,

                        "fight_id":
                            fight_id,

                        "player_id":
                            player_id,

                        "target_id":
                            target_id,

                        "target_name":
                            target_name,

                        "total":
                            safe_number(
                                target.get(
                                    "total"
                                )
                            ),

                        "hits":
                            safe_number(
                                target.get(
                                    "hits"
                                )
                            )

                    })


        # ====================================================
        # DAMAGE TAKEN
        # ====================================================

        damage_taken_data = loaded.get(
            "DamageTaken"
        )


        damage_taken_entries = get_entries(
            damage_taken_data
        )


        for entry in damage_taken_entries:

            player_id = entry.get(
                "id"
            )

            player_name = entry.get(
                "name",
                ""
            )


            sources = entry.get(
                "sources",
                []
            )


            if not isinstance(
                sources,
                list
            ):

                sources = []


            for source in sources:

                fact_damage_taken.append({

                    "report_code":
                        report_code,

                    "fight_id":
                        fight_id,

                    "player_id":
                        player_id,

                    "player_name":
                        player_name,

                    "source_id":
                        source.get(
                            "id"
                        ),

                    "source_name":
                        source.get(
                            "name"
                        ),

                    "total":
                        safe_number(
                            source.get(
                                "total"
                            )
                        ),

                    "hits":
                        safe_number(
                            source.get(
                                "hits"
                            )
                        )

                })


        # ====================================================
        # HEALING
        # ====================================================

        healing_data = loaded.get(
            "Healing"
        )


        healing_entries = get_entries(
            healing_data
        )


        for entry in healing_entries:

            fact_healing.append({

                "report_code":
                    report_code,

                "fight_id":
                    fight_id,

                "player_id":
                    entry.get(
                        "id"
                    ),

                "player_name":
                    entry.get(
                        "name"
                    ),

                "total_healing":
                    safe_number(
                        entry.get(
                            "total"
                        )
                    ),

                "active_time_ms":
                    safe_number(
                        entry.get(
                            "activeTime"
                        )
                    ),

                "item_level":
                    entry.get(
                        "itemLevel"
                    )

            })


        # ====================================================
        # DEATHS
        # ====================================================

        deaths_data = loaded.get(
            "Deaths"
        )


        deaths_entries = get_entries(
            deaths_data
        )


        for entry in deaths_entries:

            fact_deaths.append({

                "report_code":
                    report_code,

                "fight_id":
                    fight_id,

                "player_id":
                    entry.get(
                        "id"
                    ),

                "player_name":
                    entry.get(
                        "name"
                    ),

                "death_time":
                    entry.get(
                        "deathTime"
                    ),

                "death_reason":
                    entry.get(
                        "deathReason"
                    )

            })


        # ====================================================
        # INTERRUPTS
        # ====================================================

        interrupts_data = loaded.get(
            "Interrupts"
        )


        interrupts_entries = get_entries(
            interrupts_data
        )


        for entry in interrupts_entries:

            fact_interrupts.append({

                "report_code":
                    report_code,

                "fight_id":
                    fight_id,

                "player_id":
                    entry.get(
                        "id"
                    ),

                "player_name":
                    entry.get(
                        "name"
                    ),

                "ability":
                    entry.get(
                        "ability"
                    ),

                "source":
                    entry.get(
                        "source"
                    ),

                "target":
                    entry.get(
                        "target"
                    ),

                "timestamp":
                    entry.get(
                        "timestamp"
                    )

            })


        # ====================================================
        # DISPELS
        # ====================================================

        dispels_data = loaded.get(
            "Dispels"
        )


        dispels_entries = get_entries(
            dispels_data
        )


        for entry in dispels_entries:

            fact_dispels.append({

                "report_code":
                    report_code,

                "fight_id":
                    fight_id,

                "player_id":
                    entry.get(
                        "id"
                    ),

                "player_name":
                    entry.get(
                        "name"
                    ),

                "ability":
                    entry.get(
                        "ability"
                    ),

                "source":
                    entry.get(
                        "source"
                    ),

                "target":
                    entry.get(
                        "target"
                    ),

                "timestamp":
                    entry.get(
                        "timestamp"
                    )

            })


        # ====================================================
        # CASTS
        # ====================================================

        casts_data = loaded.get(
            "Casts"
        )


        casts_entries = get_entries(
            casts_data
        )


        for entry in casts_entries:

            fact_casts.append({

                "report_code":
                    report_code,

                "fight_id":
                    fight_id,

                "player_id":
                    entry.get(
                        "id"
                    ),

                "player_name":
                    entry.get(
                        "name"
                    ),

                "ability":
                    entry.get(
                        "ability"
                    ),

                "casts":
                    safe_number(
                        entry.get(
                            "casts"
                        )
                    ),

                "timestamp":
                    entry.get(
                        "timestamp"
                    )

            })


        processed_fights += 1


print()
print("=" * 70)
print("RAW EXTRACTION PROCESSING COMPLETE")
print("=" * 70)
print()


# ============================================================
# 7. CONVERT TO DATAFRAMES
# ============================================================

tables = {

    "dim_report":
        dim_reports,

    "dim_fight":
        dim_fights,

    "dim_player":
        dim_players,

    "dim_ability":
        dim_abilities,

    "dim_target":
        dim_targets,

    "fact_player_performance":
        fact_player_performance,

    "fact_damage_abilities":
        fact_damage_abilities,

    "fact_damage_targets":
        fact_damage_targets,

    "fact_damage_taken":
        fact_damage_taken,

    "fact_healing":
        fact_healing,

    "fact_deaths":
        fact_deaths,

    "fact_interrupts":
        fact_interrupts,

    "fact_dispels":
        fact_dispels,

    "fact_casts":
        fact_casts

}


# ============================================================
# 8. SAVE TABLES
# ============================================================

print(
    "Saving normalized tables..."
)

print()


for table_name, records in tables.items():

    dataframe = pd.DataFrame(
        records
    )


    output_path = os.path.join(

        OUTPUT_FOLDER,

        f"{table_name}.csv"

    )


    dataframe.to_csv(

        output_path,

        index=False,

        encoding="utf-8"

    )


    print(

        f"{table_name}: "
        f"{len(dataframe):,} records"

    )


# ============================================================
# 9. CREATE DATA DICTIONARY
# ============================================================

data_dictionary = {

    "dim_report":
        "One record per Warcraft Logs report.",

    "dim_fight":
        "One record per boss fight attempt.",

    "dim_player":
        "Unique players appearing in the extracted reports.",

    "dim_ability":
        "Unique abilities returned by Warcraft Logs.",

    "dim_target":
        "Unique damage targets.",

    "fact_player_performance":
        "Player-level performance for each fight.",

    "fact_damage_abilities":
        "Damage contribution by player and ability.",

    "fact_damage_targets":
        "Damage contribution by player and target.",

    "fact_damage_taken":
        "Damage received by player and source.",

    "fact_healing":
        "Healing performance by player and fight.",

    "fact_deaths":
        "Player deaths by fight.",

    "fact_interrupts":
        "Interrupt activity.",

    "fact_dispels":
        "Dispel activity.",

    "fact_casts":
        "Player cast activity."

}


dictionary_path = os.path.join(

    OUTPUT_FOLDER,

    "data_dictionary.json"

)


with open(

    dictionary_path,

    "w",

    encoding="utf-8"

) as file:

    json.dump(

        data_dictionary,

        file,

        indent=2

    )


# ============================================================
# 10. FINAL VALIDATION
# ============================================================

print()
print("=" * 70)
print("NORMALIZATION SUMMARY")
print("=" * 70)
print()


print(
    f"Reports: "
    f"{len(dim_reports):,}"
)

print(
    f"Fights: "
    f"{len(dim_fights):,}"
)

print(
    f"Players: "
    f"{len(dim_players):,}"
)

print(
    f"Abilities: "
    f"{len(dim_abilities):,}"
)

print(
    f"Targets: "
    f"{len(dim_targets):,}"
)

print()


print(
    f"Player performance rows: "
    f"{len(fact_player_performance):,}"
)

print(
    f"Damage ability rows: "
    f"{len(fact_damage_abilities):,}"
)

print(
    f"Damage target rows: "
    f"{len(fact_damage_targets):,}"
)

print(
    f"Damage taken rows: "
    f"{len(fact_damage_taken):,}"
)

print(
    f"Healing rows: "
    f"{len(fact_healing):,}"
)

print(
    f"Deaths: "
    f"{len(fact_deaths):,}"
)

print(
    f"Interrupts: "
    f"{len(fact_interrupts):,}"
)

print(
    f"Dispels: "
    f"{len(fact_dispels):,}"
)

print(
    f"Casts: "
    f"{len(fact_casts):,}"
)

print()


print(
    "Output folder:"
)

print(
    OUTPUT_FOLDER
)

print()


print("=" * 70)
print("V3 STAGE 3 COMPLETE")
print("=" * 70)

print()
print(
    "Do NOT build the Power BI dashboard yet."
)

print(
    "We will validate the normalized data first."
)