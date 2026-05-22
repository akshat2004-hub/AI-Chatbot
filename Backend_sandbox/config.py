import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # 🔐 API Keys
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "").strip()

    # 🤖 Model Config
    EMBEDDING_MODEL = "models/gemini-embedding-001"

    PRIMARY_MODEL = "gemini-2.0-flash"
    FALLBACK_MODEL = "gemini-flash-latest"
    LITE_MODEL = "gemini-pro-latest"

    # 🔥 UPDATED
    TEMPERATURE = 0.4

    # 📁 Paths
    VECTORSTORE_PATH = "vectorstore/"
    LEADS_FILE = "data/leads.json"
    LOGS_FILE = "logs.txt"

    # 📊 Project Constants
    DEV_LEVELS = ["Junior", "Mid", "Senior"]
    BUDGET_RANGES = ["< $5k", "$5k - $15k", "$15k - $50k", "$50k+"]

    # 🧠 Strategy Template (optional use)
    STRATEGY_TEMPLATE = """
    # Project Strategy: {project_name}

    ## Overview
    {overview}

    ## Recommended Tech Stack
    {tech_stack}

    ## Timeline & Approach
    {timeline}
    """

# ensure folder exists
if not os.path.exists("data"):
    os.makedirs("data")
