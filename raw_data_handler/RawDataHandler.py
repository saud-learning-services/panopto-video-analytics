from panopto_soap_api.AuthenticatedClientFactory import AuthenticatedClientFactory
from panopto_rest_api.panopto_oauth2 import PanoptoOAuth2
from panopto_rest_api.panopto_interface import Panopto
from datetime import datetime, timedelta
from progress.spinner import Spinner
from termcolor import cprint
import pandas as pd
import settings
import time
import os


class RawDataHandler():
    '''
    A class that deals with all fetching and storing of raw viewing data from Panopto
    Reads from the API's and writes to Database (currently CSVs)
    '''

    @staticmethod
    def __add_fields(record):
        '''
        Adds a column for Date (no time)
        Adds column for Stop Position
        '''
        record['Date'] = record['Time'].date()

        stop_position = record['StartPosition'] + record['SecondsViewed']
        record['StopPosition'] = stop_position

        return record

    def __init__(self):
        '''
        Initializes the SOAP and REST clients for making calls
        Sets the UsageReporting Client from SOAP as well
        '''

        # SOAP API
        self.soap_interface = AuthenticatedClientFactory(settings.SERVER,
                                                         settings.USERNAME,
                                                         settings.PASSWORD,
                                                         verify_ssl=True)
        self.usage_client = self.soap_interface.get_client('UsageReporting')

        # REST API
        oauth2 = PanoptoOAuth2(settings.SERVER,
                               settings.CLIENT_ID,
                               settings.CLIENT_SECRET,
                               True)
        self.rest_interface = Panopto(settings.SERVER, True, oauth2)

    def update_database(self):
        '''
        Public method to fetch Panopto viewing data and commit to the database
        '''

        courses_path = settings.ROOT + '/courses.csv'
        state_path = settings.ROOT + '/raw_data_handler/' + 'state.csv'
        courses = pd.read_csv(courses_path)
        state = pd.read_csv(state_path)

        folder_ids_to_run = list(courses['PanoptoFolderID'])
        folder_ids_already_run = list(state['PanoptoFolderID'])
        for fid in folder_ids_to_run:
            folder_name = self.rest_interface.get_folder(
                folder_id=fid)['Name']
            if fid in folder_ids_already_run:
                # get the beginRange from the state
                row = state.loc[state['PanoptoFolderID'] == fid].iloc[0]
                last_fetched = datetime.fromisoformat(
                    row['LastDateFetched(UTC)'] + ' 23:59:59')

                # if the data has been updated in the last 24 utc hours, it doesn't need to be fetched again
                if last_fetched >= datetime.utcnow() - timedelta(days=1):
                    print(
                        '\n⚠️  ' + folder_name + ' data is already up-to-date => up to ' + str(last_fetched) + ' UTC ⚠️')
                    continue

                one_second = timedelta(seconds=1)
                begin_range = last_fetched + one_second
            else:
                # starts Sept 01 2020 at 12:00am
                begin_range = datetime.fromisoformat('2020-09-01 00:00:00')

            utcnow_date = datetime.utcnow().date()
            one_day = timedelta(days=1)
            day_prior = utcnow_date - one_day
            end_of_day = datetime.max.time()
            end_range = datetime.combine(day_prior, end_of_day)

            all_videos_overview_df = self.__get_videos_overview(fid)
            viewing_data_df = self.__get_folder_viewing_data(fid,
                                                             begin_range,
                                                             end_range)

            database_path = settings.ROOT + '/database'
            target = database_path + f'/{folder_name}[{fid}]'

            if not os.path.isdir(target):
                os.mkdir(target)

            if fid in folder_ids_already_run and os.path.isdir(target):
                saved_viewing_data_df = pd.read_csv(
                    f'{target}/viewing_activity.csv')
                viewing_data_df = pd.concat(
                    [viewing_data_df, saved_viewing_data_df], ignore_index=True)

                # empty the target folder contents
                os.remove(f'{target}/videos_overview.csv')
                os.remove(f'{target}/viewing_activity.csv')

                # update entry in state
                state.loc[state['PanoptoFolderID'] == fid, [
                    'LastDateFetched(UTC)']] = end_range.date().isoformat()
            else:
                # add new entry to state
                entry = {
                    'PanoptoFolderName': folder_name,
                    'PanoptoFolderID': fid,
                    'LastDateFetched(UTC)': end_range.date().isoformat()
                }
                state = state.append(entry, ignore_index=True)

            all_videos_overview_df.to_csv(
                f'{target}/videos_overview.csv', index=False)
            viewing_data_df.to_csv(
                f'{target}/viewing_activity.csv', index=False)

            state.to_csv(state_path, index=False)

    def __get_videos_overview(self, folder_id):
        '''
        Creates a table (df) summarizing all the videos in the given folder
        '''

        sessions = self.rest_interface.get_sessions(folder_id=folder_id)
        time.sleep(1)

        columns = ['FolderId',
                   'FolderName',
                   'SessionID',
                   'SessionName',
                   'Description',
                   'Duration']

        data = []
        for session in sessions:
            row = {
                'FolderId': session['FolderDetails']['Id'],
                'FolderName': session['FolderDetails']['Name'],
                'SessionID': session['Id'],
                'SessionName': session['Name'],
                'Description': session['Description'],
                'Duration': session['Duration']
            }

            data.append(row)

        return pd.DataFrame(data=data, columns=columns)

    def __get_folder_viewing_data(self, folder_id, begin_range, end_range):
        '''
        Gets all the viewing data for all sessions within a folder
        Stiches all the session viewing data into a single CSV
        '''

        sessions = self.rest_interface.get_sessions(folder_id=folder_id)

        columns = ['SessionId',
                   'UserId',
                   'Date',
                   'Time',
                   'PlaybackSpeed',
                   'StartPosition',
                   'StartReason',
                   'StopPosition',
                   'StopReason',
                   'SecondsViewed']

        folder_viewing_data = []
        for session in sessions:
            session_name = session['Name']
            print('\n 🔁 Fetching viewing data for video...')
            cprint(' 🎬 ' + session_name, 'green')
            cprint(f' 🕙 From: {begin_range}', 'yellow')
            cprint(
                f' 🕙 To: {end_range.strftime("%Y-%m-%d %H:%M:%S")}', 'yellow')
            session_viewing_data = self.__get_session_viewing_data(session['Id'],
                                                                   begin_range,
                                                                   end_range)
            folder_viewing_data = [*folder_viewing_data, *session_viewing_data]

        return pd.DataFrame(data=folder_viewing_data, columns=columns)

    def __get_session_viewing_data(self, session_id, begin_range, end_range):
        '''
        Calls the "UsageReporting.GetSessionExtendedDetailedUsage" method
        Gets all records by iterating through all pages
        Adds/renames several columns and converts to dataframe
        '''

        page_size = 150
        page_num = 0

        records = []
        records_remaining = None

        spinner = Spinner(' ⏳ ')
        while True:
            if records_remaining is not None and records_remaining <= 0:
                break

            resp = self.usage_client.call_service(
                'GetSessionExtendedDetailedUsage',
                sessionId=session_id,
                pagination={'MaxNumberResults': page_size,
                            'PageNumber': page_num},
                beginRange=begin_range,
                endRange=end_range)

            # if the response has no viewing data just skip it
            if resp['TotalNumberResponses'] == 0:
                break

            page_of_data = resp['PagedResponses']['ExtendedDetailedUsageResponseItem']

            if len(page_of_data) > 0:
                records = [*records, *page_of_data]
                records_remaining = resp['TotalNumberResponses'] - \
                    (page_size * (page_num + 1))

            page_num += 1

            spinner.next()

        print('')
        records = list(map(self.__add_fields, records))

        return records
