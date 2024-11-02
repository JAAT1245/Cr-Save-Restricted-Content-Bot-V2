# devggn
# Note if you are trying to deploy on vps then directly fill values in ("")

from os import getenv

API_ID = int(getenv("API_ID", "24894984"))
API_HASH = getenv("API_HASH", "")
BOT_TOKEN = getenv("BOT_TOKEN", "4956e23833905463efb588eb806f9804")
OWNER_ID = list(map(int, getenv("OWNER_ID", "902551614").split()))
MONGO_DB = getenv("MONGO_DB", "")
LOG_GROUP = getenv("LOG_GROUP", "-1002404864606")
CHANNEL_ID = int(getenv("CHANNEL_ID", "-1002182291545"))
