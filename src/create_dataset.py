import sys
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


if __name__ == '__main__':
    dc = DatasetCreator(
        name='boop',
        yaml_code='this is yaml',
        transform_py_code='print("this is python")',
        sql_code='this is sql',
        test_py_code='print("this is test python")'
    )
    if len(sys.argv) > 1:
        dc.undo()
        print("UNDONE")
    else:
        dc.execute()
        print("DONE")
