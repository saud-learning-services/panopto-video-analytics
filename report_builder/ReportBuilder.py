from panopto_api.AuthenticatedClientFactory import AuthenticatedClientFactory
from datetime import datetime, date, timedelta


class ReportBuilder:

    def __init__(self, host, username, password):
        self.host = host
        self.username = username
        self.password = password

        # authorization
        self.auth = AuthenticatedClientFactory(host, username, password, verify_ssl=True)
        self.usage_client = self.auth.get_client('UsageReporting')

    def get_session_extended_details(self, session_id):
        '''
        Returns the result of calling the "UsageReporting.GetSessionExtendedDetailedUsage" method
        '''

        now = datetime.now()
        last_month = now - timedelta(days=30)

        page_size = 50

        resp = self.usage_client.call_service(
            'GetSessionExtendedDetailedUsage',
            sessionId=session_id,
            pagination={'MaxNumberResults': page_size},
            beginRange=last_month,
            endRange=now)

        return resp

    def get_session_details(self, session_id):
        '''
        Returns the result of calling the "UsageReporting.GetSessionDetailedUsage" method
        '''

        now = datetime.now()
        last_month = now - timedelta(days=30)

        resp = self.usage_client.call_service(
            'GetSessionDetailedUsage',
            sessionId=session_id,
            beginRange=last_month,
            endRange=now)

        return resp

    def get_session_usage_summary(self, session_id):
        '''
        Returns the result of calling the "UsageReporting.GetSessionDetailedUsage" method
        '''

        now = date.today()
        last_month = now - timedelta(days=30)

        resp = self.usage_client.call_service(
            'GetSessionSummaryUsage',
            sessionId=session_id,
            beginRange=last_month,
            endRange=now,
            granularity='Daily')

        return resp
