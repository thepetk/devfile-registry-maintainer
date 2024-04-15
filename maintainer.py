#!/usr/bin/env python3
#
# This script aims to run all lifecycle actions required
# inside a devfile registry repo. More detailed, it will
# check all stack versions to see if they should be removed
# or deprecated. To deprecate a stack version someone need
# to add a "Deprecate" tag to the metadata.tags.

# More information about the devfile project can be found
# at www.devfile.io.

# An example registry repo is:

# https://github.com/devfile/registry

# The flow of the script is very simple. It is designed with
# the following steps:

# 1. Fetches all ENV variables. All variables are listed in
# the README.md.
# 2. Gets all stacks from the github API and converts them
# to RegistryStack objects.
# 3. Checks every stack if the deprecation or removal criteria
# are met.
# 4. For every update action it creates a RegistryRepoPR obj.
# 5. For every RegistryRepoPR creates a PR to github.com.
import io
import logging
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Literal

from github import Auth, Github
from github.ContentFile import ContentFile
from github.GithubException import BadCredentialsException, GithubException
from ruamel.yaml import YAML


class CriticalException(Exception):
    pass


def get_int_env_var(env_var: str, default: int) -> int:
    try:
        return int(os.getenv(env_var, default))
    except ValueError as err:
        logging.error("Invalid input given for {}:: {}".format(env_var, str(err)))
        sys.exit(1)


GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
DEBUG_MODE = get_int_env_var("DEBUG_MODE", 0)
DATETIME_STRFTIME_FORMAT = "%a, %d %b %Y %H:%M:%S GMT"
DATETIME_STRPTIME_FORMAT = "%a, %d %b %Y %H:%M:%S %Z"
DEFAULT_BRANCH = os.getenv("DEFAULT_BRANCH", "main")
DEPRECATION_DAYS_LIMIT = get_int_env_var("DEPRECATION_INACTIVITY_LIMIT", 365)
DEPRECATED_TAG = "Deprecated"
PR_CREATION_LIMIT = get_int_env_var("PR_CREATION_LIMIT", 5)
REGISTRY_REPO = os.getenv("REGISTRY_REPO", "thepetk/registry")
REMOVAL_DAYS_LIMIT = get_int_env_var("REMOVAL_DEPRECATION_LIMIT", 365)
STACKS_DIR = os.getenv("STACKS_DIR", "stacks")
TEST_MODE = get_int_env_var("TEST_MODE", 0)


def get_logging_level():
    if DEBUG_MODE > 0:
        return logging.DEBUG
    return logging.INFO


logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
    level=get_logging_level(),
)


def critical_error(msg: str) -> None:
    logging.error(msg)
    sys.exit(1)


class YAMLConfig:
    def __init__(
        self,
        preserve_quotes: bool = True,
        default_flow_style: bool = False,
        default_style: bool = False,
        width: int = 4096,
        mapping_indent: int = 2,
        sequence_indent: int = 4,
        offset_indent: int = 2,
    ) -> None:
        self.preserve_quotes = preserve_quotes
        self.default_flow_style = default_flow_style
        self.width = width
        self.default_style = default_style
        self.mapping_indent = mapping_indent
        self.sequence_indent = sequence_indent
        self.offset_indent = offset_indent

    def config(self, _yaml: YAML) -> YAML:
        _yaml.preserve_quotes = self.preserve_quotes
        _yaml.default_flow_style = self.default_flow_style
        _yaml.width = self.width
        _yaml.default_style = self.default_style  # type: ignore
        _yaml.indent(
            mapping=self.mapping_indent,
            sequence=self.sequence_indent,
            offset=self.offset_indent,
        )
        return _yaml


def get_YAML() -> YAML:
    _yaml = YAML()
    _config = YAMLConfig()
    return _config.config(_yaml)


@dataclass
class RegistryRepoPR:
    """
    represents a github Pull Request creation action.
    """

    action: Literal["deprecate", "remove"]
    branch_name: str
    commit_message: str
    description: str
    filepath: str
    file_sha: str
    title: str
    devfile_updated_content: str | None = None


