import os
import logging
import json
import copy
import time
import settings
import requests
import pprint as pp


class Panopto:
    '''
    Main interface for doing anything Panopto related

    MODIFIED VERSION OF: https://github.com/Panopto/upload-python-sample/tree/master/simplest
    Contributors (GitHub): Hiroshi Ohno, Zac Rumford
    Apache-2.0 License

    *modified to suit our specific use-case*
    '''

    def __init__(self, server, ssl_verify, oauth2):
        '''
        Constructor of uploader instance.
        This goes through authorization step of the target server.
        '''
        self.server = server
        self.ssl_verify = ssl_verify
        self.oauth2 = oauth2
        self.current_token = None

        # Use requests module's Session object in this example.
        # This is not mandatory, but this enables applying the same settings (especially
        # OAuth2 access token) to all calls and also makes the calls more efficient.
        # ref. https://2.python-requests.org/en/master/user/advanced/#session-objects
        self.requests_session = requests.Session()
        self.requests_session.verify = self.ssl_verify

        self.__setup_or_refresh_access_token()

    def __setup_or_refresh_access_token(self):
        '''
        This method invokes OAuth2 Authorization Code Grant authorization flow.
        It goes through browser UI for the first time.
        It refreshes the access token after that and no user interfaction is requetsed.
        This is called at the initialization of the class, as well as when 401 (Unaurhotized) is returend.
        '''
        access_token = self.oauth2.get_access_token_authorization_code_grant()
        self.requests_session.headers.update(
            {'Authorization': 'Bearer ' + access_token})
        self.current_token = access_token

    def __inspect_response_is_retry_needed(self, response):
        '''
        Inspect the response of a requets' call.
        True indicates the retry needed, False indicates success. Othrwise an exception is thrown.
        Reference: https://stackoverflow.com/a/24519419

        This method detects 403 (Forbidden), refresh the access token, and returns as 'is retry needed'.
        This example focuses on the usage of upload API and OAuth2, and any other error handling is not implemented.
        Prodcution code should handle other failure cases and errors as appropriate.
        '''
        if response.status_code // 100 == 2:
            # Success on 2xx response.
            return False

        if response.status_code == requests.codes.forbidden:
            print('Forbidden. This may mean token expired. Refresh access token.')
            logging.error(
                'Forbidden. This may mean token expired. Refresh access token.')
            self.__setup_or_refresh_access_token()
            return True

        # Throw unhandled cases.
        response.raise_for_status()

    def get_session(self, session_id):
        '''
        Call GET /api/v1/sessions/{id} API and return the response
        '''
        while True:
            url = 'https://{0}/Panopto/api/v1/sessions/{1}'.format(
                self.server, session_id)
            resp = self.requests_session.get(url=url)
            if self.__inspect_response_is_retry_needed(resp):
                continue
            data = resp.json()
            break
        return data

    def get_timestamps(self, session_id):
        '''
        Return timestamps (table of contents) in JSON format for specific session
        '''

        self.requests_session.headers.update(
            {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1 Safari/605.1.15',
             'Content-Type': 'video/mp4'})
        self.requests_session.cookies = requests.utils.cookiejar_from_dict(
            {'.ASPXAUTH': settings.ASPXAUTH})

        url = f'https://{settings.SERVER}/Panopto/Pages/Viewer/DeliveryInfo.aspx'
        params = {
            "deliveryId": session_id,
            "responseType": "json"
        }
        resp = self.requests_session.post(url=url, params=params)

        if resp.status_code != 200:
            raise RuntimeError(
                f'DeliveryInfo response came with status code {resp.status_code}\nCheck ASPXAUTH token.')

        delivery_info = json.loads(resp.text)
        if 'ErrorMessage' in delivery_info.keys():
            message = delivery_info['ErrorMessage']
            raise RuntimeError(
                f'DeliveryInfo response came with message: {message}\nCheck ASPXAUTH token.')

        return delivery_info['Delivery']['Timestamps']

    def get_folder(self, folder_id):
        '''
        Call GET /api/v1/folders/{id} API and return the response
        '''
        while True:
            url = 'https://{0}/Panopto/api/v1/folders/{1}'.format(
                self.server, folder_id)
            resp = self.requests_session.get(url=url)
            if self.__inspect_response_is_retry_needed(resp):
                continue
            data = resp.json()
            break
        return data

    def get_child_folders(self, folder_id):
        while True:
            url = 'https://{0}/Panopto/api/v1/folders/{1}/children'.format(
                self.server, folder_id)
            resp = self.requests_session.get(url=url)
            if self.__inspect_response_is_retry_needed(resp):
                continue
            data = resp.json()
            break
        return data

    def get_sessions(self, folder_id):
        page_number = 0
        data = []
        while True:
            url = 'https://{0}/Panopto/api/v1/folders/{1}/sessions'.format(
                self.server, folder_id)
            time.sleep(0.2)
            resp = self.requests_session.get(
                url=url, params={'pageNumber': str(page_number)})
            if self.__inspect_response_is_retry_needed(resp):
                continue
            # analyze response for data coming back
            if resp.status_code == 200:
                data_chunk = resp.json()
                # print('LENGTH: ' + str(len(data_chunk['Results'])))
                if len(data_chunk['Results']) > 0:
                    data = data + data_chunk['Results']
                    page_number += 1
                    continue
            break
        return data

    def get_containing_folder(self, delivery_id):
        '''
        Given a sessions delivery_id, make the necessary calls to get its folder id
        '''

        session = self.get_session(delivery_id)
        details = session['FolderDetails']

        folder_id = details['Id']
        folder_name = details['Name']

        return (folder_name, folder_id)

    def __enumerate_files(self, folder):
        '''
        Return the list of files in the specified folder. Not to traverse sub folders.
        '''
        print('')
        files = []
        for entry in os.listdir(folder):
            path = os.path.join(folder, entry)
            if os.path.isdir(path):
                continue
            files.append(path)
            print('  {0}'.format(path))

        return files
