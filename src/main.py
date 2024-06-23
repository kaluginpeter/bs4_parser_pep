from collections import defaultdict
import logging
import re
from urllib.parse import urljoin

from tqdm import tqdm
import requests_cache

from constants import (
    BASE_DIR, MAIN_DOC_URL,
    MAIN_PEP_URL, EXPECTED_STATUS,
    WHATS_NEW_URL, DOWNLOAD_URL,
    DOWNLOAD_DIR
)
from configs import configure_argument_parser, configure_logging
from exceptions import NoneMatchesException
from outputs import control_output
from utils import find_tag, creating_soup

SUCCESSFUL_DOWNLOAD_MESSAGE = (
    'Archive with documentation been '
    'saved, on path: {archive_path}'
)
INITIAL_PARSER_MESSAGE = 'Parser launch.'
COMMAND_LINE_ARGUMENTS_MESSAGE = 'Cli arguments: {args}'
FINAL_PARSER_MESSAGE = 'Parser completed his work.'
ERROR_CONNECTION_TO_URL = 'Cannot connection to url! Error: {error}'
ERROR_NOT_MATCHES = 'Find None matches!'
ERROR_PARSER_FINAL_PART = 'Parser got next error: {traceback}'
ERROR_NOT_EQUAL_PEP_STATUSES = (
    'Incorrect statuses:\n{detail_pep_url}\n'
    'Real status: {status_on_detail_pep_page}\n'
    'Excpected statues: '
    '{excepcted_status}\n'
)


def whats_new(session):
    try:
        soup = creating_soup(session, WHATS_NEW_URL)
    except ConnectionError as error:
        logging.error(
            ERROR_CONNECTION_TO_URL.format(error=error)
        )
    errors = []
    results = [('Ссылка на статью', 'Заголовок', 'Редактор, автор')]
    for tag_a in tqdm(
        soup.select(
            '#what-s-new-in-python div.toctree-wrapper li.toctree-l1 > a'
        ),
        desc='Parsing python versions'
    ):
        href = tag_a.get('href')
        version_link = urljoin(WHATS_NEW_URL, href)
        try:
            soup = creating_soup(session, version_link)
        except ConnectionError as error:
            errors.append(ERROR_CONNECTION_TO_URL.format(error=error))
        results.append(
            (
                version_link,
                find_tag(soup, 'h1').text,
                find_tag(soup, 'dl').text.replace('\n', ' ')
            )
        )
    [map(logging.error, errors)]
    return results


def latest_versions(session):
    try:
        soup = creating_soup(session, MAIN_DOC_URL)
    except ConnectionError as error:
        logging.error(
            ERROR_CONNECTION_TO_URL.format(error=error)
        )
    sidebar = find_tag(soup, 'div', attrs={'class': 'sphinxsidebarwrapper'})
    ul_tags = find_tag(sidebar, 'ul')
    for ul in ul_tags:
        if 'All versions' in ul.text:
            a_tags = find_tag(ul, 'a')
            break
    else:
        raise NoneMatchesException(ERROR_NOT_MATCHES)
    results = [('Link on docs', 'Version', 'Status')]
    # Pattern for searching version and status:
    pattern = r'Python (?P<version>\d\.\d+) \((?P<status>.*)\)'
    for a_tag in a_tags:
        link = a_tag.get('href')
        re_match = re.search(pattern, a_tag.text)
        if re_match:
            version, status = re_match.groups()
        else:
            version = a_tag.text
            status = ''
        results.append((link, version, status))
    return results


