# Data Dictionary

This document describes the primary datasets used in the World of Warcraft Raid Analytics project and explains how they support the Power BI analytical model.

The project combines fight-level, player-level, and event-level combat data to analyze raid progression, boss performance, player performance, utility, and survivability.

---

## Data Architecture

The analytical data is organized into several categories:

- Fight and encounter data
- Player performance data
- Ability and utility events
- Death events
- Dispel events
- Healing events
- Interrupt events

The processed datasets are stored in the `/data` folder.

Additional dimensional and display tables were created directly within Power BI and are documented separately in the [Data Model](data_model.md).

---

# Analytical Datasets

## fight_inventory_master_COMPLETE.csv

### Purpose

Contains the master inventory of fights and encounters used to organize raid and encounter-level analysis.

### Analytical Use

This dataset supports:

- Raid progression analysis
- Encounter identification
- Fight-level filtering
- Boss performance analysis
- Fight duration analysis
- Kill, wipe, and attempt analysis
- Linking encounters to player performance

### Used By

Primarily supports the:

- Raid Overview
- Boss Performance
- Player Performance

Power BI pages.

---

## player_fight_master_COMPLETE.csv

### Purpose

Contains player-level performance information associated with individual fights.

This dataset provides the foundation for analyzing how individual players performed during encounters.

### Analytical Use

The data supports metrics and analysis including:

- Player damage
- Damage taken
- Healing received
- Average DPS
- Fight result
- Fight duration
- Active time
- Deaths
- Interrupts
- Dispels
- Player and encounter comparisons

### Used By

Primarily supports:

- Player Performance
- Raid Overview
- Utility & Survivability

---

## player_ability_events.csv

### Purpose

Contains player ability event information used to analyze player actions during encounters.

### Analytical Use

The dataset supports analysis of player abilities and their relationship to encounter mechanics.

It contributes to utility analysis, including interruption-related analysis and player ability activity.

### Used By

Primarily supports:

- Utility & Survivability
- Player Performance

---

## player_death_events.csv

### Purpose

Contains player death events recorded during encounters.

### Analytical Use

The dataset supports survivability analysis, including:

- Player deaths
- Death frequency
- Deaths by encounter
- Player survivability comparisons

### Used By

Primarily supports:

- Utility & Survivability
- Player Performance
- Raid Overview

---

## player_dispel_events_FINAL.csv

### Purpose

Contains player dispel events used to analyze dispel activity during encounters.

### Analytical Use

The dataset supports:

- Dispel counts
- Player utility comparisons
- Encounter-specific dispel activity
- Utility performance analysis

### Used By

Primarily supports:

- Utility & Survivability
- Player Performance

---

## player_healing_received_events_COMPLETE.csv

### Purpose

Contains healing events associated with players during encounters.

### Analytical Use

The dataset supports analysis of:

- Total healing received
- Average healing received
- Player survivability
- Healing-related performance comparisons

### Used By

Primarily supports:

- Raid Overview
- Player Performance
- Utility & Survivability

---

## player_interrupt_events_FINAL.csv

### Purpose

Contains player interruption events recorded during encounters.

### Analytical Use

The dataset supports detailed interruption analysis, including:

- Total interrupts
- Interrupting player
- Boss
- Interrupted ability
- Interrupting ability
- Interrupts by encounter
- Interrupts by player
- Ability-specific interruption analysis

### Used By

Primarily supports the:

- Utility & Survivability

dashboard.

The dashboard includes an **Interrupts by Player Ability** matrix that breaks interruption activity down by player, boss, interrupted ability, and interrupting ability.

---

# Key Analytical Concepts

The following concepts are used throughout the Power BI dashboard.

## Damage Done

Measures the amount of damage a player contributes during an encounter.

Used for player performance comparisons and raid performance analysis.

---

## Damage Taken

Measures the amount of damage a player receives during an encounter.

Used primarily for survivability and defensive-performance analysis.

---

## Healing Received

Measures healing received by a player during encounters.

Used to evaluate survivability and player-level healing exposure.

---

## Average DPS

Represents average damage output per second for a player during the applicable encounter or analysis period.

Used extensively in player and boss performance analysis.

---

## Deaths

Represents player deaths recorded during encounters.

Death information is used to evaluate player survivability and encounter outcomes.

---

