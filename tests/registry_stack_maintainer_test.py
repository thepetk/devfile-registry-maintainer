from datetime import datetime, timedelta

from maintainer import RegistryStack, RegistryStackMaintainer
from tests.utils import MaintainerTestCase, run_test_cases


def test_update(
    test_registry_stack: RegistryStack,
    test_expired_non_deprecated_registry_stack: RegistryStack,
    test_deprecated_registry_stack: RegistryStack,
    registry_stack_maintainer: RegistryStackMaintainer,
) -> None:
    run_test_cases(
        [
            MaintainerTestCase(
                title="update already deprecated stack",
                args=(test_deprecated_registry_stack,),
                want=registry_stack_maintainer._remove(test_deprecated_registry_stack),
                func=registry_stack_maintainer.update,
                want_error=None,
            ),
            MaintainerTestCase(
                title="update not expired stack",
                args=(test_registry_stack,),
                want=None,
                func=registry_stack_maintainer.update,
                want_error=None,
            ),
            MaintainerTestCase(
                title="update expired but not deprecated stack",
                args=(test_expired_non_deprecated_registry_stack,),
                want=registry_stack_maintainer._deprecate(
                    test_expired_non_deprecated_registry_stack
                ),
                func=registry_stack_maintainer.update,
                want_error=None,
            ),
        ]
    )


def test_limit_reached(registry_stack_maintainer: RegistryStackMaintainer) -> None:
    run_test_cases(
        [
            MaintainerTestCase(
                title="limit has been reached",
                args=((datetime.now() - timedelta(days=(365 + 2))), 365),
                want=True,
                func=registry_stack_maintainer._limit_reached,
                want_error=None,
            ),
            MaintainerTestCase(
                title="limit has not been reached",
                args=((datetime.now() - timedelta(days=(365 - 2))), 365),
                want=False,
                func=registry_stack_maintainer._limit_reached,
                want_error=None,
            ),
        ]
    )


def test_add_owners_mention(registry_stack_maintainer: RegistryStackMaintainer) -> None:
    desc_list = ["This is a test PR"]
    owners = ["test_owner"]
    new_line = "The PR should be reviewed by: @test_owner"
    run_test_cases(
        [
            MaintainerTestCase(
                title="owners exist",
                args=(desc_list, owners),
                want=desc_list + [new_line],
                func=registry_stack_maintainer._add_owners_mention,
                want_error=None,
            ),
            MaintainerTestCase(
                title="owners do not exist",
                args=(desc_list, []),
                want=desc_list,
                func=registry_stack_maintainer._add_owners_mention,
                want_error=None,
            ),
        ]
    )
