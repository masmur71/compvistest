
from dotenv import load_dotenv
load_dotenv()
import os

API_URL = os.getenv("API_TOKEN")
print(API_URL)