class RegistryStack:
    """
    a stack version fetched from the devfile registry.
    """

    def __init__(
        self,
        path: str,
        raw_content: str,
        last_modified: str,
        file_sha: str,
        owners_content: str | None,
    ) -> None:
        self.yaml = get_YAML()
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
            path.replace("{}/".format(STACKS_DIR), "")
            .replace("/devfile.yaml", "")
            .replace("/devfile.yml", "")
        )

    def _get_last_modified(self, last_modified: str) -> datetime:
        """
        converts the string value from github api to a datetime object.
        """
        return datetime.strptime(last_modified, DATETIME_STRPTIME_FORMAT)

    def _get_deprecated(self, raw_content: str) -> bool:
        content_dict: dict[str, Any] = self.yaml.load(raw_content)
        return "deprecated" in [i.lower() for i in content_dict["metadata"]["tags"]]

    def _get_owners(self, owners_content: str | None) -> list[str]:
        """
        converts the owners file found for the stack to a list of strings.
        """
        if owners_content is None:
            return []

        owners_dict: dict[str, Any] = self.yaml.load(owners_content)
        return owners_dict.get("reviewers", [])


class GithubProvider:
    """
    manages all github API operations ran inside the script.
    """

    def __init__(
        self, token: str = GITHUB_TOKEN, registry_url: str = REGISTRY_REPO
    ) -> None:
        self.gb = self._init_github(token)
        self.registry_repo = self.gb.get_repo(registry_url)

    def _init_github(self, token: str) -> Github:
        logging.debug("Setting up github connection")
        _auth = Auth.Token(token)

        # Test cases should not authenticate github
        if TEST_MODE > 0:
            return Github()

        _g = Github(auth=_auth)

        # check if given credentials are ok
        try:
            _g.get_user().login
        except BadCredentialsException:
            raise CriticalException("bad credentials given for github")

        return Github(auth=_auth)

    def _get_last_modified(self, item: ContentFile) -> str:
        """
        gets the datatime of the last commit related to this ContentFile.
        """
        _c = self.registry_repo.get_commits(path=item.path)
        commits = [commit for commit in _c]
        if len(commits) > 0:
            return "" if commits[0].last_modified is None else commits[0].last_modified
        else:
            return datetime.strftime(datetime.now(), DATETIME_STRFTIME_FORMAT)

    def _get_repo_items(self, path: str) -> tuple[list[ContentFile], list[ContentFile]]:
        """
        gets all items inside the repo having filename in [/devfile.yaml, /devfile.yml,
        /OWNERS]
        """
        devfiles: list[ContentFile] = []
        owner_files: list[ContentFile] = []
        logging.info("Fetching repo files")
        repo_items: list[ContentFile] = self.registry_repo.get_contents(path)  # type: ignore # noqa: E501
        for item in repo_items:
            # if the item fetched is a dir get its contents too.
            if item.type == "dir":
                repo_items.extend(self.registry_repo.get_contents(item.path))  # type: ignore # noqa: E501
            elif item.path.endswith(("/devfile.yaml", "/devfile.yml")):
                devfiles.append(item)
            # exclude the stack/OWNERS as it matches all devfiles fetched.
            elif item.path.lower().endswith("/owners") and item.path != "stacks/OWNERS":
                owner_files.append(item)
        return devfiles, owner_files

    def _get_matched_devfile_owners(
        self, raw_devfiles: list[ContentFile], raw_owner_files: list[ContentFile]
    ) -> list[tuple[ContentFile, ContentFile | None]]:
        """
        matches every devfile fetched from the registry repo with an OWNERS file.
        If there is no OWNERS file found it matches a NoneType.
        """
        _matchings: list[tuple[ContentFile, ContentFile | None]] = []
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

    def get_stacks(self, path: str = STACKS_DIR) -> list[RegistryStack]:
        """
        gets all stack versions from the registry and converts them into a list
        of RegistryStack objects.
        """
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
        """
        creates a commit for the deprecated stack.
        """
        self.registry_repo.update_file(
            pr.filepath,
            pr.commit_message,
            pr.devfile_updated_content,  # type: ignore
            pr.file_sha,
            pr.branch_name,
        )

    def _remove_file(self, pr: RegistryRepoPR) -> None:
        """
        creates a commit for the removed stack.
        """
        _ = self.registry_repo.delete_file(
            pr.filepath,
            pr.commit_message,
            pr.file_sha,
            pr.branch_name,
        )

    def _branch_already_exists(self, branch_name: str) -> bool:
        try:
            _ = self.registry_repo.get_branch(branch_name)
        except GithubException:
            return False
        return True

    def _create_branch(self, pr: RegistryRepoPR) -> None:
        """
        creates a branch for the given RegistryRepoPR object.
        """
        base = self.registry_repo.get_branch(DEFAULT_BRANCH)
        _ = self.registry_repo.create_git_ref(
            ref="refs/heads/" + pr.branch_name, sha=base.commit.sha
        )

    def _create_pr(self, pr: RegistryRepoPR):
        """
        creates a pull request for the given RegistryRepoPR object.
        """
        logging.info("creating pr for {} branch".format(pr.branch_name))
        _ = self.registry_repo.create_pull(
            base=DEFAULT_BRANCH,
            head=pr.branch_name,
            title=pr.title,
            body=pr.description,
        )

    def create_prs(self, prs: list[RegistryRepoPR]):
        """
        creates all prs for the given list RegistryRepoPR objects.
        Skips if the PR_CREATION_LIMIT has been reached.
        """
        _prs_created = 0
        for pr in prs:
            if _prs_created >= PR_CREATION_LIMIT:
                logging.warn("PR creation limit is reached. Skipping")
                break

            if self._branch_already_exists(pr.branch_name):
                logging.warning(
                    "branch {} already exists. Skipping pr".format(pr.branch_name)
                )
                continue
            try:
                self._create_branch(pr)

                if pr.action == "deprecate":
                    self._deprecate_file(pr)
                else:
                    self._remove_file(pr)

                self._create_pr(pr)
                _prs_created += 1
            except GithubException as err:
                logging.warning(
                    "failed to create pr for {}:: {}".format(pr.filepath, str(err))
                )
        logging.info("created {} pull requests".format(_prs_created))


