<div align="center">
    <img alt="BugHog logo" src="./assets/bughog_logo_long.svg" height="186"/>
    <div>
        <img alt="pytest" src="https://raw.githubusercontent.com/DistriNet/BugHog/badges/pytest.svg" />
        <img alt="coverage" src="https://raw.githubusercontent.com/DistriNet/BugHog/badges/coverage.svg" />
        <img alt="ty" src="https://raw.githubusercontent.com/DistriNet/BugHog/badges/ty.svg" />
        <img alt="ruff" src="https://raw.githubusercontent.com/DistriNet/BugHog/badges/ruff.svg" />
        <br>
        <a href="https://hub.docker.com/r/bughog/core"><img alt="Docker Image Version (tag)" src="https://img.shields.io/docker/v/bughog/core/latest?logo=docker" /></a>
        <a href="https://hub.docker.com/r/bughog/core"><img alt="Docker Image Size" src="https://img.shields.io/docker/image-size/bughog/core/latest?logo=docker&label=core%20image%20size" /></a>
        <a href="https://hub.docker.com/r/bughog/core"><img alt="Docker Image Size" src="https://img.shields.io/docker/pulls/bughog/core?logo=docker" /></a>
    </div>
</div>
<br>

BugHog is a framework for pinpointing the exact code commit in which a browser bug was introduced or fixed.
Given a proof-of-concept (PoC) that reproduces a bug, BugHog automatically bisects across browser builds to find the precise commit where the behaviour changed.

This framework has been developed as part of the _"A Bug's Life: Analyzing the Lifecycle and Mitigation Process of Content Security Policy Bugs"_ paper to identify Content Security Policy bug lifecycles, published at [USENIX Security '23](https://www.usenix.org/conference/usenixsecurity23/presentation/franken).
Since then, it has continued to evolve and has been exhibited at major cybersecurity conferences, including [Black Hat USA](https://www.blackhat.com/us-24/arsenal/schedule/index.html#bughog-38604).

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


## How it works

1. **Write a PoC** — create a minimal HTML/JS file that demonstrates the bug (e.g. a CSP bypass, a rendering glitch, a JS engine crash).
2. **Select a subject and commit range** — choose a browser or engine and the range of builds to test across.
3. **Run BugHog** — it automatically executes your PoC against each build and bisects to find the exact commit where the bug appeared or disappeared.
4. **Inspect results** — the web UI shows a timeline of pass/fail results and highlights the introducing or fixing commit.


## Getting started :rocket:

### Prerequisites

- A UNIX-based system (Linux or macOS). Windows is supported via WSL — clone the repository into the WSL filesystem, not the Windows filesystem.
- Docker installed and running.
- At least 5 GB of free disk space.

### Installation

```bash
# Clone this repository
git clone https://github.com/DistriNet/BugHog
cd BugHog

# Pull the latest pre-built images from Docker Hub and start BugHog
./scripts/deploy.sh
```

Open your web browser and navigate to [http://localhost:80](http://localhost:80) to access the graphical user interface.
If BugHog is started on a remote server, substitute 'localhost' with the appropriate IP address.

> [!NOTE]
> Depending on your Docker configuration, you might have to use `sudo ./scripts/[..]`.
>
> BugHog in default configuration will spin up its own MongoDB container, which persists data in the [/database](/database/) folder.
> Configuring BugHog to use your own MongoDB and other options are explained [here](/docs/CONFIGURATION.md).

> [!TIP]
> Our [30-minute tutorial](/docs/TUTORIAL.md) will guide you on how to use BugHog to trace a real bug's lifecycle!

To stop BugHog (including any running worker containers), run this in the project root:

```bash
./scripts/stop.sh
```


## Development :hammer_and_wrench:

Use the following command to build all Docker images from the current codebase and start BugHog, for instance after you made changes to the source code:

```bash
./scripts/build-deploy.sh
```

This builds all images (core, nginx, and all subject workers) tagged as `dev`.


### Debugging


For debugging the core application, consider using the VS Code dev container.
You can utilize the configuration in [.devcontainer](.devcontainer) for this.


## Contributing

Contributions are welcome!
Please open a [GitHub issue](https://github.com/DistriNet/BugHog/issues/new) to report bugs or propose features, or submit a pull request with your changes.


## Support and contact :phone:

More information on how to use BugHog can be found [here](/docs/SUPPORT.md).

For questions, remarks or collaboration, you can reach out to [Gertjan Franken](https://distrinet.cs.kuleuven.be/people/GertjanFranken).
