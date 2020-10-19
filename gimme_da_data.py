from report_builder.ReportBuilder import ReportBuilder
import settings
import pandas as pd
from pprint import pprint

report_builder = ReportBuilder(settings.HOST, settings.USERNAME, settings.PASSWORD)

# DELIVERY ID SHOULD GO HERE
alison_session_id = '84cef7f7-f168-4a80-9a5a-ac100144db29'
# alison_session_id = '8740b73e-094b-4793-85ca-ac5701643875'


# detailed info about every unique view
# These two calls return the same amount of records - just first one has more detail about play/pause
extended_session_details = report_builder.get_session_extended_details(session_id=alison_session_id)
session_details = report_builder.get_session_details(session_id=alison_session_id)

# [DOESN'T WORK] can't just get usage details for any user id in the above calls
# (maybe you'd need a Panopto account for this one)
# extended_usage_details = report_builder.get_usage_details(user_id='9f6f58cd-e9ef-4062-9387-ac45015afcf7')

# session_usage_summary = report_builder.get_session_usage_summary(session_id=alison_session_id)

# pprint(extended_session_details)

data = extended_session_details['PagedResponses']['ExtendedDetailedUsageResponseItem']

df = pd.DataFrame(data)

df.to_csv('alison-test-video-session-details.csv', index=False)
