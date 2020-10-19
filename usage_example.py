# flake8: noqa
from panopto_api.AuthenticatedClientFactory import AuthenticatedClientFactory
from panopto_api.ClientWrapper import ClientWrapper
from datetime import datetime, timedelta, timezone
from math import ceil

# create a client factory for making authenticated API requests
auth = AuthenticatedClientFactory(
    host, username, password, verify_ssl=host != 'localhost')

# let's get the admin user
user = auth.get_client('UserManagement')
lu_response = user.call_service(
    'ListUsers',
    searchQuery='sauder_post_api',  # This can be basically anything you wanna search by
    parameters={})
# 'admin' user is guaranteed to exist! pluck it out, excluding any other users that might match the query
# match_pattern = '<span class="match">admin</span>'  # the span will contain the matching portion of the username
admin = lu_response['PagedResults']['User'][0]
# admin = [r for r in lu_response['PagedResults']['User'] if r['UserKey'] == match_pattern][0]

# what has the admin user been watching?
page_size = 10
usage = auth.get_client('UsageReporting')
gudu_response = usage.call_service(
    'GetUserDetailedUsage',
    userId=admin['UserId'],
    pagination={'MaxNumberResults': page_size}
)
if gudu_response['TotalNumberResponses'] > 0:
    # get the last page!
    gudu_response = usage.call_service(
        'GetUserDetailedUsage',
        userId=admin['UserId'],
        pagination={
            'MaxNumberResults': page_size,
            'PageNumber': int(ceil(gudu_response['TotalNumberResponses'] / float(page_size)) - 1)
        }
    )
    endRange = datetime.now(timezone.utc)
    beginRange = endRange - timedelta(days=10)
    week_views = [v for v in gudu_response['PagedResponses']['DetailedUsageResponseItem']
                  if v['Time'].replace(tzinfo=timezone.utc) > beginRange]
    if week_views:
        # let's get the sessionId of the first view and see who else has been watching it in the past week
        sessionId = week_views[0]['SessionId']
        print('admin viewed session {} in the past week'.format(sessionId))

        ssu_response = usage.call_service(
            'GetSessionSummaryUsage',
            sessionId=sessionId,
            beginRange=beginRange,
            endRange=endRange,
            granularity='Daily'  # zeep doesn't currently support parsing enumeration types, so this is a magic string
        )
        view_days = [r for r in ssu_response if r['Views'] > 0]
        for day in sorted(view_days, key=lambda d: d['Time']):
            day_offset = int(ceil((endRange - day['Time'].replace(tzinfo=timezone.utc)).total_seconds() / (3600 * 24)))
            print('{} day{} ago: {} unique users viewed {} minutes in {} distinct views'.format(
                day_offset,
                's' if day_offset > 1 else ' ',
                day['UniqueUsers'],
                day['MinutesViewed'],
                day['Views']))
    else:
        print('no admin views in the past week')
