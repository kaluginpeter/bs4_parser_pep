class ParserFindTagException(Exception):
    """Call, when parse cannot find any tag."""


class NoneMatchesException(Exception):
    """Call, when function or programm gets none or zero matches."""


class FailedConnectionException(Exception):
    """Call, when function or programm cannot connect to url."""
