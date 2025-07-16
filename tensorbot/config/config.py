# Loads env variables 
from dotenv import load_dotenv
import os 

# load environment vars from .env 
load_dotenv()

# Now read 
MONGODB_URI = os.getenv("MONGODB_URI")

TENSORDOCK_API_KEY = os.getenv("TENSORDOCK_API_KEY")

PRIVATE_KEY_PATH= os.getenv("PRIVATE_KEY_PATH")

SSH_PUBLIC_KEY = os.getenv("SSH_PUBLIC_KEY")