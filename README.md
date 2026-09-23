# World of Warcraft Raid Analytics

An end-to-end analytics project that transforms World of Warcraft combat-log data into an interactive Power BI dashboard for analyzing raid progression, boss performance, player performance, utility, and survivability.

The project demonstrates how detailed event-level data can be transformed into structured metrics, interactive visualizations, hierarchical drill-down analysis, and performance insights.

---

## Project Overview

World of Warcraft combat logs contain detailed information about fights, players, damage, healing, deaths, interrupts, dispels, and encounter outcomes.

While the underlying data provides a significant amount of information, raw combat data can be difficult to interpret without organization and analysis.

This project was created to transform that information into a multi-page analytics dashboard that allows users to move from a high-level view of raid performance into detailed player and encounter-level analysis.

The dashboard currently analyzes:

- **205 fights/attempts**
- **169 players**
- **55 kills**
- **150 wipes**
- **26.83% overall kill rate**
- Approximately **3K recorded deaths**

The analysis is organized into four dashboard pages:

1. **Raid Overview**
2. **Boss Performance**
3. **Player Performance**
4. **Utility & Survivability**

---

# Dashboard Architecture

The dashboard is designed to move through multiple levels of analysis:

**Raid → Boss → Player → Fight → Specific Utility Events**

This structure allows users to begin with overall performance and progressively investigate the factors contributing to raid outcomes.

---

# 1. Raid Overview

The Raid Overview provides a high-level summary of raid activity and player performance.

## Key Metrics

The page includes:

| Metric | Value |
|---|---:|
| Total Fights | 205 |
| Average Fight Duration | 4.2 minutes |
| Average DPS | 88.92K |
| Total Players | 169 |
| Kill Rate | 26.83% |
| Total Wipes | 150 |
| Total Deaths | ~3K |
| Total Kills | 55 |
| Average Active Time | 76.0% |

These metrics provide an immediate view of overall raid activity and progression.

## Kill Rate by Month/Year

A time-series visualization tracks kill rate across the reporting period.

This provides historical context for evaluating changes in raid progression rather than relying only on the overall kill rate.

## Kills vs. Wipes by Month

A second trend visualization compares kills and wipes over time.

This helps identify changes in raid success and failure patterns across the reporting period.

---

## Player Performance Comparison — March vs. Current

The Raid Overview contains a comparison matrix designed to evaluate changes in individual player performance over time.

### Fields

- Player
- First Class
- March Damage
- Current Damage
- Damage Change
- Deaths per Fight
- Damage Taken
- Healing Received

The **Damage Change** measure uses conditional formatting to make positive and negative changes easier to identify.

The dashboard also includes a configurable display selection for the number of players shown.

### Interactive Analysis

Selecting a player in the comparison matrix filters the Player Performance Summary below it.

This creates a simple analytical workflow:

**Compare → Select → Investigate**

The user can identify a change in player performance and then immediately examine that player's more detailed results.

---

## Player Performance Summary

The Raid Overview also contains a hierarchical player performance matrix.

### Hierarchy

**Player Name → Fight Name**

Users can expand an individual player to examine their performance across individual fights.

### Measures

The matrix includes:

- Class
- Total Damage Done
- Total Healing Received
- Interrupts per Fight
- Dispels per Fight
- Total Damage Taken
- Deaths per Fight
- Average Active Time %

This allows player performance to be examined at both an overall level and an individual-fight level.

---

# 2. Boss Performance

The Boss Performance page focuses on encounter-level analysis.

The purpose of this page is to evaluate how individual encounters contribute to overall raid progression and where encounters present greater performance challenges.

## Key Metrics

The page includes:

| Metric | Value |
|---|---:|
| Total Attempts | 205 |
| Total Kills | 55 |
| Total Wipes | 150 |
| Kill Rate | 26.83% |
| Average Fight Duration | 4.2 minutes |
| Average DPS | 88.92K |
| Average Healing Done | 8.50M |

