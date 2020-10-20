
## 🌏 Make an environment
```
HOST = ubc.ca.panopto.com
USERNAME = {panopto-username}
PASSWORD = {panopto-password}
```

## ⭐️ To Run
* setup environment from `environment.yml`
* `conda activate panopto-data-api`
* `python download_reports.py`
    * at the moment this will create a timestamped CSV with detailed session viewing data in the `/data` directory
    * Note it is currently hardcoded to get the last 30 days of data with a page size of 25 records (increase this size if working with larger courses  however it will always fetch ALL records)