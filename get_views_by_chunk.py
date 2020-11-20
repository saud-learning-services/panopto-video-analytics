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

sid = alisons_id

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

    view_ranges = []
    all_views = []

    for index, row in user_views.iterrows():

        candidate = (row['StartPosition'], row['StopPosition'])
        all_views.append(candidate)

        add_candidate = None

        # if we don't have any view ranges yet, add the tuple and continue to the next record
        if len(view_ranges) == 0:
            view_ranges.append(candidate)
            continue

        # compare candidate range to all the existing view ranges for that user
        for vrange in view_ranges:
            lower_bound = vrange[0]
            upper_bound = vrange[1]

           # falls within bound of existing range, candidate accounted for, skip
            if candidate[0] >= lower_bound and candidate[1] <= upper_bound:
                add_candidate = False
                break

            # falls above or below given range, keep searching for range that satisfies, if none is found add candidate as is
            if candidate[0] >= upper_bound or candidate[1] <= lower_bound:
                add_candidate = True
                continue

            # completely envolopes the entire range, replace the range that it envelops
            if candidate[0] < lower_bound and candidate[1] > upper_bound:
                view_ranges.remove(vrange)
                add_candidate = True
                break

            # falls partially above existing range, adjust upper bound
            if candidate[1] > upper_bound:
                # adjust the upper bound in the list
                adjusted_tuple = (vrange[0], candidate[1])
                view_ranges.remove(vrange)
                view_ranges.append(adjusted_tuple)
                add_candidate = False
                break

            # falls partially below existing range, adjust lower bound
            if candidate[0] < lower_bound:
                # adjust the lower bound in the list
                adjusted_tuple = (candidate[0], vrange[1])
                view_ranges.remove(vrange)
                view_ranges.append(adjusted_tuple)
                add_candidate = False
                break

        # if it's an etirely new range (aka not envolped or falling within existing range) add it to the list
        if add_candidate:
            view_ranges.append(candidate)

    # sort in ascending order
    view_ranges.sort(key=lambda e: e[0])

    # print('UNMERGED VIEW RANGES:')
    # print(view_ranges)

    '''
    Because earlier we replaced existing ranges with ones that envelop, we may get overlap that should get merged
    For example:
    UNMERGED VIEW RANGES (Test.csv):
    [(0.23, 7.04), (5.16, 24.53), (14.23, 20.04),
      (27.03, 32.53), (35.03, 37.53), (37.53, 40.0)]
    MERGED VIEW RANGES (Test.csv):
    [(0.23, 24.53), (27.03, 32.53), (35.03, 40.0)]
    We need to go over once again and check for these overlaps and merge them together
    '''

    to_remove = []
    for i in range(len(view_ranges) - 1):
        curr = view_ranges[i]
        nxt = view_ranges[i + 1]

        # check to see if the ranges in the tuples overlap
        if curr[1] >= nxt[0]:
            # merge
            view_ranges[i + 1] = (min(curr[0], nxt[0]), max(curr[1], nxt[1]))
            to_remove.append(view_ranges[i])

    for vrange in to_remove:
        view_ranges.remove(vrange)

    cprint('\nUser: ' + user_id, 'yellow')
    cprint(view_ranges, 'red')

    for chunk in chunks:
        # calculate unique views

        chunk_lower_bound = chunk['chunk_start']
        chunk_upper_bound = chunk['chunk_end']
        chunk_duration = chunk_upper_bound - chunk_lower_bound

        for index, vrange in enumerate(view_ranges):
            range_lower_bound = vrange[0]
            range_upper_bound = vrange[1]

            # if the view range and chunk don't overlap at all, continue to next iteration
            if chunk_lower_bound > range_upper_bound or chunk_upper_bound < range_lower_bound:
                continue

            overlap = (max(chunk_lower_bound, range_lower_bound),
                       min(chunk_upper_bound, range_upper_bound))

            overlap_duration = overlap[1] - overlap[0]

            if overlap_duration <= 0:
                raise ValueError(
                    'Expected range and chunk had at least some overlap')

            # if overlap is at least 90% of the chunk, increment the unique views
            if overlap_duration >= (chunk_duration * 0.01):
                chunk['unique_views'] += 1
                break

            total_overlap = overlap_duration

            # check neighbouring view ranges, if they overlap the chunk, add their coverage (it may go > 90% with neighbours)

            # check previous tuples
            j = 0
            while True:

                try:
                    prev = view_ranges[index - j]
                except IndexError:
                    # this means we have no previous ones to check anymore so break
                    break

                if prev[1] <= chunk_lower_bound:
                    break

                prev_overlap = (max(chunk_lower_bound, prev[0]),
                                min(chunk_upper_bound, prev[1]))

                prev_overlap_duration = prev_overlap[1] - prev_overlap[0]

                total_overlap += prev_overlap_duration
                j += 1

            # check next tuples
            j = 0
            while True:

                try:
                    nxt = view_ranges[index + j]
                except IndexError:
                    # this means we have no previous ones to check anymore so break
                    break

                if nxt[0] >= chunk_upper_bound:
                    break

                nxt_overlap = (max(chunk_lower_bound, nxt[0]),
                               min(chunk_upper_bound, nxt[1]))

                nxt_overlap_duration = nxt_overlap[1] - nxt_overlap[0]

                total_overlap += nxt_overlap_duration
                j += 1

            # if total overlap is at least 90% of the chunk, increment the unique views
            if total_overlap >= (chunk_duration * 0.01):
                chunk['unique_views'] += 1
                break

    # print(user_views)
    all_views.sort(key=lambda e: e[0])
    # print(all_views)

    user_row = {
        'user_id': user_id,
        'chunk_0': 0,
        'chunk_1': 0,
        'chunk_2': 0,
        'chunk_3': 0,
        'chunk_4': 0,
        'chunk_5': 0,
        'chunk_6': 0,
        'chunk_7': 0,
        'chunk_8': 0,
        'chunk_9': 0,
        'chunk_10': 0,
        'chunk_11': 0,
        'chunk_12': 0,
        'chunk_13': 0,
        'chunk_14': 0,
        'chunk_15': 0,
        'chunk_16': 0,
        'chunk_17': 0,
        'chunk_18': 0,
        'chunk_19': 0,
    }

    total_view_time = 0

    for vrange in all_views:
        range_lower_bound = vrange[0]
        range_upper_bound = vrange[1]

        vrange_duration = vrange[1] - vrange[0]

        total_view_time += vrange_duration

        for chunk in chunks:

            chunk_lower_bound = chunk['chunk_start']
            chunk_upper_bound = chunk['chunk_end']

            # if the view range and chunk don't overlap at all, continue to next iteration
            if chunk_lower_bound > range_upper_bound or chunk_upper_bound < range_lower_bound:
                continue

            overlap = (max(chunk_lower_bound, range_lower_bound),
                       min(chunk_upper_bound, range_upper_bound))

            overlap_duration = overlap[1] - overlap[0]

            chunk_index = chunk['chunk_index']
            key = f'chunk_{chunk_index}'

            user_row[key] += overlap_duration

    user_row['total_view_time'] = total_view_time
    table_2_data.append(user_row)

chunks_keys = []

table_2_df = pd.DataFrame(data=table_2_data)

chunks_df = pd.DataFrame(data=chunks)

print(chunks_df)
print(table_2_df)

chunks_df.to_csv('chunk_output/views_per_chunk.csv')
table_2_df.to_csv('chunk_output/chunk_viewership_per_user.csv')
