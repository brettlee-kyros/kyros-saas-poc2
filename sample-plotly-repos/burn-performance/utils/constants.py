import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()


# Determine the environment
ENV = os.getenv("ENV", "prod")

if ENV == "prod":
    SERVER_HOSTNAME = os.getenv("DBX_SERVER_HOSTNAME")
    HTTP_PATH = os.getenv("DBX_WAREHOUSE_HTTP_PATH")
    ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")

elif ENV == "dev":
    # Development variables with 'DEV_' prefix
    SERVER_HOSTNAME = os.getenv("DEV_DBX_SERVER_HOSTNAME")
    HTTP_PATH = os.getenv("DEV_DBX_WAREHOUSE_HTTP_PATH")
    ACCESS_TOKEN = os.getenv("DEV_ACCESS_TOKEN")

elif ENV == "uat":
    SERVER_HOSTNAME = os.getenv("UAT_DBX_SERVER_HOSTNAME")
    HTTP_PATH = os.getenv("UAT_DBX_WAREHOUSE_HTTP_PATH")
    ACCESS_TOKEN = os.getenv("UAT_DBX_ACCESS_TOKEN")
