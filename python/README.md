# Python Data Preparation

This folder contains the Python-based data preparation work used as part of the World of Warcraft Raid Analytics project.

Python was used to support the transformation and preparation of World of Warcraft combat-log data before the data was analyzed in Power BI.

## Purpose

The Python workflow supported the preparation of structured datasets for analytical use, including player performance, fight-level information, and combat-event data.

The prepared data was used to support the Power BI data model and dashboard.

## Data Preparation Areas

The project data includes information related to:

- Fight and encounter information
- Player performance
- Damage
- Healing
- Deaths
- Interrupts
- Dispels
- Player abilities
- Fight outcomes

## Analytical Workflow

The overall workflow for the project was:

1. Collect World of Warcraft combat-log data.
2. Prepare and organize the raw data.
3. Create structured datasets for analysis.
4. Load the prepared datasets into Power BI.
5. Build relationships and dimensional tables within the Power BI data model.
6. Develop analytical measures and KPIs.
7. Create interactive dashboard pages for raid, boss, player, utility, and survivability analysis.

## Relationship to Power BI

The prepared datasets serve as source data for the Power BI dashboard.

Additional tables, including `DimDate`, `DimFight`, `DimPlayer`, and `Player Display`, were created within Power BI as part of the analytical data model rather than being separate source datasets.

The final Power BI dashboard contains four analytical pages:

- Raid Overview
- Boss Performance
- Player Performance
- Utility & Survivability

## Tools

- Python
- Power BI
- CSV
- World of Warcraft combat-log data

## Project Outcome

The Python preparation process helped transform detailed combat-log information into structured data that could be analyzed through an interactive Power BI dashboard.

The resulting dashboard provides a consolidated view of raid progression, encounter performance, player performance, utility activity, and survivability.
