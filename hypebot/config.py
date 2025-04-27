# Loads env variables 
from dotenv import load_dotenv
import os 

# load environment vars from .env 
load_dotenv()

# Now read 
MONGODB_URI = os.getenv("MONGODB_URI")

HYPERBOLIC_API_KEY = os.getenv("HYPERBOLIC_API_KEY")