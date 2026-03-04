import logging
import os
import threading
import time
from queue import Empty, Queue

import docker
import docker.errors

from bughog import config, worker
from bughog.parameters import ExperimentParameters
from bughog.version_control.state.base import State
from bughog.web.clients import Clients

logger = logging.getLogger(__name__)


class WorkerManager:
    def __init__(self, subject_type: str, subject_name: str, max_nb_of_containers: int) -> None:
        self.max_nb_of_containers = max_nb_of_containers

        if self.max_nb_of_containers == 1:
            logger.info('Running in single container mode')
        else:
            self.container_id_pool = Queue(maxsize=self.max_nb_of_containers)
            for i in range(self.max_nb_of_containers):
                self.container_id_pool.put(i)
            self.client = docker.from_env()
            self.worker_image_ref = self.__get_worker_image_ref(subject_type, subject_name)

    def start_experiment(self, params: ExperimentParameters, state: State, blocking_wait=True) -> None:
        if self.max_nb_of_containers != 1:
            return self.__run_container(params, state, blocking_wait)

        # Single container mode
        worker.run(params, state)
        Clients.push_results_to_all()

    def __run_container(self, params: ExperimentParameters, state: State, blocking_wait=True) -> None:
        try:
            container_id = self.container_id_pool.get(block=blocking_wait)
        except Empty:
            logger.warning(
                'No container id available to run experiment. This should not happen when blocking_wait is True.'
            )
            return
        container_name = f'bh_worker_{container_id}'

        def start_container_thread():
            # TODO: Add timeout. Logs show that sometimes containers hang forever upon executable download.
            if (host_pwd := os.getenv('HOST_PWD', None)) is None:
                raise AttributeError('Could not find HOST_PWD environment var')
            try:
                # Sometimes, it takes a while for Docker to remove the container
                while True:
                    # Get all containers with same name
                    active_containers = self.client.containers.list(
                        all=True,
                        ignore_removed=True,
                        filters={
                            'name': f'^/{container_name}$'  # The exact name has to match
                        },
                    )
                    # Break loop if no container with same name is active
                    if not active_containers:
                        break
                    # Remove all containers with same name (never higher than 1 in practice)
                    for container in active_containers:
                        logger.info(f"Removing old container '{container.attrs['Name']}' to start new one")
                        container.remove(force=True)
            except docker.errors.APIError:
                logger.error('Could not consult list of active containers', exc_info=True)

            container = None
            try:
                container = self.client.containers.run(
                    self.worker_image_ref,
                    name=container_name,
                    hostname=container_name,
                    network='bh_net',
                    mem_limit='4g',  # To prevent one container from consuming multiple gigs of memory (was the case for a Firefox evaluation)
                    detach=True,
                    labels=['bh_worker'],
                    command=[params.serialize(), state.serialize()],
                    volumes=[
                        os.path.join(host_pwd, 'config') + ':/app/config:ro',
                        os.path.join(host_pwd, 'subject') + ':/app/subject:rw',
                        os.path.join(host_pwd, 'logs') + ':/app/logs:rw',
                        os.path.join(host_pwd, 'nginx/ssl') + ':/etc/nginx/ssl:ro',
                    ],
                    tmpfs={'/memory': 'exec,size=3g,mode=1777'},
                )
                result = container.wait()
                if result['StatusCode'] != 0:
                    # Assign dirty result to state associated with crashed container.
                    logger.debug(f'Assigning dirty result to {state} associated with crashed container.')
                    state.result_variables = set()
                    logger.error(
                        f"'{container_name}' exited unexpectedly with status code {result['StatusCode']}. "
                        'Check the worker logs in ./logs/ for more information.'
                    )
                else:
                    logger.debug(f"Container '{container_name}' finished experiments for '{state}'")
                    Clients.push_results_to_all()
            except docker.errors.APIError:
                logger.error('Received a docker error', exc_info=True)
            except docker.errors.ContainerError:
                logger.error(
                    f"Could not run container '{container_name}' or container was unexpectedly removed", exc_info=True
                )
                if container is not None:
                    container_info = container.attrs['State']
                    logger.error(f"'{container_name}' exited unexpectedly with {container_info}", exc_info=True)

            try:
                if container is not None:
                    container.remove()
            except docker.errors.APIError:
                logger.warning('Error received while removing container, likely because it was already being removed.')
            finally:
                self.container_id_pool.put(container_id)

        thread = threading.Thread(target=start_container_thread)
        thread.start()
        logger.info(f"Container '{container_name}' started experiments for '{state}'")
        # Sleep to avoid all workers downloading executables at once, clogging up all IO.
        time.sleep(0.1)

    @staticmethod
    def get_nb_of_running_worker_containers():
        return len(WorkerManager.get_runnning_containers())

    @staticmethod
    def get_runnning_containers():
        return docker.from_env().containers.list(
            filters={'label': 'bh_worker', 'status': 'running'}, ignore_removed=True
        )

    def wait_until_all_evaluations_are_done(self):
        if self.max_nb_of_containers == 1:
            return
        while True:
            if self.get_nb_of_running_worker_containers() == 0:
                break
            time.sleep(5)

    @staticmethod
    def forcefully_stop_all_running_containers():
        for container in WorkerManager.get_runnning_containers():
            container.remove(force=True)

    def __get_worker_image_ref(self, subject_type: str, subject_name: str) -> str:
        """
        Returns the worker image's reference.
        """
        subject_type_ref = f'bughog/worker-{subject_type}:{config.get_tag()}'
        if self.__pull_worker_image(subject_type_ref):
            return subject_type_ref

        subject_name_ref = f'bughog/worker-{subject_name}:{config.get_tag()}'
        if self.__pull_worker_image(subject_name_ref):
            return subject_name_ref

        return f'bughog/worker:{config.get_tag()}'

    def __pull_worker_image(self, image_ref: str) -> bool:
        try:
            _ = self.client.images.pull(image_ref)
            return True
        except docker.errors.ImageNotFound:
            return False
        except docker.errors.APIError:
            return False
