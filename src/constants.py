from urllib.parse import urljoin
from pathlib import Path
# Urls
MAIN_DOC_URL = 'https://docs.python.org/3/'
MAIN_PEP_URL = 'https://peps.python.org/'
WHATS_NEW_URL = urljoin(MAIN_DOC_URL, 'whatsnew/')
DOWNLOAD_URL = urljoin(MAIN_DOC_URL, 'download.html')

# Dirrectories and local files
BASE_DIR = Path(__file__).parent
LOGGING_DIR = BASE_DIR / 'logs'
LOGGING_FILE_DIR = LOGGING_DIR / 'parser.log'
RESULTS_DIR = 'results'
DOWNLOAD_DIR = 'downloads'

# Time format
DATETIME_FORMAT = '%Y-%m-%d_%H-%M-%S'
DT_FORMAT = '%d.%m%Y %H:%M:%S'

# Parsing information
EXPECTED_STATUS = {
    'A': ('Active', 'Accepted'),
    'D': ('Deferred',),
    'F': ('Final',),
    'P': ('Provisional',),
    'R': ('Rejected',),
    'S': ('Superseded',),
    'W': ('Withdrawn',),
    '': ('Draft', 'Active'),
}
LOG_FORMAT = '"(asctime)s - [%(levelname)s] - %(message)s"'
PRETTY = 'pretty'
FILE = 'file'
