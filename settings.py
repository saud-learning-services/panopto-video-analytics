import os
from dotenv import load_dotenv

load_dotenv()

# For SOAP API
HOST = os.getenv('HOST_URL')
USERNAME = os.getenv('USERNAME')
PASSWORD = os.getenv('PASSWORD')

# For REST API
SERVER = os.getenv('SERVER')
ASPXAUTH = os.getenv('ASPXAUTH')
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')

# Filepath for ROOT directory
ROOT = os.path.dirname(os.path.abspath(__file__))
