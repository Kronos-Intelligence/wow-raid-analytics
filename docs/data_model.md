# Power BI Data Model

This document describes the data model used for the **World of Warcraft Raid Analytics** Power BI dashboard.

The model combines cleaned analytical datasets prepared through Python with dimensional and supporting tables created directly within Power BI. The structure allows the dashboard to move from high-level raid analysis into detailed fight, player, and ability-level analysis.

---

## Model Architecture

The project follows this general analytical pipeline:

    World of Warcraft Combat Logs
                |
                v
          Python Processing
                |
                v
           Data Validation
                |
                v
        Cleaned Analytical Data
                |
                v
           Power BI Data Model
                |
         +------+------+------+
         |             |      |
         v             v      v
      Fight Data   Player Data  Event Data
         |             |      |
         +-------------+------+
                       |
                       v
                Power BI Measures
                       |
                       v
              Interactive Dashboard

Python is used to extract, clean, normalize, classify, validate, and prepare the analytical datasets before they are loaded into Power BI.

Power BI then combines those prepared datasets with dimensional and supporting tables to provide the relationships, calculations, filtering, and visualizations used by the dashboard.

---

## Data Model Components

The Power BI model contains three primary categories of data:

1. Analytical fact-style datasets prepared outside Power BI
2. Dimensional tables created within Power BI
3. Supporting tables used for player presentation and dashboard functionality

---

## Analytical Datasets

The primary analytical datasets loaded into the Power BI model are:

| Dataset | Purpose |
|---|---|
| `fight_inventory_master_COMPLETE` | Provides fight- and encounter-level information used for raid and boss analysis. |
| `player_fight_master_COMPLETE` | Provides player performance information at the fight level, including performance and outcome metrics. |
| `player_ability_events` | Contains player ability event information used for ability-level analysis. |
| `player_death_events` | Contains player death events used for survivability and death analysis. |
| `player_dispel_events_FINAL` | Contains player dispel activity used for utility analysis. |
| `player_healing_received_events_COMPLETE` | Contains healing received information used for player survivability and healing analysis. |
| `player_interrupt_events_FINAL` | Contains interrupt activity used for utility and encounter analysis. |

These datasets represent the cleaned analytical layer of the project.

The datasets were prepared through the Python processing workflow before being incorporated into the Power BI model.

---

## Dimensional Tables

Several dimensional tables were created directly within Power BI rather than being maintained as separate CSV files.

### DimDate

The `DimDate` table provides date-related fields used for time-based analysis and filtering.

It allows the model to support consistent date filtering and time-oriented analysis where applicable.

### DimFight

The `DimFight` table provides standardized fight and encounter information used to support analysis across the analytical datasets.

This table helps provide a consistent reference for encounters and allows users to move between raid-level, encounter-level, and detailed performance views.

### DimPlayer

The `DimPlayer` table provides a standardized player reference used throughout the model.

It supports consistent player identification and allows player-related analytical datasets to be connected through a common player dimension.

---

## Player Display Table

The `Player Display` table is a supporting table created within Power BI.

It is used to support player presentation and selection within the dashboard.

Rather than representing another raw event dataset, the table provides a controlled player-facing reference that supports dashboard interaction and readable player selections.

This helps separate the analytical data used for calculations from the presentation requirements of the dashboard.

---

## Fact-Style Data

The analytical datasets function primarily as fact-style tables because they contain measurable events and performance information.

Examples include:

- Fight results
- Player performance
- Damage
- Healing
- Deaths
- Interrupts
- Dispels
- Ability activity

These datasets provide the detailed records from which Power BI measures and visualizations are generated.

---

## Dimension and Fact Relationship

Conceptually, the model follows a dimensional structure in which common entities such as players, fights, and dates provide reference points for the analytical datasets.

    DimDate
       |
       |
    DimFight
       |
       +----------------------+
       |                      |
       v                      v
    Fight Inventory      Player Fight Data
                               |
                            DimPlayer
                               |
              +----------------+----------------+
              |         |        |       |      |
              v         v        v       v      v
           Ability    Death   Healing  Interrupt Dispel
            Events    Events   Events    Events  Events

The exact relationships and filter directions are defined within the Power BI model.

The primary conceptual keys used to connect the model are based on shared identifiers such as:

- Player identifiers
- Fight and encounter identifiers
- Date-related fields
- Other standardized fields required to connect event-level data to the appropriate fight and player

---

## Data Flow Through the Model

The data moves through the model in several stages.

### 1. Raw Combat Data

World of Warcraft combat-log information provides detailed event-level records.

These records can contain information about:

- Fights
- Players
- Damage
- Healing
- Deaths
- Interrupts
- Dispels
- Abilities
- Encounter outcomes

