from panopto_rest_api.panopto_interface import Panopto
from panopto_rest_api.panopto_oauth2 import PanoptoOAuth2
import settings

# REST API
oauth2 = PanoptoOAuth2(settings.SERVER,
                       settings.CLIENT_ID,
                       settings.CLIENT_SECRET,
                       True)
rest_interface = Panopto(settings.SERVER, True, oauth2)

# Paste a panopto folder ID here (as string)
FOLDER_ID = 'abcd-0000'
results = rest_interface.get_subfolder_ids(FOLDER_ID)

print(results)
