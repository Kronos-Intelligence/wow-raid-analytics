# Power BI Data Model

This document describes the data model used for the World of Warcraft Raid Analytics Power BI dashboard.

The model combines prepared analytical datasets with dimensional and supporting tables created within Power BI. The structure allows the dashboard to move from high-level raid analysis to detailed fight, player, and ability-level analysis.

---

## Model Architecture

The project follows this general architecture:

```text
World of Warcraft Combat Logs
            |
            v
      Python Processing
            |
            v
     Validated Analytical Data
            |
            v
       Power BI Data Model
            |
      +-----+-----+-----+
      |           |     |
      v           v     v
   Raid/Fight   Player  Event
     Data       Data    Data
      |           |       |
      +-----------+-------+
                  |
                  v
          Power BI Measures
                  |
                  v
          Interactive Dashboard
