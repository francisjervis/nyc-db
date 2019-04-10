import sys
import re
import argparse
import textwrap
import csv
from pathlib import Path

import nycdb


MY_DIR = Path(__file__).parent.resolve()

NYCDB_DIR = MY_DIR / 'nycdb'

DATASETS_DIR = NYCDB_DIR / 'datasets'

TRANSFORMATIONS_PY_PATH = NYCDB_DIR / 'dataset_transformations.py'

SQL_DIR = NYCDB_DIR / 'sql'

TEST_DIR = MY_DIR / 'tests' / 'integration'

NYCDB_TEST_PY_PATH = TEST_DIR / 'test_nycdb.py'

TEST_DATA_DIR = TEST_DIR / 'data'

assert DATASETS_DIR.exists()
assert TRANSFORMATIONS_PY_PATH.exists()
assert SQL_DIR.exists()
assert TEST_DIR.exists()
assert NYCDB_TEST_PY_PATH.exists()
assert TEST_DATA_DIR.exists()


class DatasetCreator:
    def __init__(
        self,
        name: str,
        yaml_code: str,
        transform_py_code: str,
        sql_code: str,
        test_py_code: str,
        test_csv_text: str
    ) -> None:
        self.name = name
        self.yaml_code = yaml_code
        self.transform_py_code = transform_py_code
        self.sql_code = sql_code
        self.test_py_code = test_py_code
        self.test_csv_text = test_csv_text

        self.yaml_path = DATASETS_DIR / f"{name}.yml"
        self.sql_path = SQL_DIR / f"{name}.sql"
        self.test_csv_path = TEST_DATA_DIR / f"{name}.csv"

    def append_to_file(self, path: Path, text: str) -> None:
        with path.open('a') as f:
            f.write(self._with_leading_newlines(text))

    def unappend_from_file(self, path: Path, text: str) -> None:
        path.write_text(
            path.read_text().replace(
                self._with_leading_newlines(text),
                ''
            )
        )

    def _with_leading_newlines(self, text: str) -> str:
        return f"\n\n{text}"

    def execute(self) -> None:
        self.undo()
        self.yaml_path.write_text(self.yaml_code)
        self.sql_path.write_text(self.sql_code)
        self.test_csv_path.write_text(self.test_csv_text)
        self.append_to_file(TRANSFORMATIONS_PY_PATH, self.transform_py_code)
        self.append_to_file(NYCDB_TEST_PY_PATH, self.test_py_code)

    def undo(self) -> None:
        paths = [
            self.yaml_path,
            self.sql_path,
            self.test_csv_path
        ]
        for path in paths:
            if path.exists():
                path.unlink()
        self.unappend_from_file(TRANSFORMATIONS_PY_PATH, self.transform_py_code)
        self.unappend_from_file(NYCDB_TEST_PY_PATH, self.test_py_code)


def is_valid_identifier(path: str) -> bool:
    '''
    Returns whether the argument is a valid Python identifier
    that starts with an alphabetic character or an underscore
    and contains only alphanumeric characters or underscores
    thereafter, e.g.:

        >>> is_valid_identifier('boop')
        True
        >>> is_valid_identifier('0boop')
        False
        >>> is_valid_identifier('_boop')
        True
        >>> is_valid_identifier('@#$@!#$')
        False
    '''

    return bool(re.match(r'^[A-Za-z_][A-Za-z0-9_]+$', path))


# https://stackoverflow.com/a/19053800
def to_camel_case(snake_str: str) -> str:
    '''
    Convert the given string to camel case, e.g.:

        >>> to_camel_case('boop_bap')
        'BoopBap'
    '''

    components = snake_str.split('_')
    return ''.join(x.title() for x in components)


def cleanup_text(text: str) -> str:
    return textwrap.dedent(text).lstrip()


def get_head(filepath: Path, max_lines: int) -> str:
    lines = []
    i = 0
    with filepath.open('r') as f:
        for line in f.readlines():
            lines.append(line)
            i += 1
            if i >= max_lines:
                break
    return ''.join(lines)


def generate_yaml_code(dataset: str, csvpath: Path) -> str:
    with csvpath.open('r') as f:
        reader = csv.reader(f)
        header_row = next(reader)
    fields = '\n        '.join([
        f"{to_camel_case(name)}: text" for name in header_row
    ])
    return cleanup_text(f"""
    ---
    files:
      -
        # TODO: Change this to a real URL!
        url: https://SOME-DOMAIN.ORG/SOME-PATH/{dataset}.csv
        dest: {dataset}.csv
    schema:
      table_name: {dataset}
      fields:
        # TODO: The data types for these fields likely aren't ideal!
        {fields}
    """)


def generate_transform_py_code(dataset: str) -> str:
    return cleanup_text(f"""
    def {dataset}(dataset):
        return to_csv(dataset.files[0].dest)
    """)


def generate_test_py_code(dataset: str) -> str:
    return cleanup_text(f"""
    def test_{dataset}(conn):
        drop_table(conn, '{dataset}')
        dataset = nycdb.Dataset('{dataset}', args=ARGS)
        dataset.db_import()
        assert row_count(conn, '{dataset}') > 0
    """)


def generate_sql_code(dataset: str) -> str:
    return cleanup_text(f"""
    CREATE INDEX {dataset}_bbl_idx on {dataset} (bbl);
    """)


def fail(msg: str) -> None:
    sys.stderr.write(f"{msg}\n")
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Create scaffolding for a new NYC-DB dataset."
    )
    parser.add_argument(
        'csvfile',
        help='The CSV file to base the new dataset on.'
    )
    parser.add_argument(
        '--undo',
        action='store_true',
        help='Attempt to undo the creation of the scaffolding.'
    )
    args = parser.parse_args()

    csvpath = Path(args.csvfile)

    if not is_valid_identifier(csvpath.stem):
        fail(
            f"'{csvpath.stem}' can contain only alphanumeric characters/underscores,\n"
            f"and cannot start with a number."
        )

    if not csvpath.exists():
        fail(f"'{csvpath}' does not exist!")

    dc = DatasetCreator(
        name=csvpath.stem,
        yaml_code=generate_yaml_code(csvpath.stem, csvpath),
        transform_py_code=generate_transform_py_code(csvpath.stem),
        sql_code=generate_sql_code(csvpath.stem),
        test_py_code=generate_test_py_code(csvpath.stem),
        test_csv_text=get_head(csvpath, max_lines=101),
    )

    if args.undo:
        print(f"Undoing scaffolding for dataset '{dc.name}'.")
        dc.undo()
    else:
        dc.execute()
        print(f"Scaffolding created for new dataset '{dc.name}'.")


if __name__ == '__main__':
    main()
