from report_builder.ReportBuilder import ReportBuilder
from panopto_rest_api.panopto_oauth2 import PanoptoOAuth2
from panopto_rest_api.panopto_interface import Panopto
import settings
import pandas as pd
from pprint import pprint
from datetime import datetime

report_builder = ReportBuilder(
    settings.HOST, settings.USERNAME, settings.PASSWORD)

# DELIVERY ID - hardcoded Alison's test video
# delivery_id = '84cef7f7-f168-4a80-9a5a-ac100144db29'
delivery_id = 'ef62eef6-b2ae-474f-a333-ac5901232c1a'


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
# session_views_df.to_csv(
#     f'data/session_views_{datetime_string}.csv', index=False)

## TESTING REST API ###

oauth2 = PanoptoOAuth2(settings.SERVER,
                       settings.CLIENT_ID,
                       settings.CLIENT_SECRET,
                       True)

panopto = Panopto(settings.SERVER, True, oauth2)

session = panopto.get_session(session_id=delivery_id)

session_data = {
    'SessionID': session['Id'],
    'SessionName': session['Name'],
    'Description': session['Description'],
    'Duration': session['Duration'],
    'EmbedURL': session['Urls']['EmbedUrl'],
    'FolderId': session['FolderDetails']['Id'],
    'FolderName': session['FolderDetails']['Name']
}

session_df = pd.DataFrame([session_data])

session_df.to_csv(
    f'data/session_overview_{datetime_string}.csv', index=False)
