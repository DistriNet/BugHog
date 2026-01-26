import logging
import subprocess
import shlex

logger = logging.getLogger("cli")


def execute(command, cwd=None, timeout=60, max_tries=1, ignore_error=False):
    cmd_list = command.split()

    for attempt in range(1, max_tries + 1):
        try:
            subprocess.check_output(cmd_list, cwd=cwd, timeout=timeout)
            return True
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout of {timeout} minutes expired: starting try {attempt + 1}")
            if attempt == max_tries:
                return False
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed with error: {e}")
            return ignore_error
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return False
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
