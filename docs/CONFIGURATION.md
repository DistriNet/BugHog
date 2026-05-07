# Configuration options

BugHog can be configured using environment variables. The easiest way is to copy `config/.env.example` to `config/.env` and modify the values there.

## Configuration variables

| Variable | Default | Description |
| :--- | :--- | :--- |
| `BUGHOG_GITHUB_TOKEN` | — | GitHub API token for looking up commit numbers, commit IDs, and release tags. Only requires access to public repositories. |
| `BUGHOG_SERVICE_API` | `https://api.bughog.distrinet-research.be/` | BugHog service domain name for commit number <-> commit ID conversion and executable search. |
| `BUGHOG_EXECUTABLE_CACHE_LIMIT` | `0` | Max number of executables to keep cached in the database. `0` disables caching. |
| `BUGHOG_EXPERIMENT_TRIES` | `3` | Number of times each experiment is repeated to reduce flakiness. |
| `BUGHOG_MONGO_HOST` | — | Hostname of the MongoDB instance. |
| `BUGHOG_MONGO_USERNAME` | — | Username for MongoDB authentication. |
| `BUGHOG_MONGO_PASSWORD` | — | Password for MongoDB authentication. |
| `BUGHOG_MONGO_DATABASE` | — | Name of the MongoDB database. |
| `BUGHOG_VERSION` | — | Manual override for the BugHog version tag. |

## MongoDB

By default, BugHog starts its own MongoDB container and persists data in the `/database` folder.
If you want to use an external MongoDB instance, you must provide all four `BUGHOG_MONGO_*` variables. If any of these are missing, BugHog will fall back to using the built-in container.

## Sudo usage

If your Docker installation requires `sudo`, you might need to pass the `HOST_PWD` variable explicitly when running scripts:

```bash
sudo HOST_PWD=$PWD ./scripts/deploy.sh
```
