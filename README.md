# Panopto Viewing Data API

An interface for getting viewing data from Panopto sessions. Specify Panopto folders in `courses.csv` to add them to the database.

There are two independent parts to this project:

### Updating the Database

- run by calling `$ python update_database.py`
- will grab viewing data from each folder on Panopto specified in `courses.csv`
- will add a few additional columns and save data to the database directory
- this part of the project manages its own state so it will only grab data that it doesn't already have, up to the most recent complete UTC date - ie. if it has up to Jan 5 11:59pm UTC and you run it on January 10th at 4pm UTC, it will grab data till Jan 9th 11:59 UTC (the last full date of viewing)
- if a script is being run from the first time the tool will grab all viewing data from Sept 1 2020

### Outputting Chunked Data

- run by calling `$ python output_chunked_data.py`
- this independent part of the project isn't concerned with data on Panopto, but what it already has recorded in the `database` directory
- it will read each folder of data in the database and apply transformations and output to a folder with the same title in `output[CHUNKED]`

## 🌏 Make an environment

```
SERVER = ubc.ca.panopto.com

USERNAME = {panopto-username}
PASSWORD = {panopto-password}

CLIENT_ID = {panopto-api-client-id}
CLIENT_SECRET = {panopto-api-client-secret}

ASPXAUTH = {.ASPXAUTH-token-found-in-cookies}
```

To find your .ASPXAUTH token, login to Panopto using Chrome, go to dev-tools -- Command + Option + J (Mac) or Control + Shift + J (Windows, Linux, Chrome OS) -- under the Application tab, click the URL under Cookies, then copy the value next to .ASPXAUTH

#### Output structure of database

For each (course) panopto folder specified in courses.csv, `database` will have after running `update_database.py`:

    .
    ├── <Folder Name>[<Folder ID>]
    │   ├── videos_overview.csv
    │   └── viewing_activity.csv

#### Output structure of output[CHUNKED]

For each course in the database, `output[CHUNKED]` will contain the following after running `output_chunked_data.py`:

    .
    ├── <Folder Name>[<Folder ID>]
    │   ├── chunked_data.csv
    │   └── session_overview.csv

#### Tableau

> TODO: The action that allows you to click through the COURSE OVERVIEW to the VIDEO OVERVIEW is having issues and has been removed for now ⚠️

Perform the following join with the data output by `output_chunked_data.py`:

<div align="center">
    <img src="_imgs/tableau-join.png" alt="join" width="600">
</div>