## Deaths per Player

Provides a player-level measure of deaths across the applicable encounters.

This metric is used in the Utility & Survivability analysis.

---

## Interrupts

Represents successful interruption activity performed by players.

Interrupt data is analyzed by player, boss, interrupted ability, and interrupting ability.

---

## Dispel

Represents dispel activity performed during encounters.

Dispel information is used as a utility-performance metric.

---

## Fight Result

Represents the outcome of an encounter or fight.

The Power BI model uses fight outcomes such as:

- Kill
- Wipe

These outcomes support encounter progression and boss performance analysis.

---

## Fight Duration

Represents the duration of an encounter.

Fight duration is used to provide context for:

- DPS
- Healing
- Damage
- Encounter performance
- Kill and wipe analysis

---

## Active Time

Represents the percentage or amount of time a player was actively participating during an encounter.

The Player Performance analysis uses **Average Active Time %** to compare player participation.

---

# Power BI-Created Tables

Not all tables in the final Power BI model originate from CSV files.

The following tables were created within Power BI:

## DimDate

A date dimension used to support date-based organization and analysis within the Power BI model.

---

## DimFight

A dimensional table representing fight-level information used to organize encounter analysis.

---

## DimPlayer

A dimensional table representing player information used throughout the Power BI model.

---

## Player Display

A Power BI-created supporting table used for player display and analytical presentation.

These tables are part of the Power BI data model and are not represented as standalone CSV files in the `/data` folder.

---

# Dashboard Relationships

The datasets support four major analytical areas.

## Raid Overview

The Raid Overview page provides a high-level view of raid and player performance.

The page includes:

- Player Performance Comparison
- March vs. Current performance comparison
- Damage change
- Deaths per fight
- Player Performance Summary
- Total damage done
- Total healing received
- Interrupts per fight
- Dispels per fight
- Damage taken
- Average active time

---

## Boss Performance

The Boss Performance page focuses on encounter-level performance.

The Boss Performance Summary includes metrics such as:

- Total attempts
- Total kills
- Total wipes
- Kill rate
- Average fight duration
- Average DPS
- Average healing done
- Average damage taken per fight

---

## Player Performance

The Player Performance page provides detailed player-level analysis.

The Player Performance Matrix includes:

- Player Name
- Class
- Fight Result
- Average Active Time %
- Average Fight Duration
- Damage Done
- Average DPS
- Damage Taken
- Healing Received
- Average Healing Done
- Deaths
- Interrupts
- Dispels

The matrix supports hierarchical drill-down from player to fight and fight ID.

---

## Utility & Survivability

The Utility & Survivability page focuses on player survival and utility contributions.

The page includes metrics such as:

- Total Deaths
- Deaths per Player
- Damage Taken per Player
- Average Healing Received
- Total Interrupts

The **Utility & Survivability by Player & Encounter** matrix provides player and encounter-level analysis of:

- Fight Result
- Deaths per Player
- Total Damage Taken
- Average DPS
- Average Healing Received
- Interrupts
- Dispels

The **Interrupts by Player Ability** matrix provides a more detailed view of interruption activity by:

- Player Name
- Boss
- Interrupted Ability
- Interrupting Ability
- Total Interrupts

---

# Data Preparation

The source combat-log information was processed through a Python-based data preparation workflow before being incorporated into the Power BI model.

The Python workflow included:

1. Data extraction
2. Raw data validation
3. Encounter classification
4. Content classification
5. Data normalization
6. Master dataset construction
7. Data completion
8. Utility and wipe/progression corrections
9. Final analytical validation

The Python scripts used for this process are documented in the `/python` folder.

---

# Data Quality and Validation

Validation was performed at multiple stages of the project.

The workflow includes validation of:

- Raw source data
- Normalized data
- Master analytical datasets
- Final raid analytics datasets

This approach was used to reduce data-quality issues before the information was modeled and visualized in Power BI.

---

# Relationship to the Power BI Model

The CSV datasets in `/data` provide the underlying analytical information used by the Power BI model.

Power BI then combines the prepared datasets with dimensional and supporting tables to create an interactive analytical environment.

The resulting model supports hierarchical drill-down, filtering, comparison analysis, encounter-level analysis, and player-level performance analysis.

See [Data Model](data_model.md) for the structure and relationships of the Power BI model.
