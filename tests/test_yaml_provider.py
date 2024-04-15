import io

from ruamel.yaml import YAML

from tests.utils import MaintainerTestCase, run_test_cases


def compare_file_content(file1: str, file2: str) -> bool:
    return file1 == file2


def test_get_YAML(
    acceptable_yaml: str,
    test_yaml_dict: dict[str, str],
    yaml_provider: YAML,
) -> None:
    _buf = io.StringIO()
    _ = yaml_provider.dump(test_yaml_dict, _buf)
    run_test_cases(
        [
            MaintainerTestCase(
                title="check a test yaml file against yaml file dumped from yaml_provider",
                args=(acceptable_yaml, _buf.getvalue()),
                want=True,
                func=compare_file_content,
                want_error=None,
            ),
        ]
    )
