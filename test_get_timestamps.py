from panopto_rest_api.panopto_oauth2 import PanoptoOAuth2
from panopto_rest_api.panopto_interface import Panopto
import settings
from pprint import pprint

# REST API Initialization
oauth2 = PanoptoOAuth2(settings.SERVER,
                       settings.CLIENT_ID,
                       settings.CLIENT_SECRET,
                       True)
panopto_rest = Panopto(settings.SERVER, True, oauth2)

# Put Delivery ID here
session_id = '39bbd4a6-ba70-46f3-8541-ac58012f95e9'

timestamps = panopto_rest.get_timestamps(session_id)

pprint(timestamps)
