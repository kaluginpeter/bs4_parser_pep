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
FIRST_PARSER_MODE = 'pretty'
SECOND_PARSER_MODE = 'file'
DEFAULT_PARSER_MODE = 'default'

# Messages for parser
ERROR_CONNECTION_TO_URL_MESSAGE = (
    'Error been given in the moment connect with url {url}\n'
    'Error message: {traceback}'
)
ERROR_UNFOUNDED_TAG_MESSAGE = 'Не найден тег {tag} {attrs}'
ERROR_NOT_EQUAL_PEP_STATUSES = (
    'Incorrect statuses:\n{detail_pep_url}\n'
    'Real status: {status_on_detail_pep_page}\n'
    'Excpected statues: '
    '{excepcted_status}\n'
)
ERROR_PARSER_FINAL_PART = 'Parser got next error: {traceback}'
SUCCESSFUL_OUTPUT_FILE_MESSAGE = (
    'File with parsed data been saved, '
    'on path: {file_path}'
)
SUCCESSFUL_DOWNLOAD_MESSAGE = (
    'Archive with documentation been '
    'saved, on path: {archive_path}'
)
INITIAL_PARSER_MESSAGE = 'Parser launch.'
COMMAND_LINE_ARGUMENTS_MESSAGE = 'Cli arguments: {args}'
FINAL_PARSER_MESSAGE = 'Parser completed his work.'
