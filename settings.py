import os
from dotenv import load_dotenv

load_dotenv()

SERVER = os.getenv('SERVER')

# For SOAP API
USERNAME = os.getenv('USERNAME')
PASSWORD = os.getenv('PASSWORD')

# For REST API
ASPXAUTH = os.getenv('ASPXAUTH')
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')

# Filepath for ROOT directory
ROOT = os.path.dirname(os.path.abspath(__file__))
