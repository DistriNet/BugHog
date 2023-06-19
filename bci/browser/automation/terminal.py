import logging
import signal
import subprocess
import time


logger = logging.getLogger('bci')


class TerminalAutomation:

    @staticmethod
    def run(url: str, args: list[str], seconds_per_visit: int):
        logger.debug("Starting browser process...")
        args.append(url)
        logger.debug(f'Command string: \'{" ".join(args)}\'')
        proc = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        time.sleep(seconds_per_visit)

        logger.debug(f'Terminating browser process after {seconds_per_visit}s using SIGINT...')
        # Use SIGINT and SIGTERM to end process such that cookies remain saved.
        proc.send_signal(signal.SIGINT)
        proc.send_signal(signal.SIGTERM)

        try:
            stdout, stderr = proc.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            logger.info("Browser process did not terminate after 5s. Killing process through pkill...")
            subprocess.run(['pkill', '-2', args[0].split('/')[-1]])

        proc.wait()
        logger.debug("Browser process terminated.")
