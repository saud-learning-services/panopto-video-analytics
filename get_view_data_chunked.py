from report_builder.ReportBuilder import ReportBuilder
from panopto_rest_api.panopto_oauth2 import PanoptoOAuth2
from panopto_rest_api.panopto_interface import Panopto
import settings
import os
import pandas as pd
from pprint import pprint
from pytz import timezone
from termcolor import cprint


def get_coverage(viewing_data_tuples):
    '''
    @param viewing_data_tuples: a list of tuples of the form (startPostiion, endPosition)
    Represents all the viewing activity for a particular user on a particular day
    '''
    coverage = []
    for candidate in viewing_data_tuples:

        add_candidate = None

        # if we don't have any view ranges yet, add the tuple and continue to the next record
        if len(coverage) == 0:
            coverage.append(candidate)
            continue

        # compare candidate range to all the existing view ranges for that user
        for vrange in coverage:
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
                coverage.remove(vrange)
                add_candidate = True
                break

            # falls partially above existing range, adjust upper bound
            if candidate[1] > upper_bound:
                # adjust the upper bound in the list
                adjusted_tuple = (vrange[0], candidate[1])
                coverage.remove(vrange)
                coverage.append(adjusted_tuple)
                add_candidate = False
                break

            # falls partially below existing range, adjust lower bound
            if candidate[0] < lower_bound:
                # adjust the lower bound in the list
                adjusted_tuple = (candidate[0], vrange[1])
                coverage.remove(vrange)
                coverage.append(adjusted_tuple)
                add_candidate = False
                break

        # if it's an etirely new range (aka not envolped or falling within existing range) add it to the list
        if add_candidate:
            coverage.append(candidate)

    # sort in ascending order
    coverage.sort(key=lambda e: e[0])

    to_remove = []
    for i in range(len(coverage) - 1):
        curr = coverage[i]
        nxt = coverage[i + 1]

        # check to see if the ranges in the tuples overlap
        if curr[1] >= nxt[0]:
            # merge
            coverage[i + 1] = (min(curr[0], nxt[0]), max(curr[1], nxt[1]))
            to_remove.append(coverage[i])

    for vrange in to_remove:
        coverage.remove(vrange)

    return coverage


def make_pst_date(utc_datetime):
    '''
    takes a UTC datetime as an argument, converts it to PST and returns just the date (no time)
    '''
    pst_datetime = utc_datetime.astimezone(timezone('US/Pacific'))
    return pst_datetime.date()


def make_chunk_list(video_duration):
    chunk_duration = video_duration / 20

    chunks = []

    # start upper bound at 0 seconds
    prev_upper_bound = 0.00

    # create a list of 20 chunks (5%)
    for i in range(20):

        chunk_start = prev_upper_bound

        chunk_end = chunk_start + chunk_duration

        if chunk_end > video_duration:
            chunk_end = video_duration

        chunk = {
            'index': i,
            'start': chunk_start,
            'end': chunk_end
        }

        prev_upper_bound = chunk_end
        chunks.append(chunk)

    return chunks


def get_total_time_spent_in_chunk(chunk, viewing_data):
    chunk_lower_bound = chunk['start']
    chunk_upper_bound = chunk['end']

    total_time = 0

    for view in viewing_data:
        view_lower_bound = view[0]
        view_upper_bound = view[1]

        # view does not fall within chunk, continue to next view
        if view_lower_bound > chunk_upper_bound or view_upper_bound < chunk_lower_bound:
            continue

        # view falls within chunk, add overlap to toal duration
        overlap = (max(chunk_lower_bound, view_lower_bound),
                   min(chunk_upper_bound, view_upper_bound))

        overlap_duration = overlap[1] - overlap[0]

        total_time += overlap_duration

    return total_time


def check_neighbours(index, chunk, coverage, view_time_acc, ascending):
    chunk_lower_bound = chunk['start']
    chunk_upper_bound = chunk['end']

    j = 1
    while True:

        if ascending:
            neighbouring_index = index + j
        else:
            neighbouring_index = index - j

        # if we've reached the first
        if neighbouring_index < 0 or neighbouring_index > len(coverage) - 1:
            break

        neighbour = coverage[neighbouring_index]

        if neighbour[1] <= chunk_lower_bound or neighbour[0] >= chunk_upper_bound:
            break

        overlap = (max(chunk_lower_bound, neighbour[0]),
                   min(chunk_upper_bound, neighbour[1]))

        overlap_duration = overlap[1] - \
            overlap[0]

        view_time_acc += overlap_duration
        j += 1

    return view_time_acc


