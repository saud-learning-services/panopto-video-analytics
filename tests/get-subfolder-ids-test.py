from panopto_rest_api.panopto_interface import Panopto
from panopto_rest_api.panopto_oauth2 import PanoptoOAuth2
import settings

# REST API
oauth2 = PanoptoOAuth2(settings.SERVER,
                       settings.CLIENT_ID,
                       settings.CLIENT_SECRET,
                       True)
rest_interface = Panopto(settings.SERVER, True, oauth2)

results = rest_interface.get_subfolder_ids(
    'b8f6a68e-60fd-4f74-9939-ac250158ef28')

print(results)