class RegistryStackMaintainer:
    def __init__(self) -> None:
        self.yaml = get_YAML()

    def update(self, stack: RegistryStack) -> RegistryRepoPR | None:
        """
        checks if the given stack matches the removal or deprecation
        citeria.
        """
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
        return datetime.now() > last_modified + timedelta(days=days_limit)

    def _add_owners_mention(self, desc_list: list[str], owners: list[str]) -> list[str]:
        """
        mentions owners if they exist.
        """
        if len(owners) > 0:
            desc_list.append(
                "The PR should be reviewed by: {}".format(
                    ", ".join([f"@{owner}" for owner in owners])
                )
            )
        return desc_list

    def _deprecate(self, stack: RegistryStack) -> RegistryRepoPR:
        """
        updates the stack content with the deprecated tag.
        """
        # add deprecated stack
        devfile_dict = self.yaml.load(stack.devfile_content)
        devfile_dict["metadata"]["tags"].append(DEPRECATED_TAG)

        # dump new content to variable
        _buf = io.StringIO()
        _ = self.yaml.dump(devfile_dict, _buf)
        devfile_updated_content = _buf.getvalue()
        desc_list = [
            "## What this PR does?\n",
            "This PR deprecates the {} stack as it has reached the inactivity limit of {} days.".format(  # noqa: E501
                stack.name, DEPRECATION_DAYS_LIMIT
            ),
        ]

        # self._add_owners_mention(desc_list, stack.owners)

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
        """
        creates a RegistryRepoPR object for the removal action.
        """
        desc_list = [
            "## What this PR does?\n",
            "This PR deprecates the {} stack as it has reached the inactivity limit of {} days.".format(  # noqa: E501
                stack.name, DEPRECATION_DAYS_LIMIT
            ),
        ]

        # self._add_owners_mention(desc_list, stack.owners)

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

    try:
        stacks = provider.get_stacks()
    except CriticalException as err:
        critical_error(str(err))

    logging.info("Fetched {} stacks from repo".format(len(stacks)))
    for stack in stacks:
        pr = maintainer.update(stack)
        if pr is not None:
            prs.append(pr)

    logging.info("{} PRs should be created".format(len(prs)))
    provider.create_prs(prs)


if __name__ == "__main__":
    main()
