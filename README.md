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


## Installation

BugHog is compatible with UNIX systems running Docker, including WSL on Windows.
Follow these steps to get started:

1. **Clone this repository:**

    ```bash
    git clone https://github.com/DistriNet/BugHog
    cd BugHog
    ```

2. **Obtain images:**

    You will need at least 5 GB of disk space.
    There are two options available to obtain the BugHog images, and you can switch between them by executing the appropriate command.

    ***Option A:** Pulling (fastest)*

    Use the following command to pull the necessary Docker images:
    ```bash
    docker compose pull core worker web
    ```

    > :bulb: If you prefer to use a version other than the latest, simply modify the `BUGHOG_VERSION` and / or `BUGHOG_WEB_VERSION` variables accordingly.

    ***Option B:** Building*

    Use the following commands to build the Docker images yourself, for instance after you made changes to the source code:
    ```bash
    docker compose build core worker web
    ```

    > :bulb: For reference, building takes about 4 minutes on a machine with 8 CPU cores and 8 GB of RAM.


## Usage

Launch BugHog using the following command:
```bash
docker compose up -d
```

> :warning: If you use `sudo` with this command, the `PWD` environment variable won't be passed to the BugHog containers, which is necessary for dynamically starting worker containers.
> To avoid this, explicitly pass on this variable: `sudo PWD=$PWD docker compose up`.

Open your web browser and navigate to [http://localhost:5000](http://localhost:5000) to access the graphical interface.
If BugHog is started on a remote server, substitute 'localhost' with the appropriate IP address.

BugHog can be stopped through:
```bash
docker compose down
```

> :warning: BugHog's own MongoDB instance will persist data within the [database](database) folder.
> Be sure to back-up accordingly, or use your own MongoDB instance as explained below.


### Optional: Use your own MongoDB instance

By default, BugHog uses a MongoDB container to store data.
If you prefer storing data in your own MongoDB instance, follow these steps:

1. Create a `.env` file from `.env.example` (both in the [config](config) folder) and fill in the missing database values.

2. (Re)start BugHog.


### Adding your new experiments

Instructions to add your own custom experiments to the server can be found [here](https://github.com/DistriNet/BugHog-web/blob/main/experiments/README.md).
Be sure to restart the BugHog framework when you add a new experiment:

```bash
docker compose down
docker compose up -d
```

## Development

For extending or debugging the Vue UI, the most convenient approach is to launch an interactive Node environment.
The UI can be visited at [http://localhost:5173](http://localhost:5173).

```bash
docker compose up node_dev
```

For debugging the core application, consider using the VS Code dev container.
You can utilize the configuration in [.devcontainer](.devcontainer) for this.


## Contact

Don't hesitate to open a [GitHub issue](https://github.com/DistriNet/BugHog/issues/new) if you encounter a bug or want to suggest a feature!

For questions or collaboration, you can reach out to [Gertjan Franken](https://distrinet.cs.kuleuven.be/people/GertjanFranken).


## Troubleshooting

If something isn't working as expected, check out the troubleshooting tips below.
If you don't find a solution, don't hesitate to open a [GitHub issue](https://github.com/DistriNet/BugHog/issues/new).
Feel free to include any relevant logs.


### Consult the logs

- Try launching BugHog without the `-d` flag to see logging output in the terminal, which might provide more information about the issue.
- For more detailed logs at the `DEBUG` level, check out the [logs](/logs) folder for all logging files.


### WSL on Windows

- Ensure you clone the BugHog project to the WSL file system instead of the Windows file system, and launch it from there.
Virtualization between these file systems can cause complications with file management.
