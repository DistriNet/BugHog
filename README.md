# BugHog

![pytest_job](https://github.com/DistriNet/BugHog/actions/workflows/run-tests-and-linter.yml/badge.svg?branch=main)

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
    docker compose up node_install_deps
    docker compose up node_build
    docker compose build core worker web
    ```

    > :bulb: For reference, building takes about 4 minutes on a machine with 8 CPU cores and 8 GB of RAM.

### Starting
After pulling or building the images, start BugHog with the following command.
If you switch between pulled and built images, make sure to execute the appropriate commands mentioned above before starting.
```bash
docker compose up core web
```

Open your web browser and navigate to http://localhost:5000 to access the graphical interface.
If you started BugHog on a remote server, replace localhost with its IP address.

> :warning: BugHog's own MongoDB instance will persist data within the [database](database) folder.
> Be sure to back-up accordingly, or use your own MongoDB instance as explained below.

#### Optional: Use your own MongoDB instance

By default, BugHog uses a MongoDB container.
you might want to prefer all data to be stored on your own MongoDB instance.
If you prefer storing data in your own MongoDB instance, follow these steps:

1. Create a `.env` file in the BugHog root directory and add the following lines with the appropriate values:

```bash
bci_mongo_host=[ip_address_of_host]
bci_mongo_database=[database_name]
bci_mongo_username=[database_user]
bci_mongo_password=[database_password]
```

2. Rebuild BugHog after making these changes.

### Stopping
To stop BugHog, run the following command:

```bash
docker compose down
```

## Adding your own proof of concepts

🚧 This section is currently under construction and will soon provide detailed instructions on how to integrate your own proofs of concept into the BugHog framework. 🚧
