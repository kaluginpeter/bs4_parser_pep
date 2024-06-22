from urllib.parse import urljoin
import re
import logging
from collections import defaultdict

from bs4 import BeautifulSoup
from tqdm import tqdm
import requests_cache

from constants import BASE_DIR, MAIN_DOC_URL, MAIN_PEP_URL, EXPECTED_STATUS
from configs import configure_argument_parser, configure_logging
from outputs import control_output
from utils import get_response, find_tag


def whats_new(session):
    whats_new_url = urljoin(MAIN_DOC_URL, 'whatsnew/')
    response = get_response(session, whats_new_url)
    if response is None:
        return
    soup = BeautifulSoup(response.text, features='lxml')
    main_div = find_tag(soup, 'section', attrs={'id': 'what-s-new-in-python'})
    div_with_ul = find_tag(main_div, 'div', attrs={'class': 'toctree-wrapper'})
    sections_by_python = div_with_ul.find_all(
        'li', attrs={'class': 'toctree-l1'}
    )
    results = [('Ссылка на статью', 'Заголовок', 'Редактор, автор')]
    for section in tqdm(sections_by_python, desc='Parsing python versions'):
        version_a_tag = find_tag(section, 'a')
        href = version_a_tag['href']
        version_link = urljoin(whats_new_url, href)
        response = get_response(session, version_link)
        if response is None:
            continue
        soup = BeautifulSoup(response.text, features='lxml')
        h1 = find_tag(soup, 'h1')
        dl = find_tag(soup, 'dl')
        dl_text = dl.text.replace('\n', ' ')
        results.append((version_link, h1.text, dl_text))
    return results


def latest_versions(session):
    response = get_response(session, MAIN_DOC_URL)
    if response is None:
        return
    soup = BeautifulSoup(response.text, features='lxml')
    sidebar = find_tag(soup, 'div', attrs={'class': 'sphinxsidebarwrapper'})
    ul_tags = find_tag(sidebar, 'ul')
    for ul in ul_tags:
        if 'All versions' in ul.text:
            a_tags = find_tag(ul, 'a')
            break
    else:
        raise Exception('Find None matches!')
    results = [('Link on docs', 'Version', 'Status')]
    # Шаблон для поиска версии и статуса:
    pattern = r'Python (?P<version>\d\.\d+) \((?P<status>.*)\)'
    # Цикл для перебора тегов <a>, полученных ранее.
    for a_tag in a_tags:
        # Напишите новый код, ориентируясь на план.
        link = a_tag.get('href')
        re_match = re.search(pattern, a_tag.text)
        if re_match:
            version, status = re_match.groups()
        else:
            version = a_tag.text
            status = ''
        results.append((link, version, status))
    # Печать результата.
    return results


def download(session):
    downloads_url = urljoin(MAIN_DOC_URL, 'download.html')
    download_dir = BASE_DIR / 'downloads'
    download_dir.mkdir(exist_ok=True)
    response = get_response(session, downloads_url)
    if response is None:
        return
    soup = BeautifulSoup(response.text, features='lxml')
    div_bar = find_tag(soup, 'table', attrs={'class': 'docutils'})
    pdf_a4_tag = find_tag(
        div_bar, 'a', attrs={'href': re.compile(r'.+pdf-a4\.zip$')}
    )
    pdf_a4_link = pdf_a4_tag.get('href')
    archive_url = urljoin(downloads_url, pdf_a4_link)
    filename = archive_url.split('/')[-1]
    archive_path = download_dir / filename
    response = session.get(archive_url)
    with open(archive_path, 'wb') as file:
        file.write(response.content)
    logging.info(
        f'Archive with documentation been saved, on path: {archive_path}'
    )


def pep(session):
    count_statused: defaultdict = defaultdict(int)
    response = get_response(session, MAIN_PEP_URL)
    soup = BeautifulSoup(response.text, 'lxml')
    main_category = find_tag(soup, 'section', {'id': 'index-by-category'})
    categories = main_category.find_all('section')
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
            soup = BeautifulSoup(response_from_detail_pep_page.text, 'lxml')
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
                msg = (
                    f'Incorrect statuses:\n{detail_pep_url}\n'
                    f'Real status: {status_on_detail_pep_page}\n'
                    f'Excpected statues: '
                    f'{EXPECTED_STATUS.get(status_on_main_page)}\n')
                logging.info(
                    msg
                )
                count_statused[status_on_detail_pep_page] += 1
            else:
                count_statused[status_on_main_page] += 1
    for k, v in count_statused.items():
        results.append((k, v))
    results.append(('Total', sum(count_statused.values())))
    return results


MODE_TO_FUNCTION = {
    'whats-new': whats_new,
    'latest-versions': latest_versions,
    'download': download,
    'pep': pep,
}


def main():
    configure_logging()
    logging.info('Parser launch.')
    arg_parser = configure_argument_parser(MODE_TO_FUNCTION .keys())
    args = arg_parser.parse_args()
    logging.info(f'Cli arguments: {args}')
    parser_mode = args.mode
    session = requests_cache.CachedSession()
    if args.clear_cache:
        session.cache.clear()
    results = MODE_TO_FUNCTION[parser_mode](session)
    if results is not None:
        control_output(results, args)
        logging.info('Parser completed his work.')


if __name__ == '__main__':
    main()