def download(session):
    downloads_url = DOWNLOAD_URL
    download_dir = BASE_DIR / DOWNLOAD_DIR
    download_dir.mkdir(exist_ok=True)
    try:
        soup = creating_soup(session, DOWNLOAD_URL)
    except ConnectionError as error:
        logging.error(
            ERROR_CONNECTION_TO_URL.format(error=error)
        )
    pdf_a4_link = next(
        (
            a['href'] for a in soup.select('table.docutils a[href]')
            if re.search(r'.+pdf-a4\.zip$', a['href'])
        ), None
    )
    archive_url = urljoin(downloads_url, pdf_a4_link)
    filename = archive_url.split('/')[-1]
    archive_path = download_dir / filename
    response = session.get(archive_url)
    with open(archive_path, 'wb') as file:
        file.write(response.content)
    logging.info(
        SUCCESSFUL_DOWNLOAD_MESSAGE.format(archive_path=archive_path)
    )


def pep(session):
    count_status_of_peps = defaultdict(int)
    try:
        soup = creating_soup(session, MAIN_PEP_URL)
    except ConnectionError as error:
        logging.error(
            ERROR_CONNECTION_TO_URL.format(error=error)
        )
    main_category = find_tag(soup, 'section', {'id': 'index-by-category'})
    categories = main_category.find_all('section')
    not_equal_statuses = []
    incorrect_urls = []
    for category in categories:
        peps_in_category = category.find_all('tr')
        for pep in tqdm(peps_in_category[1:], desc='Parsing pep categories'):
            title = find_tag(pep, 'abbr')
            link_prefix = find_tag(
                pep, 'a', {'class': 'pep reference internal'}
            ).text
            detail_pep_url = urljoin(MAIN_PEP_URL, link_prefix)
            status_on_main_page = (
                '' if len(title.text) == 1 else title.text[1:]
            )
            try:
                soup = creating_soup(
                    session, detail_pep_url
                )
            except ConnectionError as error:
                incorrect_urls.append(
                    ERROR_CONNECTION_TO_URL.format(error=error)
                )
            table_on_detail_page = find_tag(
                soup, 'dl', {'class': 'rfc2822 field-list simple'}
            )
            current_sibling = table_on_detail_page.dt
            for sibling in tqdm(
                current_sibling.find_next_siblings('dt'),
                desc='Parsing detail pep data'
            ):
                if sibling.find(string='Status'):
                    status_on_detail_pep_page = sibling.find_next_sibling(
                        'dd'
                    ).string
                    break
            if status_on_detail_pep_page not in EXPECTED_STATUS.get(
                status_on_main_page
            ):
                not_equal_statuses.append(
                    ERROR_NOT_EQUAL_PEP_STATUSES.format(
                        detail_pep_url=detail_pep_url,
                        status_on_detail_pep_page=status_on_detail_pep_page,
                        ecxpected_status=EXPECTED_STATUS.get(
                            status_on_main_page
                        )
                    )
                )
                count_status_of_peps[status_on_detail_pep_page] += 1
            else:
                count_status_of_peps[status_on_main_page] += 1
    [map(logging.error, incorrect_urls)]
    [map(logging.info, not_equal_statuses)]
    return [
        ('Результаты', 'Количество'),
        *count_status_of_peps.items(),
        ('Всего', sum(count_status_of_peps.values()))
    ]


MODE_TO_FUNCTION = {
    'whats-new': whats_new,
    'latest-versions': latest_versions,
    'download': download,
    'pep': pep,
}


def main():
    configure_logging()
    logging.info(INITIAL_PARSER_MESSAGE)
    arg_parser = configure_argument_parser(MODE_TO_FUNCTION .keys())
    args = arg_parser.parse_args()
    logging.info(COMMAND_LINE_ARGUMENTS_MESSAGE)
    parser_mode = args.mode
    try:
        session = requests_cache.CachedSession()
        if args.clear_cache:
            session.cache.clear()
    except Exception as error:
        logging.error(ERROR_PARSER_FINAL_PART.format(traceback=error))
    results = MODE_TO_FUNCTION[parser_mode](session)
    try:
        control_output(results, args)
        logging.info(FINAL_PARSER_MESSAGE)
    except Exception as error:
        logging.error(ERROR_PARSER_FINAL_PART.format(traceback=error))


if __name__ == '__main__':
    main()
