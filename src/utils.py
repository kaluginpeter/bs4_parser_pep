from bs4 import BeautifulSoup
from requests import RequestException

from exceptions import ParserFindTagException

error_message = 'Не найден тег {tag} {attrs}'


def get_response(session, url, encoding='utf-8'):
    try:
        response = session.get(url)
        response.encoding = encoding
        return response
    except RequestException:
        raise RequestException(
            f'Error been given in the moment connect with url {url}',
            stack_info=True
        )


def find_tag(soup, tag, attrs=None):
    attrs = attrs if attrs is not None else {}
    searched_tag = soup.find(tag, attrs=attrs)
    if searched_tag is None:
        raise ParserFindTagException(
            error_message.format(tag=tag, attrs=[None, attrs][bool(attrs)])
        )
    return searched_tag


def creating_soup(text):
    return BeautifulSoup(text, 'lxml')
