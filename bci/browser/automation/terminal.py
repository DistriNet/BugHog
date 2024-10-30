import logging
import signal
import subprocess
import time

logger = logging.getLogger(__name__)


class TerminalAutomation:
    @staticmethod
    def visit_url(url: str, args: list[str], seconds_per_visit: int):
        args.append(url)
        proc, _ = TerminalAutomation.open_browser(args)
        logger.debug(f'Visiting the page for {seconds_per_visit}s')
        time.sleep(seconds_per_visit)
        TerminalAutomation.terminate_browser(proc, args)

    @staticmethod
    def open_browser(args: list[str]) -> tuple[subprocess.Popen, str]:
        logger.debug('Starting browser process...')
        logger.debug(f'Command string: \'{" ".join(args)}\'')
        with open('/tmp/browser.log', 'a+') as file:
            proc = subprocess.Popen(args, stdout=file, stderr=file)
            time.sleep(0.5)
            position = file.tell()
            file.seek(0)
            output = file.read()
            file.seek(position)
            return proc, output

    @staticmethod
    def terminate_browser(proc: subprocess.Popen, args: list[str]) -> None:
        logger.debug('Terminating browser process using SIGINT...')

        # Use SIGINT and SIGTERM to end process such that cookies remain saved.
        proc.send_signal(signal.SIGINT)
        proc.send_signal(signal.SIGTERM)

        try:
            stdout, stderr = proc.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            logger.info('Browser process did not terminate after 5s. Killing process through pkill...')
            subprocess.run(['pkill', '-2', args[0].split('/')[-1]])

        proc.wait()
        logger.debug('Browser process terminated.')
