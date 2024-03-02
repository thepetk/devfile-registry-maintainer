import io
from typing import Any, Literal
from github import Auth, Github
from datetime import datetime, timedelta
from github.ContentFile import ContentFile
from dataclasses import dataclass
import os
import logging

import yaml


TOKEN = os.getenv("GITHUB_TOKEN")
REGISTRY_REPO = os.getenv("REGISTRY_REPO")
DEFAULT_STACKS_PATH = os.getenv("DEFAULT_STACKS_PATH", "stacks")
DEPRECATION_DAYS_LIMIT = int(os.getenv("DEPRECATION_INACTIVITY_LIMIT", "365"))
REMOVAL_DAYS_LIMIT = int(os.getenv("REMOVAL_DEPRECATION_LIMIT", "365"))
DEBUG_MODE = int(os.getenv("DEBUG_MODE", 0))
DEFAULT_BRANCH = "main"
DEPRECATED_TAG = "Deprecated"
PR_CREATION_LIMIT = 1


def get_logging_level():
    if DEBUG_MODE > 0:
        return logging.DEBUG
    return logging.INFO


logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
    level=logging.DEBUG,
)


@dataclass
class RegistryRepoPR:
    action: Literal["deprecate", "remove"]
    branch_name: str
    commit_message: str
    description: str
    filepath: str
    file_sha: str
    title: str
    devfile_updated_content: str | None = None


class RegistryStack:
    def __init__(
        self,
        path: str,
        raw_content: str,
        last_modified: str,
        file_sha: str,
        owners_content: str | None,
    ) -> None:
        self.name = self._get_stack_name(path)
        self.devfile_path = path
        self.devfile_content = raw_content
        self.last_modified = self._get_last_modified(last_modified)
        self.deprecated = self._get_deprecated(raw_content)
        self.file_sha = file_sha
        self.owners = self._get_owners(owners_content)

    def __repr__(self) -> str:
        return "RegistryStack(name='{}')".format(self.name)

    def _get_stack_name(self, path: str) -> str:
        return (
            path.replace("{}/".format(DEFAULT_STACKS_PATH), "")
            .replace("/devfile.yaml", "")
            .replace("/devfile.yml", "")
        )

    def _get_last_modified(self, last_modified: str) -> datetime:
        return datetime.strptime(last_modified, "%a, %d %b %Y %H:%M:%S %Z")

    def _get_deprecated(self, raw_content: str) -> bool:
        content_dict: dict[str, Any] = yaml.safe_load(raw_content)
        return "deprecated" in [i.lower() for i in content_dict["metadata"]["tags"]]

    def _get_owners(self, owners_content: str | None) -> list[str]:
        if owners_content is None:
            return []

        owners_dict: dict[str, Any] = yaml.safe_load(owners_content)
        return owners_dict.get("reviewers", [])


class GithubProvider:
    def __init__(self, token: str = TOKEN, registry_url: str = REGISTRY_REPO) -> None:
        self.gb = self._init_github(token)
        self.registry_repo = self.gb.get_repo(registry_url)

    def _init_github(self, token: str) -> Github:
        logging.debug("Setting up github connection")
        _auth = Auth.Token(token)
        return Github(auth=_auth)

    def _get_last_modified(self, item: ContentFile) -> ContentFile:
        _c = self.registry_repo.get_commits(path=item.path)
        commits = [commit for commit in _c]
        return commits[0].last_modified

    def _get_repo_items(self, path: str) -> tuple[list[ContentFile], list[ContentFile]]:
        devfiles: list[ContentFile] = []
        owner_files: list[ContentFile] = []
        logging.info("Fetching repo files")
        repo_items: list[ContentFile] = self.registry_repo.get_contents(path)
        for item in repo_items:
            if item.type == "dir":
                repo_items.extend(self.registry_repo.get_contents(item.path))
            elif item.path.endswith(("/devfile.yaml", "/devfile.yml")):
                devfiles.append(item)
            elif item.path.lower().endswith("/owners") and item.path != "stacks/OWNERS":
                owner_files.append(item)
        return devfiles, owner_files

    def _get_matched_devfile_owners(
        self, raw_devfiles: list[ContentFile], raw_owner_files: list[ContentFile]
    ) -> list[tuple[ContentFile, ContentFile]]:
        _matchings: list[tuple[ContentFile, ContentFile]] = []
        for raw_devfile in raw_devfiles:
            _matched = False
            for raw_owner_file in raw_owner_files:
                if raw_owner_file.path.replace("/OWNERS", "") in raw_devfile.path:
                    _matchings.append((raw_devfile, raw_owner_file))
                    _matched = True
                    break
            if not _matched:
                _matchings.append((raw_devfile, None))
        return _matchings

    def get_stacks(self, path: str = DEFAULT_STACKS_PATH) -> list[RegistryStack]:
        raw_devfiles, raw_owner_files = self._get_repo_items(path)
        _matchings = self._get_matched_devfile_owners(raw_devfiles, raw_owner_files)
        return [
            RegistryStack(
                path=raw_devfile.path,
                last_modified=self._get_last_modified(raw_devfile),
                file_sha=raw_devfile.sha,
                raw_content=raw_devfile.decoded_content.decode(),
                owners_content=(
                    None
                    if raw_owner_file is None
                    else raw_owner_file.decoded_content.decode()
                ),
            )
            for raw_devfile, raw_owner_file in _matchings
        ]

    def _deprecate_file(self, pr: RegistryRepoPR) -> None:
        self.registry_repo.update_file(
            pr.filepath,
            pr.commit_message,
            pr.devfile_updated_content,
            pr.file_sha,
            pr.branch_name,
        )

    def _remove_file(self, pr: RegistryRepoPR) -> None:
        _ = self.registry_repo.delete_file(
            pr.filepath,
            pr.commit_message,
            pr.file_sha,
            pr.branch_name,
        )

    def _create_branch(self, pr: RegistryRepoPR) -> str:
        base = self.registry_repo.get_branch(DEFAULT_BRANCH)
        _ = self.registry_repo.create_git_ref(
            ref="refs/heads/" + pr.branch_name, sha=base.commit.sha
        )

    def _create_pr(self, pr: RegistryRepoPR):
        _ = self.registry_repo.create_pull(
            base=DEFAULT_BRANCH,
            head=pr.branch_name,
            title=pr.title,
            body=pr.description,
        )

    def create_prs(self, prs: list[RegistryRepoPR]):
        _prs_created = 0
        for pr in prs:
            if _prs_created >= PR_CREATION_LIMIT:
                logging.warn("PR creation limit is reached. Skipping")
                break
            self._create_branch(pr)
            if pr.action == "deprecate":
                self._deprecate_file(pr)
            else:
                self._remove_file(pr)
            self._create_pr(pr)
            _prs_created += 1


