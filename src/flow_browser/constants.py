from pathlib import Path

FLOW_URL = "https://labs.google/fx/tools/flow"
GOOGLE_ACCOUNTS_URL = "https://accounts.google.com"

DEFAULT_USER_DATA_DIR = Path.home() / ".flow-browser" / "profile"

DEFAULT_VIEWPORT = {"width": 1440, "height": 900}
DEFAULT_LOCALE = "en-US"

DEFAULT_TIMEOUT_S = 60.0
GENERATION_TIMEOUT_S = 600.0
DOWNLOAD_TIMEOUT_S = 120.0
