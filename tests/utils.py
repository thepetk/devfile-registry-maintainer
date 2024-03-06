import logging
import os
import pytest
from pytest import MonkeyPatch
from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class MaintainerTestCase:
    args: Any
    func: Callable
    title: str
    want_error: Exception | None
    want: Any = None
    want_type: Any = None


def run_test_cases(tcs: list[MaintainerTestCase]) -> None:
    for tc in tcs:
        logging.info("running case: {}".format(tc.title))
        # first check if we expect an error
        if tc.want_error:
            with pytest.raises(tc.want_error):
                # set args if tc.args is not none
                assert tc.func() if tc.args is None else tc.func(*tc.args)

        # then check if we want to check the type
        elif tc.want_type:
            assert (
                isinstance(tc.func(), tc.want_type)
                if tc.args is None
                else isinstance(tc.func(*tc.args), tc.want_type)
            )
        else:
            # finally compare the values
            assert (
                tc.func() == tc.want
                if tc.args is None
                else tc.func(*tc.args) == tc.want
            )
