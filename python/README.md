# Python Data Preparation

This folder contains the Python scripts used to extract, validate, classify, normalize, build, and validate World of Warcraft combat-log data for the World of Warcraft Raid Analytics project.

Python was used as the data-engineering layer of the project. The resulting datasets were prepared for analysis and visualization in Power BI.

## Data Preparation Workflow

The project uses a multi-stage data preparation process:

1. Combat-log data is extracted and organized from source reports.
2. Raw data is validated for structure and quality.
3. Fight and encounter information is classified.
4. Content and encounter types are identified.
5. Data is normalized into analytical structures.
6. Master datasets are built and completed.
7. Player and fight-level performance data is assembled.
8. Utility and wipe/progression data is patched where necessary.
9. Final datasets are validated before being used in Power BI.

The scripts in this folder represent the development and production work used throughout that process.

## Python Scripts

### Data Extraction and Inventory

**`WoW_Multi_Report_Inventory.py`**

Used to inventory and organize data from multiple World of Warcraft combat-log reports.

**`WoW_Detailed_Fight_Extractor.py`**

Extracts detailed fight-level information from combat-log data for downstream analysis.

---

### Raw Data Validation

**`WoW_Raw_Data_Validator.py`**

Performs validation checks on raw source data before transformation and normalization.

**`WoW_Normalized_Data_Validator_V3.py`**

Validates normalized datasets to identify structural or data-quality issues before they are used for analytical processing.

---

### Classification and Transformation

**`WoW_Encounter_Classifier_V6.py`**

Classifies encounters and associates fight data with the appropriate encounter information.

**`WoW_Content_Classifier_V7.py`**

Classifies the content associated with combat-log data so that encounters can be analyzed consistently.

**`WoW_Normalization_V3.py`**

Transforms source data into standardized structures suitable for analytical use.

---

### Master Data Construction

**`WoW_Master_csv_script_v2.py`**

Supports creation and organization of master CSV datasets from processed combat-log data.

**`WoW_Master_Data_Completion_v5.py`**

Completes and enriches master datasets with required fields and supporting information.

**`WoW_Raid_Analytics_Builder_V8.py`**

Builds the primary analytical datasets used by the Power BI model.

**`Build_All_Fights_Player_Performance_V8_PlayerID_Spec_Role_IconFixed.py`**

Builds player/fight performance data while incorporating player IDs, specialization, and role information needed for player-level analysis.

---

### Data Corrections and Patches

**`WoW_Final_Utility_WipeProgress_Patch.py`**

Applies final corrections to utility, survivability, wipe, and progression-related data used by the analytical model.

---

### Final Validation

**`WoW_Raid_Analytics_Validator_V8.py`**

Performs final validation of the analytical datasets before they are used in the Power BI dashboard.

## Relationship to the Data Folder

The Python scripts in this folder were used to prepare the CSV datasets stored in the repository's `/data` folder.

The primary analytical datasets currently included in `/data` are:

- `fight_inventory_master_COMPLETE.csv`
- `player_ability_events.csv`
- `player_death_events.csv`
- `player_dispel_events_FINAL.csv`
- `player_fight_master_COMPLETE.csv`
- `player_healing_received_events_COMPLETE.csv`
- `player_interrupt_events_FINAL.csv`

The Power BI model also contains dimensional tables such as `DimDate`, `DimFight`, and `DimPlayer`, as well as the `Player Display` table. These supporting tables were created within Power BI rather than being standalone CSV files in the repository.

## Analytical Pipeline

The overall project flow can be summarized as:

```text
World of Warcraft Combat Logs
            ↓
     Python Extraction
            ↓
       Data Validation
            ↓
   Classification & Normalization
            ↓
      Master Data Building
            ↓
     Data Completion / Patches
            ↓
      Final Validation
            ↓
       Analytical CSVs
            ↓
          Power BI
            ↓
   Interactive Raid Analytics
