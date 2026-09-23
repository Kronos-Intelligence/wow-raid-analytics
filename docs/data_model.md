# Power BI Data Model

This document describes the data model used for the **World of Warcraft Raid Analytics** Power BI dashboard.

The model combines cleaned analytical datasets prepared through Python with dimensional and supporting tables created directly within Power BI. This structure allows the dashboard to move from high-level raid analysis into detailed fight, player, and ability-level analysis.

---

## Model Architecture

The project follows this general analytical pipeline:

```text
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
      +-----+-----+------+
      |           |      |
      v           v      v
   Fight Data  Player   Event Data
                Data
      |           |      |
      +-----------+------+
                  |
                  v
          Power BI Measures
                  |
                  v
        Interactive Dashboard
