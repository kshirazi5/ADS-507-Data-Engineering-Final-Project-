import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("AZURE_DB_HOST"),
    "user": os.getenv("AZURE_DB_USER"),
    "password": os.getenv("AZURE_DB_PASSWORD"),
    "database": os.getenv("AZURE_DB_NAME"),
    "port": int(os.getenv("AZURE_DB_PORT", 3306)),
    "ssl_disabled": False,
    "ssl_verify_cert": False,
}

# If a CA certificate is required, set AZURE_SSL_CA in .env
# and uncomment the block below (or it activates automatically):
ssl_ca_path = os.getenv("AZURE_SSL_CA")
if ssl_ca_path:
    DB_CONFIG["ssl_ca"] = ssl_ca_path
    DB_CONFIG["ssl_verify_cert"] = True

SQLALCHEMY_URL = (
    f"mysql+mysqlconnector://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
    f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
)

SQLALCHEMY_CONNECT_ARGS = {
    "ssl_disabled": DB_CONFIG["ssl_disabled"],
    "ssl_verify_cert": DB_CONFIG["ssl_verify_cert"],
}
if ssl_ca_path:
    SQLALCHEMY_CONNECT_ARGS["ssl_ca"] = ssl_ca_path
