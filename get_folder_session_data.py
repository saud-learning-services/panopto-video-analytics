from report_builder.ReportBuilder import ReportBuilder
from panopto_rest_api.panopto_oauth2 import PanoptoOAuth2
from panopto_rest_api.panopto_interface import Panopto
import settings
import pandas as pd
from pprint import pprint
from datetime import datetime
import sys
import os


# SOAP API Initialization
report_builder = ReportBuilder(settings.HOST,
                               settings.USERNAME,
                               settings.PASSWORD)

# REST API Initialization
oauth2 = PanoptoOAuth2(settings.SERVER,
                       settings.CLIENT_ID,
                       settings.CLIENT_SECRET,
                       True)
panopto_rest = Panopto(settings.SERVER, True, oauth2)


# COMM 290 [Hardcoded]
folder_id = '55a90663-2a10-43ed-a351-ac2a016cf839'
folder_data = panopto_rest.get_folder(folder_id=folder_id)
folder_name = folder_data['Name']

output_folder_path = settings.ROOT + f'/data/{folder_name}'
os.mkdir(output_folder_path)
os.mkdir(output_folder_path + '/Session Viewing Details')

# Get a list of sessions in the given folder
# For some strange reason these do not themselves contain many of the
# URL's we're looking for so we do an individual get_session call for each
# TODO see if you can fix this because it makes it VERY VERY slow @markoprodanovic
sessions = panopto_rest.get_sessions(folder_id=folder_id)

session_ids = list(map(lambda session: session['Id'], sessions))

# Build out sessions_sumary.csv table
columns = ['SessionID',
           'SessionName',
           'Description',
           'Duration',
           'EmbedURL',
           'FolderId',
           'FolderName']

data = []

for sid in session_ids:
    session = panopto_rest.get_session(session_id=sid)
    print('Getting data for Session: {}'.format(session['Name']))
    row = {
        'SessionID': session['Id'],
        'SessionName': session['Name'],
        'Description': session['Description'],
        'Duration': session['Duration'],
        'EmbedURL': session['Urls']['EmbedUrl'],
        'FolderId': session['FolderDetails']['Id'],
        'FolderName': session['FolderDetails']['Name']
    }

    # append above row to the summary table
    data.append(row)

    # get session viewing details (as DataFrame)
    session_views_df = report_builder.get_viewing_details(session_id=sid)

    # output viewing details
    filename = session['Name'] + '_' + session['Id'] + '.csv'
    output_path = output_folder_path + f'/Session Viewing Details/{filename}'
    session_views_df.to_csv(output_path, index=False)

session_summary_df = pd.DataFrame(data=data, columns=columns)

session_summary_df.to_csv(
    output_folder_path + '/sessions_summary.csv', index=False)

print('successfully generated session_summary.csv')
