# Devfile Registry Stack Maintainer Action

A github action that deprecates all devfile registry stack meeting specific deprecation criteria

## Inputs

| Name                     | Required | Default | Description                                                                         |
| ------------------------ | -------- | ------- | ----------------------------------------------------------------------------------- |
| `registry_repo_token`    | Yes      | None    | 'Token for the registry repo. Can be passed in using `{{ secrets.GITHUB_TOKEN }}`.' |
| `registry_repo`          | Yes      | None    | The registry github repo.                                                           |
| `debug_mode`             | No       | 0       | Sets logging level to DEBUG [0/1].                                                  |
| `default_branch`         | No       | main    | Default branch of the registry repo.                                                |
| `deprecation_days_limit` | No       | 365     | Days of inactivity limit for deprecation.                                           |
| `pr_creation_limit`      | No       | 5       | Limit of PRs created inside a single run.                                           |
| `removal_days_limit`     | No       | 365     | Days of inactivity limit for removal.                                               |
| `stacks_dir`             | No       | stacks  | Stacks dir path.                                                                    |

## Output

The action will open one PR (on the `registry_repo` targeting the `default_branch`) for each `registry stack` that:

- Has reached the `deprecation_days_limit` and is not deprecated yet (deprecation action).
- Has reached the `removal_days_limit` and is not removed yet (deprecation action).

Note that if the `pr_creation_limit` is reached all the next PRs will be skipped

## Example Usage

An example usage of this Job is:

```yaml
name: Devfile Registry Maintainer

on:
  schedule:
    - cron: "0 5 * * *"

jobs:
  devfile-registry-maintainer:
    runs-on: ubuntu-latest
    name: Maintain registry stacks
    steps:
      - name: Deprecate or Remove expired stacks
        id: deprecate-remove
        uses: thepetk/devfile-registry-maintainer@<version-hash>
        with:
          # Required inputs
          registry_repo_token: ${{ secrets.GITHUB_TOKEN }}
          registry_repo: <my-org/username>/<registry-repo-name>
          # Optional inputs
          deprecation_days_limit: <limit of inactivity days for deprecation>
          pr_creation_limit: <limit of PRs created per Run>
          removal_days_limit: <limit of inactivity days for removal>
          debug_mode: <should log on debug leven (0) or info (1)>
          default_branch: <target branch name>
          stacks_dir: <path of stacks dir inside the repo>
```

## Releases

An `devfile-registry-maintainer` release is created each time a PR having updates on code is merged. You can create a new release [here](https://github.com/thepetk/devfile-registry-maintainer/releases/new)

A tag should be created with the version of the release as name. The `devfile-registry-maintainer` follows the `v{major}.{minor}.{bugfix}` format (e.g `v0.1.0`). The title of the release has to be the equal to the new tag created for the release.
The description of the release is optional. You may add a description if there were outstanding updates in the project, not mentioned in the issues or PRs of this release.

## Contributing

Contributions are always welcomed, feel free to open an issue for any feature you would like to add or for any bug you would like to report [here](github.com/thepetk/devfile-registry-maintainer/issues/new).
