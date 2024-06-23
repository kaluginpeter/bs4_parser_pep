from requests import RequestException
from traceback import format_exc

from bs4 import BeautifulSoup

from exceptions import ParserFindTagException, FailedConnectionException
from constants import (
    ERROR_CONNECTION_TO_URL_MESSAGE, ERROR_UNFOUNDED_TAG_MESSAGE
)


def get_response(session, url, encoding='utf-8'):
    try:
        response = session.get(url)
        response.encoding = encoding
        return response
    except RequestException:
        raise FailedConnectionException(
            ERROR_CONNECTION_TO_URL_MESSAGE.format(
                url=url, traceback=format_exc()
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
    failed_connections = []
    response = get_response(session, url)
    if response is None:
        failed_connections.append(
            (
                ERROR_CONNECTION_TO_URL_MESSAGE.format(
                    url=url, traceback=format_exc()
                )
            )
        )
        return [], failed_connections
    return BeautifulSoup(response.text, features), failed_connections