def get_viewers_count(sid, report_builder, panopto_rest):
    session = panopto_rest.get_session(session_id=sid)
    session_duration = session['Duration']

    cprint('\n' + session['Name'], 'green')

    df = report_builder.get_viewing_details(session_id=sid)

    # get a list of unique user id's from the dataframe
    user_ids = list(df['UserId'])
    unique_user_ids = list(dict.fromkeys(user_ids))

    unique_viewer_count = len(unique_user_ids)

    cprint('UNIQUE VIEWERS: ' + str(unique_viewer_count), 'blue')

    seeks_table_data = []

    completed_count = 0
    coverage = None
    # for every unique user (viewer)
    for user_id in unique_user_ids:
        view_data = []
        user_views = df.loc[df['UserId'] == user_id]

        for index, view in user_views.iterrows():
            view_tuple = (view['StartPosition'],
                          view['StopPosition'],
                          view['StartReason'],
                          view['DateTime'])
            view_data.append(view_tuple)

        coverage = get_coverage(view_data)

        for index, view in enumerate(view_data):
            if index == 0:
                continue

            prev = view_data[index - 1]
            if view[2] == 'Seek' and prev[1] > view[0]:

                row = {
                    'session_id': sid,
                    'user_id': user_id,
                    'date': make_pst_date(view[3]),
                    'start_time': view[0],
                    'end_time': view[1],
                    'timespent': view[1] - view[0]
                }
                seeks_table_data.append(row)

        total_duration = 0

        for vrange in coverage:
            lower_bound = vrange[0]
            upper_bound = vrange[1]

            duration = upper_bound - lower_bound

            total_duration += duration

        if total_duration >= (0.75 * session_duration):
            # increment count
            completed_count += 1

    cprint('COMPLETED VIEWERS (75%% coverage): ' + str(completed_count), 'blue')
    return unique_viewer_count, completed_count, seeks_table_data


def get_user_views_chunked(sid, report_builder, panopto_rest):

    session = panopto_rest.get_session(session_id=sid)

    # rounding down to the nearest second seems to match the total time displayed on the Panopto UI
    duration = session['Duration']

    chunks = make_chunk_list(duration)

    df = report_builder.get_viewing_details(session_id=sid)

    # get a list of unique user id's from the dataframe
    user_ids = list(df['UserId'])
    unique_user_ids = list(dict.fromkeys(user_ids))

    # this array will hold our row data (as dictionaries)
    data = []

    # for every unique user (viewer)
    for user_id in unique_user_ids:

        # select the rows that correlate to that user
        user_views = df.loc[df['UserId'] == user_id]

        # get a list of all dates in the 'DateTime' column - converted to PST (from UTC)
        datetimes = list(user_views['DateTime'])
        dates = list(map(make_pst_date, datetimes))

        # filter down to just unique dates
        filtered_dates = list(dict.fromkeys(dates))

        for date in filtered_dates:

            # go through every one of the users view records and grab the start and end position
            # put these in a tuple and add to the all_viewing_data list IF it's on the given viewing date
            # TUPLES: {startPosition, stopPosition}
            all_viewing_data = []
            for index, view in user_views.iterrows():
                view_tuple = (view['StartPosition'], view['StopPosition'])
                if (make_pst_date(view['DateTime']) == date):
                    all_viewing_data.append(view_tuple)

            # # get a dataframe with only
            # user_views_on_date_df = user_views.loc[user_views['DateTime'] == date]

            # # go through every one of their views and grab the start and end position
            # # put these in a tuple and add to the all_viewing_data list
            # # TUPLES: {startPosition, stopPosition}
            # all_viewing_data = []
            # for index, view in user_views_on_date_df.iterrows():
            #     view_tuple = (view['StartPosition'], view['StopPosition'])
            #     all_viewing_data.append(view_tuple)

            # coverage is an array of tuples representing timeline coverage
            coverage = get_coverage(all_viewing_data)

            for chunk in chunks:
                chunk_lower_bound = chunk['start']
                chunk_upper_bound = chunk['end']
                chunk_duration = chunk_upper_bound - chunk_lower_bound

                time_watched_in_chunk = get_total_time_spent_in_chunk(
                    chunk,
                    all_viewing_data)

                for index, vrange in enumerate(coverage):
                    range_lower_bound = vrange[0]
                    range_upper_bound = vrange[1]

                    # if the view range and chunk don't overlap at all, continue to next iteration
                    if chunk_lower_bound > range_upper_bound or chunk_upper_bound < range_lower_bound:
                        continue

                    overlap = (max(chunk_lower_bound, range_lower_bound),
                               min(chunk_upper_bound, range_upper_bound))

                    overlap_duration = overlap[1] - overlap[0]

                    if overlap_duration <= 0:
                        msg = 'Expected range and chunk had at least some overlap'
                        raise ValueError(msg)

                    # if overlap is less than 75% of the chunk, check neighbours for additional overlap
                    if overlap_duration < (chunk_duration * 0.75):

                        # overlap duration will represent the total time overlap between a chunk and ALL view ranges
                        # check neighbouring view ranges, if they overlap the chunk, add their coverage (it may go > 75% with neighbours)

                        # check PREVIOUS tuples
                        overlap_duration = check_neighbours(
                            index,
                            chunk,
                            coverage,
                            overlap_duration,
                            ascending=False)

                        # check NEXT tuples
                        overlap_duration = check_neighbours(
                            index,
                            chunk,
                            coverage,
                            overlap_duration,
                            ascending=True)

                    # check again if total overlap is at least 75% and create a record for that chunk
                    completed = False
                    if overlap_duration >= (chunk_duration * 0.75):
                        completed = True

                    record = {
                        'session_id': sid,
                        'user_id': user_id,
                        'date': date,
                        'chunk_index': chunk['index'],
                        'chunk_start': chunk['start'],
                        'chunk_end': chunk['end'],
                        'chunk_percent_covered': (overlap_duration / chunk_duration) * 100,
                        'total_time_spent': time_watched_in_chunk,
                        'completed(75%)': completed
                    }
                    data.append(record)
                    break
    return data


