from raw_data_handler.RawDataHandler import RawDataHandler

# Instantiate the Raw Data Handler
raw_data_handler = RawDataHandler()

# Updates our database up to 11:59 previous day UTC
raw_data_handler.update_database()
