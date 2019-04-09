import sys
import re
import argparse
from pathlib import Path

import nycdb


MY_DIR = Path(__file__).parent.resolve()

NYCDB_DIR = MY_DIR / 'nycdb'

DATASETS_DIR = NYCDB_DIR / 'datasets'

TRANSFORMATIONS_PY_PATH = NYCDB_DIR / 'dataset_transformations.py'

SQL_DIR = NYCDB_DIR / 'sql'

TEST_DIR = MY_DIR / 'tests' / 'integration'

assert DATASETS_DIR.exists()
assert TRANSFORMATIONS_PY_PATH.exists()
assert SQL_DIR.exists()
assert TEST_DIR.exists()


class DatasetCreator:
    def __init__(
        self,
        name: str,
        yaml_code: str,
        transform_py_code: str,
        sql_code: str,
        test_py_code: str,
    ) -> None:
        self.name = name
        self.yaml_code = yaml_code
        self.transform_py_code = transform_py_code
        self.sql_code = sql_code
        self.test_py_code = test_py_code
        self.yaml_path = DATASETS_DIR / f"{name}.yml"
        self.sql_path = SQL_DIR / f"{name}.sql"
        self.test_py_path = TEST_DIR / f"test_{name}.py"

    @property
    def _transform_with_newlines(self) -> str:
        return f"\n\n{self.transform_py_code}"

    def execute(self) -> None:
        self.undo()
        self.yaml_path.write_text(self.yaml_code)
        self.sql_path.write_text(self.sql_code)
        self.test_py_path.write_text(self.test_py_code)
        with TRANSFORMATIONS_PY_PATH.open('a') as f:
            f.write(self._transform_with_newlines)

    def undo(self) -> None:
        paths = [
            self.yaml_path,
            self.sql_path,
            self.test_py_path
        ]
        for path in paths:
            if path.exists():
                path.unlink()
        TRANSFORMATIONS_PY_PATH.write_text(
            TRANSFORMATIONS_PY_PATH.read_text().replace(
                self._transform_with_newlines,
                ''
            )
        )


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
        yaml_code='this is yaml',
        transform_py_code='print("this is python")',
        sql_code='this is sql',
        test_py_code='print("this is test python")'
    )

    if args.undo:
        print(f"Undoing scaffolding for dataset '{dc.name}'.")
        dc.undo()
    else:
        dc.execute()
        print(f"Scaffolding created for new dataset '{dc.name}'.")


if __name__ == '__main__':
    main()
