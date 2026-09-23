**# Project Documentation

This folder contains the technical documentation for the World of Warcraft Raid Analytics project.

The documentation describes the analytical datasets, Power BI data model, and relationships between the data-preparation pipeline and the final dashboard.

## Documentation

### Data Dictionary

The [Data Dictionary](data_dictionary.md) documents the primary analytical datasets used in the project, including player performance, fight information, damage, healing, deaths, interrupts, and dispels.

### Data Model

The [Data Model](data_model.md) describes how the analytical datasets and Power BI-created dimension tables are organized and used within the Power BI model.

## Project Architecture

The overall project follows this analytical workflow:

```text
World of Warcraft Combat Logs
            ↓
      Python Processing
            ↓
   Validation & Transformation
            ↓
      Analytical CSV Data
            ↓
        Power BI Model
            ↓
     Interactive Dashboard**