class RegistryStackMaintainer:
    def update(self, stack: RegistryStack) -> RegistryRepoPR | None:
        if not stack.deprecated and self._limit_reached(
            stack.last_modified, DEPRECATION_DAYS_LIMIT
        ):
            logging.info(
                "Stack {} should be deprecated. Last modified {}".format(
                    stack.name, stack.last_modified
                )
            )
            return self._deprecate(stack)

        elif stack.deprecated and self._limit_reached(
            stack.last_modified, REMOVAL_DAYS_LIMIT
        ):
            logging.info(
                "Stack {} is deprecated and should be removed. Last modified {}".format(
                    stack.name, stack.last_modified
                )
            )
            return self._remove(stack)

        else:
            logging.debug(
                "Stack {} doesn't need any update. Last modified {}".format(
                    stack.name, stack.last_modified
                )
            )
            return None

    def _limit_reached(self, last_modified: datetime, days_limit: int) -> bool:
        return datetime.now() + timedelta(days=90) > last_modified + timedelta(
            days=days_limit
        )

    def _deprecate(self, stack: RegistryStack) -> RegistryRepoPR:
        devfile_dict = yaml.safe_load(stack.devfile_content)
        devfile_dict["metadata"]["tags"].append(DEPRECATED_TAG)
        devfile_updated_content = yaml.dump(devfile_dict)

        desc_list = [
            "## What this PR does?\n",
            "This PR deprecates the {} stack as it has reached the inactivity limit of {} days.".format(
                stack.name, DEPRECATION_DAYS_LIMIT
            ),
        ]
        # if len(owners) > 0:
        #     desc_list.append(
        #         "The PR should be reviewed by: {}".format(
        #             ", ".join([f"@{owner}" for owner in owners])
        #         )
        #     )

        return RegistryRepoPR(
            title="chore: Deprecate {} stack after {} days of inactivity".format(
                stack.name, DEPRECATION_DAYS_LIMIT
            ),
            description="\n".join(desc_list),
            commit_message="Deprecate {}".format(stack.name),
            devfile_updated_content=devfile_updated_content,
            branch_name="devfile_maintainer/deprecate-{}".format(
                stack.name.replace("/", "-")
            ),
            action="deprecate",
            file_sha=stack.file_sha,
            filepath=stack.devfile_path,
        )

    def _remove(self, stack: RegistryStack) -> RegistryRepoPR:
        desc_list = [
            "## What this PR does?\n",
            "This PR deprecates the {} stack as it has reached the inactivity limit of {} days.".format(
                stack.name, DEPRECATION_DAYS_LIMIT
            ),
        ]
        # if len(owners) > 0:
        #     desc_list.append(
        #         "The PR should be reviewed by: {}".format(
        #             ", ".join([f"@{owner}" for owner in owners])
        #         )
        #     )

        return RegistryRepoPR(
            title="chore: Remove {} stack after {} days of inactivity".format(
                stack.name, DEPRECATION_DAYS_LIMIT
            ),
            description="\n".join(desc_list),
            action="remove",
            branch_name="devfile_maintainer/remove-{}".format(
                stack.name.replace("/", "-")
            ),
            commit_message="Remove {}".format(stack.name),
            filepath=stack.devfile_path,
            file_sha=stack.file_sha,
        )


def main():
    provider = GithubProvider()
    maintainer = RegistryStackMaintainer()
    prs: list[RegistryRepoPR] = []
    stacks = provider.get_stacks()
    logging.info("Fetched {} stacks from repo".format(len(stacks)))
    for stack in stacks:
        pr = maintainer.update(stack)
        if pr is not None:
            prs.append(pr)

    logging.info("{} PRs should be created".format(len(prs)))
    provider.create_prs(prs)


if __name__ == "__main__":
    main()
