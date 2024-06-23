import argparse
import logging
from logging.handlers import RotatingFileHandler

from constants import (
    LOG_FORMAT, DT_FORMAT, FIRST_PARSER_MODE,
    SECOND_PARSER_MODE, LOGGING_DIR, LOGGING_FILE_DIR
)


def configure_argument_parser(available_modes):
    parser = argparse.ArgumentParser(description='Python docs parser')
    parser.add_argument(
        'mode',
        choices=available_modes,
        help='Режимы работы парсера'
    )
    parser.add_argument(
        '-c',
        '--clear-cache',
        action='store_true',
        help='Очистка кеша'
    )
    parser.add_argument(
        '-o',
        '--output',
        choices=(FIRST_PARSER_MODE, SECOND_PARSER_MODE),
        help='Дополнительные способы вывода данных'
    )
    return parser


def configure_logging():
    log_dir = LOGGING_DIR
    log_dir.mkdir(exist_ok=True)
    log_file = LOGGING_FILE_DIR
    rotating_handler = RotatingFileHandler(
        log_file, maxBytes=10**6, backupCount=5
    )
    logging.basicConfig(
        datefmt=DT_FORMAT,
        format=LOG_FORMAT,
        level=logging.INFO,
        handlers=(rotating_handler, logging.StreamHandler())
    )
