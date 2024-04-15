# Devfile Registry Stack Maintainer Action

A github action that deprecates all devfile registry stack meeting specific deprecation criteria

## Inputs

| Name                     | Required | Default          | Description                               |
| ------------------------ | -------- | ---------------- | ----------------------------------------- |
| `DEBUG_MODE`             | No       | 0                | Sets logging level to DEBUG [0/1].        |
| `DEFAULT_BRANCH`         | No       | main             | Default branch of the registry repo.      |
| `DEPRECATION_DAYS_LIMIT` | No       | 365              | Days of inactivity limit for deprecation. |
| `PR_CREATION_LIMIT`      | No       | 5                | Limit of PRs created inside a single run. |
| `REGISTRY_REPO`          | No       | devfile/registry | The registry github repo.                 |
| `REMOVAL_DAYS_LIMIT`     | No       | 365              | Days of inactivity limit for removal.     |
| `STACKS_DIR`             | No       | stacks           | Stacks dir path.                          |

## Output

The action will open one PR (on the `REGISTRY_REPO` targeting the `DEFAULT_BRANCH`) for each `registry stack` that:

- Has reached the `DEPRECATION_DAYS_LIMIT` and is not deprecated yet (deprecation action).
- Has reached the `DEPRECATION_DAYS_LIMIT` and is not removed yet (deprecation action).

Note that if the `PR_CREATION_LIMIT` is reached all the next PRs will be skipped

## Releases

An `devfile-registry-maintainer` release is created each time a PR having updates on code is merged. You can create a new release [here](https://github.com/thepetk/devfile-registry-maintainer/releases/new)

A tag should be created with the version of the release as name. The `devfile-registry-maintainer` follows the `v{major}.{minor}.{bugfix}` format (e.g `v0.1.0`). The title of the release has to be the equal to the new tag created for the release.
The description of the release is optional. You may add a description if there were outstanding updates in the project, not mentioned in the issues or PRs of this release.

## Contributing

Contributions are always welcomed, feel free to open an issue for any feature you would like to add or for any bug you would like to report [here](github.com/thepetk/devfile-registry-maintainer/issues/new).
