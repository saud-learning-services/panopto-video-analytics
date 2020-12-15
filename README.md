# Panopto Video Analytics Data API

An interface for getting viewing data from Panopto sessions. Specify Panopto folders in `courses.csv` to add them to the database.

## 🌏 Make an environment

```
HOST_URL = ubc.ca.panopto.com
USERNAME = {panopto-username}
PASSWORD = {panopto-password}

SERVER = ubc.ca.panopto.com
CLIENT_ID = {panopto-api-client-id}
CLIENT_SECRET = {panopto-api-client-secret}

ASPXAUTH = {.ASPXAUTH-token-found-in-cookies}
```

#### Output structure of database

For each (course) panopto folder specified in courses.csv, `database` will have

    .
    ├── <Folder Name>[<Folder ID>]
    │   ├── videos_overview.csv
    │   └── viewing_activity.csv
