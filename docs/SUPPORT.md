# Overview of all support pages



- [General installation and usage](/README.md)
- [Adding your own experiments](/experiments/README.md)


## Troubleshooting

If something goes wrong, the tips below might help you out.
If the problem persists (or if you want to suggest a new feature), please create a [GitHub issue](https://github.com/DistriNet/BugHog/issues/new) or contact [Gertjan Franken](https://distrinet.cs.kuleuven.be/people/GertjanFranken).
Additionally, feel free to include any relevant logs for further assistance.


### Consult the logs

- Try launching BugHog without the `-d` flag to view logging output in the terminal, which might provide more information about the issue.
- For more detailed logs at the `DEBUG` level, check out the [logs](/logs) folder for all logging files.


### WSL on Windows

- Ensure you clone the BugHog project to the WSL file system instead of the Windows file system, and launch it from there.
Virtualization between these file systems can cause complications with file management.
