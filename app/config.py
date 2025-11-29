import os
from dotenv import load_dotenv

load_dotenv()

STUDENT_EMAIL = "23f3003433@ds.study.iitm.ac.in"
STUDENT_SECRET = "oas-secret"

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
