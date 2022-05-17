from datetime import datetime
from pathlib import Path
from termcolor import cprint
from utils import sanitize_string
from pytz import timezone
import pandas as pd
import colorama
import settings
import os
import re

# You need this for termcolor to display properly in windows terminal'
colorama.init()

class ChunkedDataHandler:
    """
    A class that deals with all the calculations and transformations involved in "chunking" viewing data
    Creates the output that gets plugged into the Tableau dashbaords
    """

    @staticmethod
    def __get_folder_ids():
        """
        Returns a list of folder objects {id, name} that reflect the panopto folders that exist in our database
        """
        folders = []

        database_path = Path(f"{settings.ROOT}/database")
        for d in os.listdir(database_path):
            match = re.search("\[(.*?)\]", d)

            # ignore unknown files and folders - ie. don't have [ ] in title
            if not match:
                continue

            # pulls out text from regex match object
            folder_id = match.group(1)
            folder_name = d.split("[")[0]
            folders.append({"folder_id": folder_id, "folder_name": folder_name})

        return folders

    @staticmethod
    def __make_chunk_list(video_duration):
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

            chunk = {"index": i, "start": chunk_start, "end": chunk_end}

            prev_upper_bound = chunk_end
            chunks.append(chunk)

        return chunks

    @staticmethod
    def __make_pst_date(utc_datetime):
        """
        takes a UTC datetime as an argument, converts it to PST and returns just the date (no time)
        """
        if isinstance(utc_datetime, str):
            try:
                # if datetime has microseconds
                utc_datetime = datetime.strptime(utc_datetime, "%Y-%m-%d %H:%M:%S.%f%z")
            except ValueError:
                # if datetime does not have microseconds
                utc_datetime = datetime.strptime(utc_datetime, "%Y-%m-%d %H:%M:%S%z")
        pst_datetime = utc_datetime.astimezone(timezone("US/Pacific"))
        return pst_datetime.date()

    @staticmethod
    def __get_coverage(viewing_data_tuples):
        """
        @param viewing_data_tuples: a list of tuples of the form (startPostiion, endPosition)
        Represents all the viewing activity for a particular user on a particular day
        """
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

    @staticmethod
    def __get_total_time_spent_in_chunk(chunk, viewing_data):
        chunk_lower_bound = chunk["start"]
        chunk_upper_bound = chunk["end"]

        total_time = 0

        for view in viewing_data:
            view_lower_bound = view[0]
            view_upper_bound = view[1]

            # view does not fall within chunk, continue to next view
            if (
                view_lower_bound > chunk_upper_bound
                or view_upper_bound < chunk_lower_bound
            ):
                continue

            # view falls within chunk, add overlap to toal duration
            overlap = (
                max(chunk_lower_bound, view_lower_bound),
                min(chunk_upper_bound, view_upper_bound),
            )

            overlap_duration = overlap[1] - overlap[0]

            total_time += overlap_duration

        return total_time

    @staticmethod
    def __check_neighbours(index, chunk, coverage, view_time_acc, ascending):
        chunk_lower_bound = chunk["start"]
        chunk_upper_bound = chunk["end"]

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

            overlap = (
                max(chunk_lower_bound, neighbour[0]),
                min(chunk_upper_bound, neighbour[1]),
            )

            overlap_duration = overlap[1] - overlap[0]

            view_time_acc += overlap_duration
            j += 1

        return view_time_acc

    def __get_viewers_count(
        self, session_id, sessions_overview_df, viewing_activity_df
    ):
        """
        Calculates unique and completed viewers for a given session
        """
        session = sessions_overview_df.loc[
            sessions_overview_df["SessionId"] == session_id
        ]
        session = session.iloc[0]
        session_duration = session["Duration"]

        # grab the viewing activity for the session
        session_viewing_activity = viewing_activity_df.loc[
            viewing_activity_df["SessionId"] == session_id
        ]

        # get a list of unique user id's from the dataframe
        user_ids = list(session_viewing_activity["UserId"])
        unique_user_ids = list(dict.fromkeys(user_ids))

        unique_viewer_count = len(unique_user_ids)

        completed_count = 0
        coverage = None
        # for every unique user (viewer)
        for user_id in unique_user_ids:
            view_data = []
            user_views = session_viewing_activity.loc[
                session_viewing_activity["UserId"] == user_id
            ]

            for index, view in user_views.iterrows():
                view_tuple = (view["StartPosition"], view["StopPosition"])
                view_data.append(view_tuple)

            coverage = self.__get_coverage(view_data)

            total_duration = 0

            for vrange in coverage:
                lower_bound = vrange[0]
                upper_bound = vrange[1]

                duration = upper_bound - lower_bound

                total_duration += duration

            if total_duration >= (0.75 * session_duration):
                # increment count
                completed_count += 1

        return session, unique_viewer_count, completed_count

    def __init__(self):
        """
        """
        print("Instantiating Chunked Data Handler...")

    def output_chunked_data(self):
        folders = self.__get_folder_ids()

        # If folder id's is empty, there are no valid entries in our database
        if not folders:
            print("⚠️  Error: could not chunk data -- Database empty or corrupt ⚠️")
            return

        # Lists to hold each dataframe we create for each folder
        # These get concatinated into a single dataframe at the end for Tableau
        tableau_chunked_data_dfs = []
        tableau_sessions_overview_dfs = []

        # Check to see if a Tableau folder already exists and if not make one
        tableau_target = Path(f"{settings.ROOT}/output[CHUNKED]/tableau")
        if not os.path.isdir(tableau_target):
            os.mkdir(tableau_target)

        for f in folders:
            folder_id = f["folder_id"]
            folder_name = f["folder_name"]

            folder_ids_to_run = pd.read_csv(f"{settings.ROOT}/courses.csv")["PanoptoFolderID"].to_list()

            if folder_id not in folder_ids_to_run:
                cprint(
                    f"\n\nSkipping {folder_name} from database. Not in courses.csv",
                    "yellow",
                )
                continue
            print(f"\nChunking data for: {folder_name} ({folder_id})...")

            database_path = Path(f"{settings.ROOT}/database")
            paths = list(map(lambda x: x[0], os.walk(database_path)))

            # get the path p that matches this folder id
            p = [p for p in paths if folder_id in p][0]

            overview_path = Path(p + "/sessions_overview.csv")
            activity_path = Path(p + "/viewing_activity.csv")

            sessions_overview_df = pd.read_csv(overview_path)
            viewing_activity_df = pd.read_csv(activity_path)

            chunked_data, sessions_overview_data = self.__chunk_data(
                sessions_overview_df, viewing_activity_df
            )

            chunked_data_df = pd.DataFrame(data=chunked_data)
            sessions_overview_df = pd.DataFrame(data=sessions_overview_data)

            # Push dataframes to Tableau lists - will get concatinated into single df
            tableau_chunked_data_dfs.append(chunked_data_df)
            tableau_sessions_overview_dfs.append(sessions_overview_df)

            target = Path(f"{settings.ROOT}/output[CHUNKED]/{sanitize_string(folder_name)}[{folder_id}]")
            if not os.path.isdir(target):
                os.mkdir(target)

            chunked_data_df.to_csv(target / "chunked_data.csv", index=False)
            sessions_overview_df.to_csv(target / "sessions_overview.csv", index=False)

        print("\n\nOutputting data for Tableau...")
        # Concatinate and output the tables for Tableau
        tableau_chunked_df = pd.concat(tableau_chunked_data_dfs)
        tableau_sessions_df = pd.concat(tableau_sessions_overview_dfs)

        # Add the Order column
        # tableau_sessions_df.insert(
        #     0, 'Order', range(1, 1 + len(tableau_sessions_df)))

        tableau_chunked_df.to_csv(tableau_target / "chunked_data.csv", index=False)
        tableau_sessions_df.to_csv(
            tableau_target / "sessions_overview.csv", index=False
        )

    def __chunk_data(self, sessions_overview_df, viewing_activity_df):
        """
        Given raw data in the form of two tables:
            - video_overview: summarizing all videos in a particular course folder
            - viewing_activity: all viewing activity for all sessions in that folder
        ...transform these tables to a 'chunked' format where viewing activity is summarized
        across 20 chunks on the timeline (This is the data format needed for the Panopto Video
        Tableau dashboards)
        """
        # this array will hold our row data (as dictionaries)
        chunked_data = []
        session_summary_data = []

        print("Working...")

        for index, video in sessions_overview_df.iterrows():

            video_duration = video["Duration"]
            session_id = video["SessionId"]

            session, unique_viewer_count, completed_count = self.__get_viewers_count(
                session_id, sessions_overview_df, viewing_activity_df
            )

            session_record = {
                "Order": index + 1,
                "SessionId": session["SessionId"],
                "SessionName": session["SessionName"],
                "Description": session["Description"],
                "Duration": session["Duration"],
                "RootFolderID": session["RootFolderID"],
                "RootFolderName": session["RootFolderName"],
                "ContainingFolderID": session["ContainingFolderId"],
                "ContainingFolderName": session["ContainingFolderName"],
                "UniqueViewers": unique_viewer_count,
                "CompletedViewerCount(75%Coverage)": completed_count,
            }

            session_summary_data.append(session_record)

            chunks = self.__make_chunk_list(video_duration)

            # Parse out the viewing data for THIS SESSION/VIDEO
            session_viewing_data = viewing_activity_df.loc[
                viewing_activity_df["SessionId"] == session_id
            ]

            # get a list of unique user id's from the dataframe (Users who have viewed the session)
            user_ids = list(session_viewing_data["UserId"])
            unique_user_ids = list(dict.fromkeys(user_ids))

            # for every unique user (viewer)
            for user_id in unique_user_ids:

                # select the rows that correlate to that user
                user_views = session_viewing_data.loc[
                    session_viewing_data["UserId"] == user_id
                ]

                # get a list of all dates in the 'DateTime' column - converted to PST (from UTC)
                datetimes = list(user_views["DateTime"])
                dates = list(map(self.__make_pst_date, datetimes))

                # filter down to just unique dates
                filtered_dates = list(dict.fromkeys(dates))

                for date in filtered_dates:
                    # go through every one of the users view records and grab the start and end position
                    # put these in a tuple and add to the all_viewing_data list IF it's on the given viewing date
                    # TUPLES: {startPosition, stopPosition}
                    all_viewing_data = []
                    for index, view in user_views.iterrows():
                        if self.__make_pst_date(view["DateTime"]) == date:
                            view_tuple = (view["StartPosition"], view["StopPosition"])
                            all_viewing_data.append(view_tuple)

                    # coverage is an array of tuples representing timeline coverage
                    coverage = self.__get_coverage(all_viewing_data)

                    for chunk in chunks:
                        chunk_lower_bound = chunk["start"]
                        chunk_upper_bound = chunk["end"]
                        chunk_duration = chunk_upper_bound - chunk_lower_bound

                        time_watched_in_chunk = self.__get_total_time_spent_in_chunk(
                            chunk, all_viewing_data
                        )

                        for index, vrange in enumerate(coverage):
                            range_lower_bound = vrange[0]
                            range_upper_bound = vrange[1]

                            # if the view range and chunk don't overlap at all, continue to next iteration
                            if (
                                chunk_lower_bound > range_upper_bound
                                or chunk_upper_bound < range_lower_bound
                            ):
                                continue

                            overlap = (
                                max(chunk_lower_bound, range_lower_bound),
                                min(chunk_upper_bound, range_upper_bound),
                            )

                            overlap_duration = overlap[1] - overlap[0]

                            if overlap_duration < 0:
                                msg = (
                                    "Expected range and chunk had at least some overlap"
                                )
                                raise ValueError(msg)

                            # if overlap is less than 75% of the chunk, check neighbours for additional overlap
                            if overlap_duration < (chunk_duration * 0.75):

                                # overlap duration will represent the total time overlap between a chunk and ALL view ranges
                                # check neighbouring view ranges, if they overlap the chunk, add their coverage (it may go > 75% with neighbours)

                                # check PREVIOUS tuples
                                overlap_duration = self.__check_neighbours(
                                    index,
                                    chunk,
                                    coverage,
                                    overlap_duration,
                                    ascending=False,
                                )

                                # check NEXT tuples
                                overlap_duration = self.__check_neighbours(
                                    index,
                                    chunk,
                                    coverage,
                                    overlap_duration,
                                    ascending=True,
                                )

                            # check again if total overlap is at least 75% and create a record for that chunk
                            completed = False
                            if overlap_duration >= (chunk_duration * 0.75):
                                completed = True

                            record = {
                                "SessionId": session_id,
                                "UserId": user_id,
                                "Date": date,
                                "ChunkIndex": chunk["index"],
                                "ChunkStart": chunk["start"],
                                "ChunkEnd": chunk["end"],
                                "ChunkPercentCovered": (
                                    overlap_duration / chunk_duration
                                )
                                * 100,
                                "TotalTimeSpent": time_watched_in_chunk,
                                "Completed(75%)": completed,
                            }
                            chunked_data.append(record)
                            break
        return chunked_data, session_summary_data
