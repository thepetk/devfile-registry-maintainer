import yaml
from tests.utils import MaintainerTestCase, run_test_cases
from maintainer import IndentDumper


def compare_file_content(file1: str, file2: str) -> bool:
    return file1 == file2


def test_increase_indent(
    acceptable_yaml: str,
    test_yaml_dict: dict[str, str],
) -> None:
    dumped = yaml.dump(test_yaml_dict, Dumper=IndentDumper)
    run_test_cases(
        [
            MaintainerTestCase(
                title="check a test yaml file against the ident dumper",
                args=(acceptable_yaml, dumped),
                want=True,
                func=compare_file_content,
                want_error=None,
            ),
        ]
    )
