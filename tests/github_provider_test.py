from datetime import datetime
from unittest.mock import patch

from github import Github

from maintainer import DATETIME_STRFTIME_FORMAT, GithubProvider
from tests.mocker import GithubMocker
from tests.utils import MaintainerTestCase, run_test_cases

mocker = GithubMocker()


@patch("maintainer.GITHUB_TOKEN", "sometoken")
def test__init_github(github_provider: GithubProvider) -> None:
    test_token = "test_token"
    run_test_cases(
        [
            MaintainerTestCase(
                title="initialize github success",
                args=(test_token,),
                want_type=Github,
                func=github_provider._init_github,
                want_error=None,
            ),
        ]
    )


@patch(
    "github.Repository.Repository.get_commits",
    mocker.get_commits,
)
@patch(
    "github.Commit.Commit.last_modified",
    mocker.mocked_commit.last_modified_recent_str,
)
def test__get_last_modified_with_commits(github_provider: GithubProvider) -> None:
    run_test_cases(
        [
            MaintainerTestCase(
                title="get last modified with commits",
                args=(mocker.mocked_content_file.to_content_file,),
                want=mocker.mocked_commit.last_modified_recent_str,
                func=github_provider._get_last_modified,
                want_error=None,
            ),
        ]
    )


@patch(
    "github.Repository.Repository.get_commits",
    mocker.get_commits,
)
@patch(
    "github.Commit.Commit.last_modified",
    datetime.strftime(datetime.now(), DATETIME_STRFTIME_FORMAT),
)
def test__get_last_modified_without_commits(github_provider: GithubProvider) -> None:
    run_test_cases(
        [
            MaintainerTestCase(
                title="get last modified without commits",
                args=(mocker.mocked_content_file.to_content_file,),
                want=mocker.mocked_commit.last_modified_recent_str,
                func=github_provider._get_last_modified,
                want_error=None,
            ),
        ]
    )


@patch(
    "github.Repository.Repository.get_commits",
    mocker.get_commits,
)
@patch(
    "github.Commit.Commit.last_modified",
    datetime.strftime(datetime.now(), DATETIME_STRFTIME_FORMAT),
)
def test__get_repo_items(github_provider: GithubProvider) -> None:
    run_test_cases(
        [
            MaintainerTestCase(
                title="get last modified without commits",
                args=(mocker.mocked_content_file.to_content_file,),
                want=mocker.mocked_commit.last_modified_recent_str,
                func=github_provider._get_last_modified,
                want_error=None,
            ),
        ]
    )