### 2. Python Data Preparation

Python scripts are used to process the raw data.

The preparation workflow includes activities such as:

- Extraction
- Data cleaning
- Normalization
- Classification
- Validation
- Consolidation
- Analytical dataset construction

The goal is to produce structured datasets that are suitable for analytical use.

### 3. Validated Analytical Data

The processed datasets are validated and prepared for Power BI.

This creates a consistent analytical layer between the raw combat-log information and the dashboard.

### 4. Power BI Data Model

The cleaned datasets are loaded into Power BI and combined with dimensional tables created within Power BI.

The model provides the structure necessary to analyze the data across different levels of detail.

### 5. Measures and Calculations

Power BI measures are used to transform the underlying data into meaningful performance metrics.

These calculations support areas such as:

- Raid performance
- Boss performance
- Player performance
- Damage
- Healing
- DPS
- Fight outcomes
- Deaths
- Interrupts
- Dispels
- Survivability
- Utility

### 6. Interactive Dashboard

The resulting model powers the four primary analytical pages in the Power BI dashboard:

- Raid Overview
- Boss Performance
- Player Performance
- Utility & Survivability

---

## Drill-Down Structure

One of the primary purposes of the model is to allow users to move from broad performance information into increasingly detailed analysis.

The conceptual drill-down structure is:

    Raid
      |
      v
    Encounter / Boss
      |
      v
    Fight
      |
      v
    Player
      |
      v
    Ability / Event

This structure allows the dashboard to answer questions at multiple levels.

For example:

- How did the raid perform overall?
- Which encounters were successful?
- How did individual bosses perform?
- Which players contributed to the outcome?
- What happened during individual fights?
- Which abilities contributed to player performance?
- Where did deaths, interrupts, or dispels occur?

---

## Dashboard Relationship to the Model

The data model directly supports the four primary dashboard pages.

### Raid Overview

Uses aggregated raid and player performance data to provide a high-level view of overall raid activity and performance.

### Boss Performance

Uses fight and encounter-level information to analyze:

- Attempts
- Kills
- Wipes
- Kill rate
- Fight duration
- DPS
- Healing
- Damage
- Encounter performance

### Player Performance

Uses player and fight-level data to analyze individual player performance, including:

- Fight results
- Active time
- Damage
- DPS
- Healing
- Interrupts
- Deaths
- Dispels

### Utility & Survivability

Uses event-level datasets to analyze:

- Deaths
- Damage taken
- Healing received
- Interrupts
- Dispel activity
- Interrupting abilities
- Interrupted abilities
- Player survivability

---

## Why the Model Uses Multiple Tables

The project separates different types of analytical information rather than placing every event into a single dataset.

This approach provides several benefits:

- Reduces unnecessary duplication
- Keeps event-level datasets focused on specific analytical purposes
- Supports more efficient analysis
- Allows different event types to be analyzed independently
- Provides reusable player and fight dimensions
- Makes the Power BI model easier to navigate
- Supports detailed drill-down analysis

For example, death events can be analyzed independently from interrupt events while still being connected to the appropriate player and fight context.

---

## Power BI-Created Tables vs. Source Datasets

Not every table visible in the Power BI Data pane exists as a separate source file in the repository.

The repository contains the primary analytical datasets used to build the model.

The following tables were created or maintained within Power BI:

- `DimDate`
- `DimFight`
- `DimPlayer`
- `Player Display`

These tables support modeling, filtering, relationships, and dashboard presentation.

The distinction is intentional: the repository preserves the major analytical source datasets while Power BI contains additional modeling structures required for the final dashboard.

---

## Model Design Approach

The model was designed to balance analytical detail with dashboard usability.

The Python layer handles data preparation and validation, while Power BI handles:

- Data modeling
- Relationships
- Measures
- Filtering
- Aggregation
- Interactive analysis
- Dashboard presentation

This separation allows the project to demonstrate a complete analytics workflow rather than relying exclusively on transformations performed inside the visualization tool.

---

## Summary

The World of Warcraft Raid Analytics data model provides the structural foundation for the Power BI dashboard.

The overall workflow is:

    Combat-Log Data
          |
          v
    Python Data Preparation
          |
          v
    Validation and Cleaning
          |
          v
    Analytical Datasets
          |
          v
    Power BI Data Model
          |
          +----------------------+
          |                      |
          v                      v
    Dimensional Tables      Supporting Tables
          |                      |
          +----------+-----------+
                     |
                     v
              Power BI Measures
                     |
                     v
          Interactive Dashboard

The resulting model supports analysis from the raid level down to individual encounters, players, abilities, and events.

This structure demonstrates how detailed event-level game data can be transformed into a structured analytical model and ultimately into an interactive business-intelligence-style dashboard.
