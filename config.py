import os
from os import getenv

API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

BOT_USERNAME = getenv("BOT_USERNAME", "EsproChatBot")

OWNER_ID = list(map(int, getenv("OWNER_ID", "7666870729").split()))

# Fill Only Username Without @
SUPPORT_GROUP = getenv("SUPPORT_GROUP", "EsproSupport")

MONGO_URL = os.environ.get("MONGO_URL")

LOGGER_ID = int(getenv("LOGGER_ID", "-1002861883767"))

# Set True if you want to set bot commands automatically
SETCMD = getenv("SETCMD", "True")

# Upstream repo
UPSTREAM_REPO = getenv(
    "UPSTREAM_REPO", "https://github.com/RitikRohin/EsproChatBot"
)

UPSTREAM_BRANCH = getenv("UPSTREAM_BRANCH", "main")

# GIT TOKEN (if your edited repo is private)
GIT_TOKEN = getenv("GIT_TOKEN", None)

# Sightengine API credentials
SIGHTENGINE_API_USER = getenv("SIGHTENGINE_API_USER", "1916313622")
SIGHTENGINE_API_SECRET = getenv("SIGHTENGINE_API_SECRET", "frPDtcGYH42kUkmsKuGoj9SVYHCMW9QA")

# Optional safety check
if not SIGHTENGINE_API_USER or not SIGHTENGINE_API_SECRET:
    raise Exception("Sightengine credentials are missing in config.")
