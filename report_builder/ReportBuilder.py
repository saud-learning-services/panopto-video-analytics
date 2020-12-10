from panopto_soap_api.AuthenticatedClientFactory import AuthenticatedClientFactory
from datetime import datetime, date, timedelta
from pprint import pprint
import pandas as pd


class ReportBuilder:

    @staticmethod
    def _add_fields(record):
        record['Date'] = record['Time'].date()
        record['StopPosition'] = record['StartPosition'] + \
            record['SecondsViewed']
        return record

    def __init__(self, host, username, password):
        self.host = host
        self.username = username
        self.password = password

        # authorization
        self.auth = AuthenticatedClientFactory(
            host, username, password, verify_ssl=True)
        self.usage_client = self.auth.get_client('UsageReporting')

    def get_viewing_details(self, session_id):
        '''
        Calls the "UsageReporting.GetSessionExtendedDetailedUsage" method
        Gets all records by iterating through all pages
        Adds/renames several columns and converts to dataframe
        Returns the df
        '''

        # Variables to get the last 30 days of data
        now = datetime.now()
        sept = date(2020, 9, 1)
        # last_month = now - timedelta(days=30)

        page_size = 150
        page_num = 0

        records = []

        # initialize to 500 (any positive int will do)
        # this will help us keep count for pagination
        records_remaining = 500

        while True:
            if records_remaining <= 0:
                break

            resp = self.usage_client.call_service(
                'GetSessionExtendedDetailedUsage',
                sessionId=session_id,
                pagination={'MaxNumberResults': page_size,
                            'PageNumber': page_num},
                beginRange=sept,
                endRange=now)

            # if the response has no viewing data just skip it
            # TODO: should there be a CSV even if there are no views?
            if resp['TotalNumberResponses'] == 0:
                break

            chunk = resp['PagedResponses']['ExtendedDetailedUsageResponseItem']

            if len(chunk) > 0:
                records = [*records, *chunk]
                records_remaining = resp['TotalNumberResponses'] - \
                    (page_size * (page_num + 1))

            page_num += 1

        records = list(map(self._add_fields, records))

        cols = ['SessionId', 'UserId', 'Date', 'Time', 'PlaybackSpeed', 'StartPosition', 'StartReason',
                'StopPosition', 'StopReason', 'SecondsViewed']

        df = pd.DataFrame(records, columns=cols)

        df = df.rename(columns={'Time': 'DateTime'})

        return df

    def get_session_details(self, session_id):
        '''
        Returns the result of calling the "UsageReporting.GetSessionDetailedUsage" method
        '''

        now = datetime.now()

        # last_month = now - timedelta(days=30)
        sept = date(2020, 9, 1)
        resp = self.usage_client.call_service(
            'GetSessionDetailedUsage',
            sessionId=session_id,
            beginRange=sept,
            endRange=now)

        return resp

    def get_session_usage_summary(self, session_id):
        '''
        Returns the result of calling the "UsageReporting.GetSessionDetailedUsage" method
        '''

        now = date.today()
        sept = date(2020, 9, 1)
        # last_month = now - timedelta(days=30)

        resp = self.usage_client.call_service(
            'GetSessionSummaryUsage',
            sessionId=session_id,
            beginRange=sept,
            endRange=now,
            granularity='Daily')

        return resp
