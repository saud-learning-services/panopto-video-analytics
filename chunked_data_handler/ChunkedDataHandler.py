import pandas as pd
import settings
import os
import re

class ChunkedDataHandler():
    '''
    A class that deals with all the calculations and transformations involved in "chunking" viewing data
    Creates the output that gets plugged into the Tableau dashbaords
    '''

    @staticmethod
    def __get_folder_ids():
        '''
        Returns a list of folder ids that reflect the panopto folders that exist in our database
        '''
        folder_ids = []

        for d in os.listdir(settings.ROOT + '/database'):
            match = re.search('\[(.*?)\]', d)
            
            # ignore unknown files and folders - ie. don't have [ ] in title
            if not match:
                continue
            
            # pulls out text from regex match object
            folder_id = match.group(1)
            folder_ids.append(folder_id)

        return folder_ids

    def __init__(self):
        '''
        '''
        print('Instantiating Chunked Data Handler...')

    def output_chunked_data(self):
        '''
        '''

        folder_ids = self.__get_folder_ids()

        # If folder id's is empty, there are no valid entries in our database
        if not folder_ids:
            print('⚠️  Error: could not chunk data -- Database empty or corrupt ⚠️')
            return
        
        for fid in folder_ids:
            paths = list(map(lambda x: x[0], os.walk(settings.ROOT + '/database')))

            # get the path p that matches this folder id
            p = [p for p in paths if fid in p][0]

            overview_path = p + '/videos_overview.csv'
            activity_path = p + '/viewing_activity.csv'

            videos_overview_df = pd.read_csv(overview_path)
            viewing_activity_df = pd.read_csv(activity_path)

            session_ids = viewing_activity_df['SessionId'].tolist()
            unique_session_ids = list(set(session_ids))

            for sid in unique_session_ids:
                self.__chunk_data(sid)
    
    def __chunk_data(self, session_id):
        '''
        '''
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




            

        
    