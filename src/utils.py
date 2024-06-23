from requests import RequestException

from bs4 import BeautifulSoup

from exceptions import ParserFindTagException

ERROR_CONNECTION_TO_URL_MESSAGE = (
    'Error been given in the moment connect with url {url}\n'
    'Error message: {traceback}'
)
ERROR_UNFOUNDED_TAG_MESSAGE = 'Не найден тег {tag} {attrs}'


def get_response(session, url, encoding='utf-8'):
    try:
        response = session.get(url)
        response.encoding = encoding
        return response
    except RequestException as error:
        raise ConnectionError(
            ERROR_CONNECTION_TO_URL_MESSAGE.format(
                url=url, traceback=error
            )
        )


def find_tag(soup, tag, attrs=None):
    attrs = attrs if attrs is not None else {}
    searched_tag = soup.find(tag, attrs=attrs)
    if searched_tag is None:
        raise ParserFindTagException(
            ERROR_UNFOUNDED_TAG_MESSAGE.format(
                tag=tag, attrs=[None, attrs][bool(attrs)]
            )
        )
    return searched_tag


def creating_soup(session, url, features='lxml'):
    return BeautifulSoup(get_response(session, url).text, features)
