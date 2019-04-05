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


def create_dataset(
    name,
    yaml_code,
    transform_py_code,
    sql_code,
    test_py_code,
):
    yaml_path = DATASETS_DIR / f"{name}.yml"
    sql_path = SQL_DIR / f"{name}.sql"
    test_py_path = TEST_DIR / f"test_{name}.py"
    # TODO: Write `yaml_code` to `yaml_path`.
    # TODO: Append `transform_py_code` to `TRANSFORMATIONS_PY_PATH`.
    # TODO: Write 'sql_code' to `sql_path`.
    # TODO: Write `test_py_code` to `test_py_path`.
