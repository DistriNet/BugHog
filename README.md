<div align="center">
    <img alt="BugHog logo" src="./assets/bughog_logo_long.svg" height="256"/>
    <div>
        <img alt="pytest_job" src="https://github.com/DistriNet/BugHog/actions/workflows/run-tests-and-linter.yml/badge.svg?branch=main" />
        <a href="https://hub.docker.com/r/bughog/core"><img alt="Docker Image Version (tag)" src="https://img.shields.io/docker/v/bughog/core/latest?logo=docker" /></a>
        <a href="https://hub.docker.com/r/bughog/core"><img alt="Docker Image Size" src="https://img.shields.io/docker/image-size/bughog/core?logo=docker" /></a>
    </div>
</div>
<br>

BugHog is a powerful framework designed specifically to address the challenging task of pinpointing the exact code revisions in which a particular browser bug was introduced or fixed.

This framework has been developed as part of the _"A Bug's Life: Analyzing the Lifecycle and Mitigation Process of Content Security Policy Bugs"_ paper to identify Content Security Policy bug lifecycles, published at [USENIX Security '23](https://www.usenix.org/conference/usenixsecurity23/presentation/franken).

<br>

<div align="center">
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
</div>


## Getting started :rocket:

BugHog is compatible with UNIX systems running Docker, including WSL on Windows.
You will need at least 5 GB of disk space.

Follow these steps to get started:

```bash
# Clone this repository
git clone https://github.com/DistriNet/BugHog
cd BugHog

# Pull our pre-built Docker images
./scripts/pull.sh

# Start the pulled images
./scripts/start.sh
```

Open your web browser and navigate to [http://localhost:80](http://localhost:80) to access the graphical user interface.
If BugHog is started on a remote server, substitute 'localhost' with the appropriate IP address.

> [!NOTE]
> Depending on your Docker configuration, you might have to use `sudo ./scripts/[..]`.
>
> BugHog in default configuration will spin up its own MongoDB container, which persists data in the [/database](/database/) folder.
> Configuring BugHog to use your own MongoDB and other options are explained [here](https://github.com/DistriNet/BugHog/wiki/Configuration-options).

> [!TIP]
> Our [30-minute tutorial](https://github.com/DistriNet/BugHog/wiki/Tutorial) will guide you on how to use BugHog to trace a real bug's lifecycle!

To stop BugHog, simply run this in the project root:

```bash
./scripts/stop.sh
```


## Development

Use the following commands to build the Docker images yourself, for instance after you made changes to the source code:

```bash
# Build BugHog images
./scripts/build.sh

# Run the freshly built images
./scripts/start.sh
```

> [!NOTE]
> For reference, building takes about 4 minutes on a machine with 8 CPU cores and 8 GB of RAM.


### Debugging

The most convenient debugging approach is to launch an interactive Node environment.
The UI can be visited at [http://localhost:5173](http://localhost:5173).

```bash
./scripts/node_dev.sh
```

For debugging the core application, consider using the VS Code dev container.
You can utilize the configuration in [.devcontainer](.devcontainer) for this.


## Support and contact

More information on how to use BugHog can be found [here](/docs/SUPPORT.md).

For questions, remarks or collaboration, you can reach out to [Gertjan Franken](https://distrinet.cs.kuleuven.be/people/GertjanFranken).
