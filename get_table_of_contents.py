from panopto_rest_api.panopto_oauth2 import PanoptoOAuth2
from panopto_rest_api.panopto_interface import Panopto
import settings
import pandas as pd
from pprint import pprint
import sys

# REST API Initialization
oauth2 = PanoptoOAuth2(settings.SERVER,
                       settings.CLIENT_ID,
                       settings.CLIENT_SECRET,
                       True)
panopto_rest = Panopto(settings.SERVER, True, oauth2)

# Put Delivery ID here
session_id = 'PASTE ID HERE'

session = panopto_rest.get_session(session_id=session_id)

timestamps = panopto_rest.get_timestamps(session_id)

timestamps_df = pd.DataFrame(timestamps)

session_name = session['Name']
path = f'{settings.ROOT}/data/{session_name}_TOC.csv'
timestamps_df.to_csv(path, index=False)
