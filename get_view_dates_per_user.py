from report_builder.ReportBuilder import ReportBuilder
from panopto_rest_api.panopto_oauth2 import PanoptoOAuth2
from panopto_rest_api.panopto_interface import Panopto
import settings
import pandas as pd
from pprint import pprint
from datetime import datetime
from termcolor import cprint

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


alisons_id = '84cef7f7-f168-4a80-9a5a-ac100144db29'
# COMM290_id = 'f5fde953-e41b-4303-b76f-ac5c0129e031'

# Sep28HelpSessionRecording.COMM290
# COMM290_id = '20ddb30e-a362-4604-b162-ac45012627bc'

# 3-3.ClassRecording.COMM290.2020W1
COMM290_id = '9cfb9b7c-3b17-4aa6-8a9b-ac540125b5a3'

sid = COMM290_id

session = panopto_rest.get_session(session_id=sid)

# rounding down to the nearest second seems to match the total time displayed on the Panopto UI
duration = session['Duration']
print()
cprint(session['Name'], 'green')
# print(duration)

# 5% chunks
chunk_duration = duration / 20
# print(chunk_duration)

chunks = []
prev_upper_bound = 0
for i in range(20):

    chunk_start = prev_upper_bound

    chunk_end = chunk_start + chunk_duration

    if chunk_end > duration:
        chunk_end = duration

    chunk = {
        'session_id': sid,
        'chunk_index': i,
        'chunk_start': chunk_start,
        'chunk_end': chunk_end,
        'unique_views': 0,
        # 'chunk_id': sid + '-' + str(i)
    }

    prev_upper_bound = chunk_end
    chunks.append(chunk)

df = report_builder.get_viewing_details(session_id=sid)

# for testing purposes uncomment
# df = pd.read_csv('tests/test.csv')

# get a list of unique user id's from the dataframe
user_ids = list(df['UserId'])
filtered = list(dict.fromkeys(user_ids))

cprint('Unique Viewers: ' + str(len(filtered)), 'blue')

table_2_data = []

# for every unique user id
for user_id in filtered:
    # select the rows that correlate to that user
    user_views = df.loc[df['UserId'] == user_id]

    dates = list(user_views['Date'])
    filtered_dates = list(dict.fromkeys(dates))

    cprint(user_id, 'yellow')
    cprint(filtered_dates, 'blue')

    continue
