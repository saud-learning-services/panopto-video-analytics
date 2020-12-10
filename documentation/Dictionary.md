# Data Dictionary & Descriptions

## Individual Video

### Single Session Data
- empty source is original to panopto
- \* means transformed field

column | source  | description
------- | ------- | -------
SessionId | | original column, a session is a video (this is actually the DeliveryId in the soap api)
UserId | | original column, Panopto's best guess at unique user
Date |*| transformation from DateTime
DateTime | | renamed from original column Time
StartPosition | | The time (in seconds) of the view
StartReason | | Start, Seek, Resume
StopPosition|*| StartPosition + SecondsViewed
StopReason | | Seek, Pause, End, PlayerClose
SecondsViewed | | The seconds of video viewed

#### Sample 
- sessionId and UserId shortened

SessionId | UserId | Date | DateTime | StartPosition | StartReason | StopPosition | StopReason | SecondsViewed
----------|--------|------|----------|---------------|-------------|--------------|------------|--------------
84cef7f7 | ac5601662b4b | 2020-10-16 | 2020-10-16 21:44:33.973000+00:00 | 0 | Start | 4.232846 | Seek | 4.232846
84cef7f7 | ac5601662b4b | 2020-10-16 | 2020-10-16 21:44:33.980000+00:00 | 26.79128 | Seek | 29.048043 | Seek | 2.256763
84cef7f7 | ac5601662b4b | 2020-10-16 | 2020-10-16 21:44:33.987000+00:00 | 9.816088 | Seek | 12.746006 | Pause | 2.929918
84cef7f7 | ac5601662b4b | 2020-10-16 | 2020-10-16 21:44:33.990000+00:00 | 12.83526 | Resume | 15.136563 | Pause | 2.301303
84cef7f7 | ac56017150bb | 2020-10-16 | 2020-10-16 22:25:10.247000+00:00 | 0 | Start | 6.179465 | Pause | 6.179465
84cef7f7 | ac56017150bb | 2020-10-16 | 2020-10-16 22:25:10.253000+00:00 | 19.278933 | Seek | 30.985006 | End | 11.706073
84cef7f7 | ac56017150bb | 2020-10-16 | 2020-10-16 22:26:10.240000+00:00 | 8.91215 | Seek | 11.365616 | Pause | 2.453466
84cef7f7 | ab5101848a3f | 2020-10-16 | 2020-10-16 22:27:12.380000+00:00 | 15.595997 | Seek | 26.321004 | Pause | 10.725007
84cef7f7 | ab5101848a3f | 2020-10-16 | 2020-10-16 22:30:21.683000+00:00 | 0.5 | Seek | 30.94654 | End | 30.44654

### COMM 290 Sample
> Generated Oct. 20 ~3:30pm

`Folder Name = COMM 290`

    .
    ├── <Folder Name>
    │   ├── sessions_summary.csv
    │   └── Session Viewing Details
    │       ├──<Session Name>_<Session ID>.csv
    │       └── ...

# Data Questions/Tests
- watch the same half of the video twice as an anonymous user (incognito in unique browser, as unique as possible) -> does this look like they watched 50% or 100% of the video
