# Panopto Video Analytics

> Version: 0.6.0

## Summary

This collection of dashboards is designed to give faculty an overview of viewing activity in their Panopto videos. This is done through two views **COURSE OVERVIEW** and **VIDEO OVERVIEW** which offer course-level and video-level data/visualizations respectively.

## Definitions

- Note that Panopto refers to videos as "sessions". For clarity, we will refer to them as **videos** throughtout the rest of this documentation and the within the dashboards themselves.
- We will use the words **cover** and **coverage** to refer to the amount of a video's content a viewer has seen. So if I watched 0:00-0:10 today and 0:05-0:30 tomorrow, my total video coverage would be 0:00-0:30 (i.e. the video content I've seen).

## Getting Started

To begin, please ensure you are connected to the UBC network (via VPN if remote). After connecting, you'll be able to access a specific workbook with your course data on Tabluea Server https://reports.sauder.ubc.ca/.

[COMM 290](https://reports.sauder.ubc.ca/#/site/Sauder/workbooks/3954/views)

[COMM 293](https://reports.sauder.ubc.ca/#/site/Sauder/workbooks/3956/views)

Once you have opened the notebook, we recommend starting with the **COURSE OVERVIEW**.

You can navigate between dashboards using the tabs at the top of the page. While in the **COURSE OVERVIEW** dashboard, you can select a video of interest to reveal the option to **See VIDEO OVERVIEW for this video**

## COURSE OVERVIEW

The **COURSE OVERVIEW** dashboard displays course-level details.

Top 5 video's are shown in two lists on the top-left of the dashbaord. One list ranks top videos based on **unique views** and the other uses **% of unique viewers who've watched >= 75%**.

A chart representing viewers across time is shown in the top-right.

All video contained in the Panopto course folder are shown in a grid. Under "Select Grid View" you, can specify the type of visualization to use to compare and distinguish videos.

You can adjust the parameter that is used to determine the color intensity of the heatmap using the dropdown menu.

### Hover over a cell to see:

- **Unique viewers**: count of unique viewers who have accessed the video (Panopto determines uniqueness - we cannot verify the accuracy of unique viewers, however it should be treated as a estimate of student viewership and not an exact figure)
- **Unique viewers who’ve covered at least 75% (entire video)**: count of unique viewers who've covered 75% or more of the video
- **Duration**: The duration of the video expressed in HH:MM:SS
- **Total Watch Time**: the total amount of time spent watching the video across all viewers

Clicking on a cell will reveal the option to **See VIDEO OVERVIEW for this video**

## VIDEO OVERVIEW

The **VIDEO OVERVIEW** dashboard shows video stats and viewing activity across **chunks**. Each chunk represents 5% of the video timeline (20 chunks). The dashboard has several components:

- **Unique viewers**
- **Duration**
- **Total watch time**
- **Unique viewers who’ve covered at least 75% (entire video)**

... as defined in the **COURSE OVERVIEW** section

- **Viewers Across Time**: a chart showing the number of unique viewers across days
- **Viewers Across Chunks (5% intervals)**
  - The **blue line** represents the number of unique viewers who have watched _some_ of the chunk
  - The **red line** represents the number of unique _viewers who have've covered at least 75% (chunk)_ - Note that unlike the **Viewers who've covered at least 75% (entire video)**, this is specific to the chunk and not the entire video
- **Avg. Viewing Time Across Chunks**: average amount of time viewers spent in each chunk (in HH:MM:SS)

There is a dropdown menu in the top-right corner for selecting different videos.

The **Date Range Selector** on the top right lets you define a range of dates to include in the dashboards. By adjusting your range, you'll adjust the visualizations to reflect only those dates of viewing. This doesn't apply to the **Viewers who've covered at least 75%** stat or the **Duration** stat.
