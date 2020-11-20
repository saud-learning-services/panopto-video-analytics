# Panopto Session Views Workbook

> Version: 0.4.0

## Summary

This workbook is designed to give faculty members an overview of viewing activity in their Panopto videos. This workbook includes two dashboards **COURSE OVERVIEW** and **SESSION OVERVIEW** which offer course-level and session-level visualizations respectively.

## Getting Started

To begin, please ensure you are connected to the UBC network (via VPN if remote). After connecting, you'll be able to access a specific workbook with your course data on Tabluea Server https://reports.sauder.ubc.ca/.

[COMM 290](https://reports.sauder.ubc.ca/#/site/Sauder/workbooks/3954/views)

[COMM 293](https://reports.sauder.ubc.ca/#/site/Sauder/workbooks/3956/views)

Once you have opened the notebook, we recommend starting with the **COURSE OVERVIEW**.

You can navigate between dashboards using the tabs at the top of the page. Alternatively, while in the **COURSE OVERVIEW** dashboard, you can select a video of interest and automatically be taken to the **SESSION OVERVIEW** dashboard for that video.

## COURSE OVERVIEW

The **COURSE OVERVIEW** dashboard displays a grid, each cell representing a session in the given course folder. For each session, the following properties will be visible:

- **Session Name**: session title on panopto
- **Unique Views**: count of unique viewers who have accessed the video
- **Total Viewing Time**: the total amount of time spent watching the video across all viewers

Hovering over a cell will show viewing activity across time.

Clicking on a cell will open the **SESSION OVERVIEW** dashboard with that course selected. In other words, click for more detailed viewing info about a session.

## SESSION OVERVIEW

The **SESSION OVERVIEW** dashboard shows viewing activity across "chunks". Each chunk represents 5% of the video timeline (20 chunks). The dashboard combines several visualizations:

- **Unique Views**: count of unique viewers who have accessed the video
- **Viewers Across Chunks (5% intervals)**
  - The blue line represents the total number of unique viewers who have watched _some_ of the chunk
  - The red line represents the total number of unique viewers who have "completed" the chunk (i.e. watched at least 75% of it)
- **Avg. Viewing Time Across Chunks (mins)**: average amount of time spent in each chunk (in minutes)
- **Chunk Info**: Table that shows the start and end time for each chunk (in minutes)

There is a dropdown menu in the top-right corner for selecting a different session. Or the same thing can be done by clicking on a session in the **COURSE OVERVIEW** table.

The **Date Range Selector** let's you define a range of dates to show in the visualizations.
