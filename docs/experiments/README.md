# Proofs of Concept / Experiments

You can easily add new proofs of concept or experiments directly through BugHog’s UI.

Additional documentation in this folder explains the available experiment options and the parameters you can define in your experiment files.

If you want to import a larger collection of existing experiments, you can simply copy or clone them into the directory:
```
./subject/<subject_type>/experiments/<project_name>/
```

After adding new experiments, restart BugHog to load them.

For example, to import the [CSP PoC repository](https://github.com/DistriNet/bughog-csp-pocs) for web browsers, run:
```bash
git clone https://github.com/DistriNet/bughog-csp-pocs.git ./subject/web_browser/experiments/csp/
```
