import logging
from unittest.mock import patch
from tests.utils import MaintainerTestCase, run_test_cases
from maintainer import get_int_env_var, get_logging_level


def test_get_int_env_var() -> None:
    run_test_cases(
        [
            MaintainerTestCase(
                title="get int env var success",
                args=("TEST_ENV_VAR", "1"),
                want=1,
                func=get_int_env_var,
                want_error=None,
            ),
            MaintainerTestCase(
                title="get int env var failure",
                args=("TEST_ENV_VAR", "one"),
                func=get_int_env_var,
                want_error=SystemExit,
            ),
        ]
    )


@patch("maintainer.DEBUG_MODE", 0)
def test_get_logging_level_info() -> None:
    run_test_cases(
        [
            MaintainerTestCase(
                title="get logging level with DEBUG_MODE unset",
                args=None,
                want=logging.INFO,
                func=get_logging_level,
                want_error=None,
            ),
        ],
    )


@patch("maintainer.DEBUG_MODE", 1)
def test_get_logging_level_debug() -> None:
    run_test_cases(
        [
            MaintainerTestCase(
                title="get logging level with DEBUG_MODE set",
                args=None,
                want=logging.DEBUG,
                func=get_logging_level,
                want_error=None,
            ),
        ],
    )