if __name__ == '__main__':

    # SOAP API Initialization
    report_builder = ReportBuilder(settings.SERVER,
                                   settings.USERNAME,
                                   settings.PASSWORD)

    # REST API Initialization
    oauth2 = PanoptoOAuth2(settings.SERVER,
                           settings.CLIENT_ID,
                           settings.CLIENT_SECRET,
                           True)
    panopto_rest = Panopto(settings.SERVER, True, oauth2)

    folder_ids = ['6a132260-aae0-4e8d-8589-ac570162f885',
                  '55a90663-2a10-43ed-a351-ac2a016cf839']

    for folder_id in folder_ids:
        folder_data = panopto_rest.get_folder(folder_id=folder_id)
        folder_name = folder_data['Name']

        output_folder_path = settings.ROOT + f'/data/{folder_name}'
        os.mkdir(output_folder_path)

        sessions = panopto_rest.get_sessions(folder_id=folder_id)

        session_ids = list(map(lambda session: session['Id'], sessions))

        # Build out sessions_sumary.csv table
        columns = ['Order',
                   'SessionID',
                   'SessionName',
                   'Description',
                   'Duration',
                   'EmbedURL',
                   'FolderId',
                   'FolderName',
                   'UniqueViewers',
                   'CompletedViewerCount (75%% coverage)']

        session_summary_data = []

        user_views_chunked_data = []

        all_seeks_data = []

        alphabetic_index = 1

        for sid in session_ids:
            session = panopto_rest.get_session(session_id=sid)

            unique_viewer_count, completed_view_count, seeks_data = get_viewers_count(
                sid, report_builder, panopto_rest)

            all_seeks_data = all_seeks_data + seeks_data

            seeks_cols = ['session_id', 'user_id', 'date',
                          'start_time', 'end_time', 'timespent']

            seeks_df = pd.DataFrame(data=all_seeks_data, columns=seeks_cols)

            seeks_df.to_csv(output_folder_path +
                            '/seeks_backwards.csv', index=False)

            # print('Getting data for Session: {}'.format(session['Name']))
            row = {
                'Order': alphabetic_index,
                'SessionID': session['Id'],
                'SessionName': session['Name'],
                'Description': session['Description'],
                'Duration': session['Duration'],
                'EmbedURL': session['Urls']['EmbedUrl'],
                'FolderId': session['FolderDetails']['Id'],
                'FolderName': session['FolderDetails']['Name'],
                'UniqueViewers': unique_viewer_count,
                'CompletedViewerCount (75%% coverage)': completed_view_count
            }

            # append above row to the summary table
            session_summary_data.append(row)

            session_views_data = get_user_views_chunked(
                sid, report_builder, panopto_rest)

            user_views_chunked_data = user_views_chunked_data + session_views_data

            alphabetic_index += 1

        session_summary_df = pd.DataFrame(
            data=session_summary_data, columns=columns)

        user_views_chunked_df = pd.DataFrame(
            data=user_views_chunked_data)

        session_summary_df.to_csv(
            output_folder_path + '/sessions_summary.csv', index=False)

        print('successfully generated session_summary.csv')

        user_views_chunked_df.to_csv(
            output_folder_path + '/folder_viewing_activity_chunked.csv', index=False)

        print('successfully generated user_views_chunked.csv')