---

## Boss Performance Summary

The Boss Performance Summary is organized by:

**Fight Name**

Each encounter is evaluated using:

- Total Attempts
- Total Kills
- Total Wipes
- Kill Rate
- Average Fight Duration
- Average DPS
- Average Healing Done
- Average Damage Taken per Fight

This matrix combines progression outcomes with performance measures.

It allows encounters to be compared based on:

- Number of attempts
- Number of successful kills
- Number of wipes
- Kill rate
- Fight duration
- Damage output
- Healing requirements
- Damage taken

---

## Deaths per Fight by Boss

A bar chart ranks encounters by deaths per fight.

This provides a survivability perspective on encounter difficulty and helps identify fights where deaths may be contributing to unsuccessful attempts.

---

## Kill Rate by Fight

A visual comparison of kill rates across encounters provides another way to identify stronger and weaker progression results.

---

## Healing Pressure vs. Deaths by Boss

A scatter visualization compares:

- Average Healing Done
- Deaths per Fight

This provides a way to examine the relationship between healing requirements and survivability across encounters.

---

# 3. Player Performance

The Player Performance Analytics Dashboard provides detailed analysis of individual player performance.

Rather than evaluating players using DPS alone, the dashboard incorporates activity, damage, healing, incoming damage, deaths, interrupts, and dispels.

## Key Metrics

The page includes:

| Metric | Value |
|---|---:|
| Total Players | 169 |
| Average DPS | 69.68K |
| Average Healing Done | 8.50M |
| Damage Taken per Player | 223M |
| Deaths per Player | 21.01 |
| Average Active Time | 76.0% |

---

## Player Performance Matrix

The primary Player Performance matrix uses a three-level hierarchy:

**Player Name → Fight Name → Fight ID**

This allows users to move from an individual player's aggregate performance into individual fights and then into the specific fight record.

### Measures

The matrix includes:

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

This provides a multi-dimensional view of player performance.

The analysis considers:

**Damage + Activity + Survivability + Healing + Utility**

rather than treating damage output as the sole measure of performance.

---

## Top Players by Average DPS

A bar chart identifies the players with the highest average DPS.

This provides a quick view of top damage output while the detailed matrix provides additional context around those players.

---

## Activity vs. Deaths by Player

A scatter visualization compares:

- Average Active Time %
- Deaths per Fight

This allows the relationship between player activity and survivability to be explored.

---

## Deaths by Role

Deaths are also summarized by role:

- DPS
- Healer
- Tank

This provides additional context for understanding how deaths are distributed across raid roles.

---

# 4. Utility & Survivability

The Utility & Survivability page expands the analysis beyond damage and healing output.

It focuses on player deaths, incoming damage, healing received, interrupts, and dispels.

## Key Metrics

The page includes:

| Metric | Value |
|---|---:|
| Total Deaths | ~3K |
| Deaths per Player | 21.01 |
| Interrupts per Player | 17.81 |
| Total Dispels | ~2K |
| Dispels per Player | 35.13 |
| Damage Taken per Player | 223M |
| Average Healing Received | 1.64M |
| Total Interrupts | ~2K |

---

## Utility & Survivability by Player & Encounter

This matrix uses a three-level hierarchy:

**Player Name → Fight Name → Fight ID**

Users can expand a player to examine individual fights and specific fight records.

### Measures

The matrix includes:

- Class
- Fight Result
- Deaths per Player
- Total Damage Taken
- Average DPS
- Average Healing Received
- Interrupts
- Dispels

This combines performance, survivability, and utility measures in one analytical view.

The matrix allows users to investigate questions such as:

- Which players are taking the most damage?
- Which players are experiencing deaths?
- How much healing are players receiving?
- Who is contributing interrupts?
- Who is contributing dispels?
- How do these measures vary between encounters?

---

## Interrupts by Player Ability

The Utility & Survivability page contains a detailed interrupt analysis table.

### Fields

