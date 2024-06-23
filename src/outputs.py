import datetime as dt
import csv
import logging

from prettytable import PrettyTable

from constants import (
    DATETIME_FORMAT, BASE_DIR, RESULTS_DIR,
    FIRST_PARSER_MODE, SECOND_PARSER_MODE,
    DEFAULT_PARSER_MODE, SUCCESSFUL_OUTPUT_FILE_MESSAGE
)

empty_data_message = 'Parse mode return None data'


def control_output(results, cli_args):
    output = cli_args.output if cli_args.output else DEFAULT_PARSER_MODE
    OUTPUT_FUNCTIONS.get(output)(results, cli_args)


def default_output(results, args=None):
    for row in results:
        print(*row)


def pretty_output(results, args=None):
    table = PrettyTable()
    table.field_names = (results[0])
    table.align = 'l'
    table.add_rows(results[1:])
    print(table)


def file_output(results, cli_args):
    result_dir = BASE_DIR / RESULTS_DIR
    result_dir.mkdir(exist_ok=True)
    parser_mode = cli_args.mode
    file_name = (
        f'{parser_mode}_'
        f'{dt.datetime.now().strftime(DATETIME_FORMAT)}.csv'
    )
    file_path = result_dir / file_name
    with open(file_path, 'w', encoding='utf-8') as f:
        csv.writer(f, dialect=csv.unix_dialect).writerows(results)
    logging.info(SUCCESSFUL_OUTPUT_FILE_MESSAGE.format(file_path=file_path))


OUTPUT_FUNCTIONS = {
    FIRST_PARSER_MODE: pretty_output,
    SECOND_PARSER_MODE: file_output,
    DEFAULT_PARSER_MODE: default_output,
}
