from famgz_utils import Cookies
from pathlib import Path

_source_path = Path(__file__).resolve()
SOURCE_DIR = _source_path.parent
COOKIES_DIR = Path(SOURCE_DIR, 'cookies')

cookies = Cookies(COOKIES_DIR).get_cookies()
