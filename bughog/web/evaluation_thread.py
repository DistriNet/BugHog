import logging
import threading

from bughog.main import Main
from bughog.parameters import EvaluationParameters
from bughog.web.clients import Clients

logger = logging.getLogger(__name__)

THREAD = None


def run_eval_thread(main: Main, eval_params_list: list[EvaluationParameters]):
    global THREAD

    def thread_wrapper():
        try:
            main.run(eval_params_list)
        except Exception as e:
            Clients.push_notification_to_all(str(e), type='error')

    if THREAD and THREAD.is_alive():
        Clients.push_notification_to_all('Evaluation thread is already running.', type='error')
    else:
        THREAD = threading.Thread(target=thread_wrapper)
        THREAD.start()
