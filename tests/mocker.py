from datetime import datetime, timedelta
from github.Commit import Commit
from github.ContentFile import ContentFile
from github.Requester import Requester
from dataclasses import dataclass

from maintainer import DATETIME_STRFTIME_FORMAT, DEPRECATION_DAYS_LIMIT

MOCKED_REQUESTER = Requester(
    auth="some_auth",
    base_url="https://some.base.url",
    timeout=1,
    user_agent="some_agent",
    per_page=1,
    verify=True,
    retry=1,
    pool_size=1,
)
MOCKED_HEADERS = {"server": "server"}


@dataclass
class MockedGithubCommit:
    last_modified_expired: datetime = datetime.now() - timedelta(
        days=DEPRECATION_DAYS_LIMIT + 10
    )
    last_modified_recent: datetime = datetime.now()

    @property
    def last_modified_recent_str(self) -> str:
        return datetime.strftime(
            self.last_modified_recent,
            DATETIME_STRFTIME_FORMAT,
        )

    @property
    def last_modified_expired_str(self) -> str:
        return datetime.strftime(
            self.last_modified_expired,
            DATETIME_STRFTIME_FORMAT,
        )

    @property
    def _attrs(self) -> dict[str, str | list[str]]:
        return {
            "author": "user",
            "comments_url": "https://comments.url",
            "commit": "create",
            "committer": "user",
            "files": [
                "somefile.yaml",
            ],
        }

    @property
    def to_commit(self) -> "Commit":
        return Commit(
            requester=MOCKED_REQUESTER,
            headers=MOCKED_HEADERS,
            attributes=self._attrs,
            completed=True,
        )


@dataclass
class MockedGithubContentFile:
    def get_attrs(self) -> dict[str, str]:
        return {
            "path": "some/path",
        }

    @property
    def to_content_file(self) -> "ContentFile":
        return ContentFile(
            requester=MOCKED_REQUESTER,
            headers=MOCKED_HEADERS,
            attributes=self.get_attrs(),
            completed=True,
        )


@dataclass
class GithubMocker:
    mocked_commit: MockedGithubCommit = MockedGithubCommit()
    mocked_content_file: MockedGithubContentFile = MockedGithubContentFile()

    def get_commits(self, path: str) -> "list[Commit]":
        return [self.mocked_commit.to_commit]
