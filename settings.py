import os
from dotenv import load_dotenv

load_dotenv()

HOST = os.getenv('HOST')
USERNAME = os.getenv('USERNAME')
PASSWORD = os.getenv('PASSWORD')