- Player Name
- Boss
- Interrupted Ability
- Interrupting Ability
- Total Interrupts

The current dataset contains **1,532 recorded interrupts** in this analysis.

The table connects the ability that was interrupted with the player and ability responsible for the interrupt.

This provides a more detailed view of utility contribution than simply reporting a total interrupt count.

The analysis can be examined as:

**Boss → Interrupted Ability → Player → Interrupting Ability → Total Interrupts**

---

# Analytical Design

A key feature of this project is the use of hierarchical analysis.

Multiple dashboard matrices allow the user to move from aggregated results into increasingly detailed records.

## Player Drill-Down

The Player Performance and Utility & Survivability matrices use:

**Player Name → Fight Name → Fight ID**

This allows the analysis to move from:

**Player → Encounter → Individual Fight**

without losing the connection to the broader player-level results.

## Interactive Filtering

The Raid Overview also connects the Player Performance Comparison matrix with the Player Performance Summary.

A user can:

1. Compare player performance between March and the current period.
2. Select a player.
3. Examine that player's detailed performance summary.

This creates a workflow from **identifying a change to investigating the underlying data**.

---

# Data & Analytics Workflow

The project follows an analytics workflow that transforms detailed combat data into an interactive analytical product.

### 1. Data Collection

Combat-log data is collected as the source dataset.

### 2. Data Transformation

Raw information is transformed into structured player, fight, encounter, performance, utility, and survivability data.

### 3. Metric Development

Performance measures and KPIs are developed for:

- Raid performance
- Encounter performance
- Player performance
- Survivability
- Healing
- Interrupts
- Dispels

### 4. Analytical Modeling

The dashboard organizes information around players, fights, encounters, and event-level utility activity.

### 5. Visualization

The resulting metrics are presented through:

- KPI cards
- Tables
- Hierarchical matrices
- Bar charts
- Line charts
- Scatter plots
- Role-based visualizations
- Interactive filtering

### 6. Insight Development

The dashboard allows users to move from high-level results into detailed records to investigate potential causes and performance patterns.

---

# Technologies

This project demonstrates experience with:

- **Python**
- **Pandas**
- **Power BI**
- Data cleaning
- Data transformation
- Data analysis
- KPI development
- Data visualization
- Interactive dashboards
- Hierarchical matrices
- Drill-down analysis
- Performance analytics
- Trend analysis
- Data storytelling

---

# Analytical Skills Demonstrated

This project demonstrates the ability to:

- Transform detailed source data into usable analytical structures
- Develop meaningful KPIs
- Analyze performance at multiple levels
- Build hierarchical drill-down structures
- Compare performance over time
- Analyze trends
- Identify performance differences
- Combine multiple measures into a cohesive dashboard
- Design interactive analytical workflows
- Present complex information in an accessible format

---

# Why This Project Matters

Although the dataset comes from a gaming environment, the analytical methods used in this project are applicable well beyond gaming.

The same concepts can be applied to business and operational datasets where users need to understand:

- Performance
- Productivity
- Outcomes
- Trends
- Resource utilization
- Quality
- Exceptions
- Contributing factors

The core analytical process is:

**Collect → Transform → Measure → Compare → Investigate → Communicate**

The project demonstrates how detailed event-level data can be transformed into an interactive tool that supports both high-level monitoring and detailed investigation.

---

# Future Development

Potential future enhancements include:

- Automated combat-log ingestion
- Additional historical comparisons
- Raid-to-raid performance tracking
- Player progression tracking
- Expanded class and specialization analysis
- Additional survivability analysis
- Expanded utility analysis
- Automated reporting
- Player improvement tracking
- Automated analytical summaries

---

# Project Status

**Portfolio Project — Active Development**

The current implementation represents the completed analytical dashboard and supporting data transformation work. Additional automation and analytical capabilities may be added as the project evolves.

---

## Author

**Tessa Becker**  
**Kronos Intelligence**

*Where Data Designs Better Decisions.*
