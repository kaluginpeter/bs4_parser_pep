import datetime as dt
import csv
import logging

from prettytable import PrettyTable

from constants import DATETIME_FORMAT, BASE_DIR, RESULTS_DIR, PRETTY, FILE

empty_data_message = 'Parse mode return None data'


def control_output(results, cli_args):
    if results is None:
        logging.info(empty_data_message)
    output = cli_args.output
    OUTPUT_FUNCTIONS = {
        PRETTY: pretty_output,
        FILE: file_output,
    }
    OUTPUT_FUNCTIONS.get(output, default_output)(results, cli_args)


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
    now = dt.datetime.now()
    now_formatted = now.strftime(DATETIME_FORMAT)
    file_name = f'{parser_mode}_{now_formatted}.csv'
    file_path = result_dir / file_name
    with open(file_path, 'w', encoding='utf-8') as f:
        writer = csv.writer(f, dialect=csv.unix_dialect)
        writer.writerows(results)
    logging.info(f'File with parsed data been saved, on path: {file_path}')
