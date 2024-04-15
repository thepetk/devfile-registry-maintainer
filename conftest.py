import os
from datetime import datetime, timedelta

import pytest

from maintainer import (
    DEPRECATION_DAYS_LIMIT,
    GithubProvider,
    RegistryStack,
    RegistryStackMaintainer,
    get_YAML,
)


@pytest.fixture(scope="session")
def acceptable_yaml():
    yield open("tests/resources/check_dumper.yaml").read()


@pytest.fixture(scope="session")
def test_yaml_dict():
    yield {"testblock": ["testvalue"]}


@pytest.fixture(scope="session")
def owners_content():
    yield "reviewers:\n - maintainer"


@pytest.fixture(scope="session")
def test_registry_stack(owners_content: str):
    yield RegistryStack(
        path="stacks/test-stack/1.1.0/devfile.yaml",
        raw_content="metadata:\n title: test-stack\n tags:\n - tag",
        last_modified="Sun, 03 Mar 2024 22:01:01 GMT",
        file_sha="somesha",
        owners_content=owners_content,
    )


@pytest.fixture(scope="session")
def test_expired_non_deprecated_registry_stack(owners_content: str):
    yield RegistryStack(
        path="stacks/test-stack/1.2.0/devfile.yaml",
        raw_content="metadata:\n title: test-stack\n tags:\n - tag",
        last_modified="Sun, 03 Mar 2022 22:01:01 GMT",
        file_sha="somesha",
        owners_content=owners_content,
    )


@pytest.fixture(scope="session")
def test_deprecated_registry_stack(owners_content: str):
    yield RegistryStack(
        path="stacks/test-stack/1.1.0/devfile.yaml",
        raw_content="metadata:\n title: test-stack\n tags:\n - Deprecated",
        last_modified=datetime.strftime(
            (datetime.now() - timedelta(days=DEPRECATION_DAYS_LIMIT)),
            "%a, %d %b %Y %H:%M:%S GMT",
        ),
        file_sha="somesha",
        owners_content=owners_content,
    )


@pytest.fixture(scope="session")
def test_registry_stack_no_owners():
    yield RegistryStack(
        path="stacks/test-stack/1.1.0/devfile.yaml",
        raw_content="metadata:\n title: test-stack\n tags:\n - tag",
        last_modified="Sun, 03 Mar 2024 22:01:01 GMT",
        file_sha="somesha",
        owners_content=None,
    )


@pytest.fixture(scope="session")
def github_provider():
    os.environ["TEST_MODE"] = "1"
    yield GithubProvider(token="test-token")


@pytest.fixture(scope="session")
def yaml_provider():
    yield get_YAML()


@pytest.fixture(scope="session")
def registry_stack_maintainer():
    yield RegistryStackMaintainer()
