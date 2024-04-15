from datetime import datetime
from unittest.mock import patch

from maintainer import RegistryStack
from tests.utils import MaintainerTestCase, run_test_cases


def test_get_stack_name(test_registry_stack: RegistryStack) -> None:
    run_test_cases(
        [
            MaintainerTestCase(
                title="get stack name for yaml",
                args=(test_registry_stack.devfile_path,),
                want=test_registry_stack.name,
                func=test_registry_stack._get_stack_name,
                want_error=None,
            ),
            MaintainerTestCase(
                title="get stack name for yml",
                args=(test_registry_stack.devfile_path.replace(".yaml", ".yml"),),
                want=test_registry_stack.name,
                func=test_registry_stack._get_stack_name,
                want_error=None,
            ),
        ]
    )


def test_get_last_modified(test_registry_stack: RegistryStack) -> None:
    run_test_cases(
        [
            MaintainerTestCase(
                title="get last modified success",
                args=(
                    datetime.strftime(
                        test_registry_stack.last_modified, "%a, %d %b %Y %H:%M:%S GMT"
                    ),
                ),
                want=test_registry_stack.last_modified,
                func=test_registry_stack._get_last_modified,
                want_error=None,
            ),
        ]
    )


def test_get_deprecated(
    test_registry_stack: RegistryStack, test_deprecated_registry_stack: RegistryStack
) -> None:
    run_test_cases(
        [
            MaintainerTestCase(
                title="get non deprecated stack",
                args=(test_registry_stack.devfile_content,),
                want=False,
                func=test_registry_stack._get_deprecated,
                want_error=None,
            ),
            MaintainerTestCase(
                title="get deprecated stack",
                args=(test_deprecated_registry_stack.devfile_content,),
                want=True,
                func=test_deprecated_registry_stack._get_deprecated,
                want_error=None,
            ),
        ]
    )


def test_get_owners(
    test_registry_stack: RegistryStack,
    test_registry_stack_no_owners: RegistryStack,
    owners_content: str,
) -> None:
    run_test_cases(
        [
            MaintainerTestCase(
                title="get owners from stack",
                args=(owners_content,),
                want=test_registry_stack.owners,
                func=test_registry_stack._get_owners,
                want_error=None,
            ),
            MaintainerTestCase(
                title="get empty owners from stack",
                args=(None,),
                want=[],
                func=test_registry_stack_no_owners._get_owners,
                want_error=None,
            ),
        ]
    )
