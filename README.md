# Devfile Registry Stack Maintainer

A github action that deprecates all devfile registry stack meeting specific deprecation criteria

### Inputs

| Name                     | Required | Default          | Description                               |
| ------------------------ | -------- | ---------------- | ----------------------------------------- |
| `DEBUG_MODE`             | No       | 0                | Sets logging level to DEBUG [0/1].        |
| `DEFAULT_BRANCH`         | No       | main             | Default branch of the registry repo.      |
| `DEPRECATION_DAYS_LIMIT` | No       | 365              | Days of inactivity limit for deprecation. |
| `PR_CREATION_LIMIT`      | No       | 5                | Limit of PRs created inside a single run. |
| `REGISTRY_REPO`          | No       | devfile/registry | The registry github repo.                 |
| `REMOVAL_DAYS_LIMIT`     | No       | 365              | Days of inactivity limit for removal.     |
| `STACKS_DIR`             | No       | stacks           | Stacks dir path.                          |
