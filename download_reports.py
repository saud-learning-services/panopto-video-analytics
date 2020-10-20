from report_builder.ReportBuilder import ReportBuilder
import settings
from pprint import pprint
from datetime import datetime

report_builder = ReportBuilder(
    settings.HOST, settings.USERNAME, settings.PASSWORD)

# DELIVERY ID - hardcoded Alison's test video
delivery_id = '84cef7f7-f168-4a80-9a5a-ac100144db29'


# detailed info about every unique view
# These two calls return the same amount of records - just first one has more detail about play/pause

# Gets a dataframe of detailed viewing data
session_views_df = report_builder.get_session_extended_details(
    session_id=delivery_id)

# Same records as above but in JSON and no play/pause data
session_details = report_builder.get_session_details(session_id=delivery_id)


# Shows views by specified level of granularity
# Hourly, Daily...
session_usage_summary = report_builder.get_session_usage_summary(
    session_id=delivery_id)


# Get datetime now as string to timestamp CSVs
now = datetime.now()
format = '%d-%m-%Y %H.%M.%S'
datetime_string = now.strftime(format)

# output the detailed session views dataframe to CSV
session_views_df.to_csv(
    f'data/session_views_{datetime_string}.csv', index=False)
