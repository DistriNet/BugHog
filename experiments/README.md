# Adding Your Own Experiments

Follow the guidelines below to integrate your own experiments into BugHog.
Examples can be found in the [experiments](/experiments/) folder.


## File structure

Experiments are organized within the experiments folder. The general file structure is as follows:

```
experiments
|-- pages
|   |-- [project 1]
|   |   |-- [experiment 1]
|   |   |-- [experiment 2]
|   |   |-- ...
|   |-- [project 2]
|   |-- ...
|-- res
```

- Experiments are grouped within projects inside the `pages` folder, representing sets of related experiments.

- The `res` folder is intended to host resources that are used by multiple experiments and/or projects (e.g., scripts, images, videos)
Every resource is hosted on all supported domains.


## Experiments

Within each experiment folder, the following structure is maintained:

```
[experiment 1]
|-- [domain 1]
    |-- [page 1]
    |   |-- headers.json
    |   |-- index.html
    |-- [page 2]
    |   |-- headers.json
    |   |-- index.js
    |-- ...
|-- [domain 2]
|-- ...
|-- url_queue.txt
```

### Domains

> Each experiment must define **at least one domain**.

Supported domain names include:
- `leak.test`
- `a.test`
- `sub.a.test`
- `sub.sub.a.test`
- `b.test`
- `sub.b.test`
- `adition.com` (tracking domain)

> :bulb: If you need support for other domain names, feel free to open a GitHub issue!


### Webpages

> Each domain must define **at least one webpage**.

A webpage is defined by an index file, which is the resource loaded when the page's URL is visited.
Supported file extensions include `index.html` and `index.js`.
The webpage's URL is constructed as follows:

```
https://[domain]/[project]/[experiment]/[page]
```


For example, the file at `experiments/pages/templates/example/a.test/main/index.html` would be accessible through the URL `https://a.test/templates/example/main`.

Response headers for each webpage can be specified by creating a `headers.json` file in the following format:

```json
[
    {
        "key": "Header name",
        "value": "Header value"
    }
]
```

Note that `headers.json` files cannot be empty.
They may, however, contain an empty list.


### URL queue

> Each experiment should define **exactly one URL queue** unless your experiment is satisfied with BugHog's default visitation (see below).

The `url_queue.txt` file contains an ordered list of URLs, separated by newlines, which instructs the browser on the sequence of pages to visit during the experiment.
If this file is absent, BugHog will instruct the browser to visit the experiment's page indicated as `main` and then proceed to visit https://a.test/report/?bughog_sanity_check=OK as a sanity check to confirm the browser's initiation.


### Outcome reporting

Experiments can report their outcome by sending a request to `https://[domain]/report/?bughog_reproduced=OK`, where `[domain]` can be any supported domain.
This outcome data is also transmitted to the BugHog core application and subsequently stored in the database.


#### Sanity Check

Including a URL in the URL queue that serves as a sanity check is recommended (i.e., https://a.test/report/?bughog_sanity_check=OK).
This URL is typically used to verify the integrity of the experiment.
For instance, if an issue occurs during browser automation, such as the browser not starting, this URL will remain unvisited.
Detecting unvisited sanity check URLs can help identify failed experiments and potential problems in the automation process.


## Resources

The `res` folder is intended to host resources shared between projects (e.g., images, videos, scripts).
All resources are hosted on each supported domain.

The example resource `experiments/res/example.html` is hosted at the endpoints `https://[domain]/res/example.html`, where `[domain]` can be any supported domain.


## Additional help

If you have questions, need assistance with adding experiments or wish to request new functionality, don't hesitate to open a [GitHub issue](https://github.com/DistriNet/BugHog/issues/new).
We're here to help!
