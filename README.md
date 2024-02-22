# BugHog

![pytest_job](https://github.com/DistriNet/BugHog/actions/workflows/run-tests-and-linter.yml/badge.svg?branch=main)
<a href="https://hub.docker.com/r/bughog/core">![Docker Image Version (tag)](https://img.shields.io/docker/v/bughog/core/latest?logo=docker)</a>
<a href="https://hub.docker.com/r/bughog/core">![Docker Image Size](https://img.shields.io/docker/image-size/bughog/core?logo=docker)</a>


BugHog is a powerful framework designed specifically to address the challenging task of pinpointing the exact revisions in which a particular browser bug was introduced or fixed.

This framework has been developed as part of the _"A Bug's Life: Analyzing the Lifecycle and Mitigation Process of Content Security Policy Bugs"_ paper to identify Content Security Policy bug lifecycles, published at [USENIX Security '23](https://www.usenix.org/conference/usenixsecurity23/presentation/franken).

<img
    src="https://secartifacts.github.io/usenixsec2023/usenixbadges-available.png"
    alt="USENIX Association artifact evaluated badge"
    width="100"/>
<img
    src="https://secartifacts.github.io/usenixsec2023/usenixbadges-functional.png"
    alt="USENIX Association artifact functional badge"
    width="100"/>
<img
    src="https://secartifacts.github.io/usenixsec2023/usenixbadges-reproduced.png"
    alt="USENIX Association artifact reproduced badge"
    width="100"/>


## Usage

### Prerequisites
- Docker (tested with version 24.0.1)

### Installing
BugHog can be installed by following the steps below:

1. Clone this repository:

    ```bash
    git clone https://github.com/DistriNet/BugHog
    cd BugHog
    ```

2. Obtain images:

    You will need at least 5 GB of disk space.

    *Option A: Pulling (fastest)*

    Use the following command to pull the necessary Docker images:
    ```bash
    docker compose pull core worker web
    ```

    *Option B: Building*

    If you want to modify the source code, use the following commands to build the necessary Docker images.
    Run this script again if you make changes to the source code.
    ```bash
    docker compose build core worker web
    ```

    > :bulb: For reference, building takes about 4 minutes on a machine with 8 CPU cores and 8 GB of RAM.

### Starting
After pulling or building the images, start BugHog with the following command.
If you switch between pulled and built images, make sure to execute the appropriate commands mentioned above before starting.
```bash
docker compose up core web
```

Open your web browser and navigate to [http://localhost:5000](http://localhost:5000) to access the graphical interface.
If you started BugHog on a remote server, replace localhost with its IP address.

> :warning: BugHog's own MongoDB instance will persist data within the [database](database) folder.
> Be sure to back-up accordingly, or use your own MongoDB instance as explained below.

#### Optional: Use your own MongoDB instance

By default, BugHog uses a MongoDB container.
you might want to prefer all data to be stored on your own MongoDB instance.
If you prefer storing data in your own MongoDB instance, follow these steps:

1. Create a `.env` file from `.env.example` (both in the [config](config) folder) and fill in the missing values.

2. (Re)start BugHog.

### Stopping
To stop BugHog, run the following command:

```bash
docker compose down
```

### Adding Your Own Experiments

Instructions to add your own custom experiments to the server can be found [here](https://github.com/DistriNet/BugHog-web/blob/main/experiments/README.md).
Be sure to restart the BugHog framework when you add a new experiment:

```bash
docker compose down
docker compose up core web
```

### Development

For extending or debugging the Vue UI, the most convenient approach is to launch an interactive Node environment.
The UI can be visited at [http://localhost:5173](http://localhost:5173).

```bash
docker compose up node_dev
```

For debugging the core application, consider using the VS Code dev container for an effortless debugging experience.
You can utilize the configuration in [.devcontainer](.devcontainer) for this.

## Additional help

Don't hesitate to open a [GitHub issue](https://github.com/DistriNet/BugHog/issues/new) if you come across a bug, want to suggest a feature, or have any questions!
