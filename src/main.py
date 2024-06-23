from collections import defaultdict
import logging
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup
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
from utils import get_response, find_tag, creating_soup

error_connection_with_url_message = 'Cannot connect to {url}!'
successfull_download_message = (
    'Archive with documentation been '
    'saved, on path: {archive_path}'
)
initial_parser_message = 'Parser launch.'
command_line_arguments_message = 'Cli arguments: {args}'
final_parser_message = 'Parser completed his work.'


def whats_new(session):
    response = get_response(session, WHATS_NEW_URL)
    if response is None:
        logging.error(
            msg=error_connection_with_url_message.format(WHATS_NEW_URL)
        )
        return
    soup = creating_soup(response.text)
    sections_by_python = soup.select(
        '#what-s-new-in-python div.toctree-wrapper li.toctree-l1'
    )
    results = [('Ссылка на статью', 'Заголовок', 'Редактор, автор')]
    for section in tqdm(sections_by_python, desc='Parsing python versions'):
        version_a_tag = find_tag(section, 'a')
        href = version_a_tag.get('href')
        version_link = urljoin(WHATS_NEW_URL, href)
        response = get_response(session, version_link)
        if response is None:
            logging.error(
                msg=error_connection_with_url_message.format(url=version_link)
            )
            continue
        soup = creating_soup(response.text)
        results.append(
            (
                version_link,
                find_tag(soup, 'h1').text,
                find_tag(soup, 'dl').text.replace('\n', ' ')
            )
        )
    return results


def latest_versions(session):
    response = get_response(session, MAIN_DOC_URL)
    if response is None:
        logging.error(
            msg=error_connection_with_url_message.format(url=MAIN_DOC_URL)
        )
        return
    soup = creating_soup(response.text)
    sidebar = find_tag(soup, 'div', attrs={'class': 'sphinxsidebarwrapper'})
    ul_tags = find_tag(sidebar, 'ul')
    for ul in ul_tags:
        if 'All versions' in ul.text:
            a_tags = find_tag(ul, 'a')
            break
    else:
        raise NoneMatchesException('Find None matches!')
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
    response = get_response(session, downloads_url)
    if response is None:
        logging.error(
            msg=error_connection_with_url_message.format(downloads_url)
        )
        return
    soup = creating_soup(response.text)
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
        msg=successfull_download_message.format(archive_path=archive_path)
    )


def pep(session):
    count_statused = defaultdict(int)
    response = get_response(session, MAIN_PEP_URL)
    soup = creating_soup(response.text)
    main_category = find_tag(soup, 'section', {'id': 'index-by-category'})
    categories = main_category.find_all('section')
    not_equal_statuses = []
    for category in categories:
        peps_in_category = category.find_all('tr')
        results = [('Status', 'Quantity')]
        for pep in tqdm(peps_in_category[1:], desc='Parsing pep categories'):
            title = find_tag(pep, 'abbr')
            link_prefix = find_tag(
                pep, 'a', {'class': 'pep reference internal'}
            ).text
            detail_pep_url = urljoin(MAIN_PEP_URL, link_prefix)
            status_on_main_page = (
                '' if len(title.text) == 1 else title.text[1:]
            )
            response_from_detail_pep_page = get_response(
                session, detail_pep_url
            )
            if response_from_detail_pep_page is None:
                logging.error(
                    msg=error_connection_with_url_message.format(
                        url=detail_pep_url
                    )
                )
            soup = creating_soup(response_from_detail_pep_page.text)
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
                    (f'Incorrect statuses:\n{detail_pep_url}\n'
                     f'Real status: {status_on_detail_pep_page}\n'
                     f'Excpected statues: '
                     f'{EXPECTED_STATUS.get(status_on_main_page)}\n')
                )
                count_statused[status_on_detail_pep_page] += 1
            else:
                count_statused[status_on_main_page] += 1
    for status_message in not_equal_statuses:
        logging.info(
            msg=status_message
        )
    return [
        ('Результаты', 'Количество'),
        *count_statused.items(),
        ('Всего', sum(count_statused.values()))
    ]


MODE_TO_FUNCTION = {
    'whats-new': whats_new,
    'latest-versions': latest_versions,
    'download': download,
    'pep': pep,
}


def main():
    configure_logging()
    logging.info(initial_parser_message)
    arg_parser = configure_argument_parser(MODE_TO_FUNCTION .keys())
    args = arg_parser.parse_args()
    logging.info(command_line_arguments_message)
    parser_mode = args.mode
    session = requests_cache.CachedSession()
    if args.clear_cache:
        session.cache.clear()
    results = MODE_TO_FUNCTION[parser_mode](session)
    control_output(results, args)
    logging.info(final_parser_message)


if __name__ == '__main__':
    main()
