## 🌏 Make an environment

```
HOST = ubc.ca.panopto.com
USERNAME = {panopto-username}
PASSWORD = {panopto-password}

SERVER = ubc.ca.panopto.com
CLIENT_ID = {panopto-api-client-id}
CLIENT_SECRET = {panopto-api-client-secret}

ASPXAUTH = {.ASPXAUTH-token-found-in-cookies}
```

## ⭐️ To Run

- setup environment from `environment.yml`
- `conda activate panopto-data-api`
- `python download_reports.py`
  - at the moment this will create a timestamped CSV with detailed session viewing data in the `/data` directory
  - Note it is currently hardcoded to get the last 30 days of data with a page size of 25 records (increase this size if working with larger courses however it will always fetch ALL records)
- `python get_folder_session_data.py`
  - gets session view and session summary data for all sessions in folder = folder_id
  - hardcoded folder id

#### outputs

    .
    ├── <Folder Name>
    │   ├── sessions_summary.csv
    │   └── Session Viewing Details
    │       ├──<Session Name>_<Session ID>.csv
    │       └── ...

- `test_get_timestamps.py` sandbox environment to testing timestamp data response JSON (specify session by delivery_id)
