import logging
import subprocess
import shlex

logger = logging.getLogger("cli")


def execute(command, cwd=None, timeout=None, max_tries=None):
    if timeout is None and max_tries is None:
        subprocess.check_output(command.split(" "), cwd=cwd)
        return True

    if timeout is None:
        timeout = 60
    if max_tries is None:
        max_tries = 1
    tries = 0
    while tries < max_tries:
        tries += 1
        try:
            subprocess.check_output(command.split(" "), cwd=cwd, timeout=timeout * 60)
            return True
        except subprocess.TimeoutExpired:
            if logger:
                logger.error("Timeout of %i minutes expired: starting try %i" % (timeout, tries + 1))
            continue
    return False


def execute_and_return_status(command, cwd=None):
    status = subprocess.call(shlex.split(command), cwd=cwd)
    return status


def execute_as_daemon(command, cwd=None):
    with subprocess.Popen(shlex.split(command), cwd=cwd) as status:
        return status


def execute_and_return_output(command, cwd=None, output_possibly_empty=False):
    output = subprocess.check_output(shlex.split(command), cwd=cwd)
    if output != b'' or output_possibly_empty:
        return output.decode("utf-8")
    # https://stackoverflow.com/questions/27933592/capturing-all-terminal-output-of-a-program-called-from-python
    executable = ["script", "-q", "/dev/null", "/bin/sh", "-c" "%s > /dev/tty" % command]
    with subprocess.Popen(executable, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd) as proc:
        out, _ = proc.communicate()
        return out.strip().decode("utf-8")


class CLIOperationException(Exception):

    def __init__(self, operation, error_message):
        super().__init__()
        self.message = "Operation '%s' failed\n%s" % (operation, error_message)
