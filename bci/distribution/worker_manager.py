import logging
import os
import threading
import time
from queue import Queue

import docker
import docker.errors

from bci import worker
from bci.configuration import Global
from bci.evaluations.logic import WorkerParameters
from bci.web.clients import Clients

logger = logging.getLogger(__name__)


class WorkerManager:
    def __init__(self, max_nb_of_containers: int) -> None:
        self.max_nb_of_containers = max_nb_of_containers

        if self.max_nb_of_containers == 1:
            logger.info('Running in single container mode')
        else:
            self.container_id_pool = Queue(maxsize=max_nb_of_containers)
            for i in range(max_nb_of_containers):
                self.container_id_pool.put(i)
            self.client = docker.from_env()

    def start_test(self, params: WorkerParameters, blocking_wait=True) -> None:
        if self.max_nb_of_containers != 1:
            return self.__run_container(params, blocking_wait)

        # Single container mode
        worker.run(params)

    def __run_container(self, params: WorkerParameters, blocking_wait=True) -> None:
        while blocking_wait and self.get_nb_of_running_worker_containers() >= self.max_nb_of_containers:
            time.sleep(5)
        container_id = self.container_id_pool.get()
        container_name = f'bh_worker_{container_id}'

        def start_container_thread():
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
                        logger.info(f'Removing old container \'{container.attrs["Name"]}\' to start new one')
                        container.remove(force=True)
                self.client.containers.run(
                    f'bughog/worker:{Global.get_tag()}',
                    name=container_name,
                    hostname=container_name,
                    shm_size='2gb',
                    network='bh_net',
                    mem_limit='1g',  # To prevent one container from consuming multiple gigs of memory (was the case for a Firefox evaluation)
                    detach=False,
                    remove=True,
                    labels=['bh_worker'],
                    command=[params.serialize()],
                    volumes=[
                        os.path.join(os.getenv('HOST_PWD'), 'config') + ':/app/config:ro',
                        os.path.join(os.getenv('HOST_PWD'), 'browser/binaries/chromium/artisanal')
                        + ':/app/browser/binaries/chromium/artisanal:rw',
                        os.path.join(os.getenv('HOST_PWD'), 'browser/binaries/firefox/artisanal')
                        + ':/app/browser/binaries/firefox/artisanal:rw',
                        os.path.join(os.getenv('HOST_PWD'), 'experiments') + ':/app/experiments:ro',
                        os.path.join(os.getenv('HOST_PWD'), 'browser/extensions') + ':/app/browser/extensions:ro',
                        os.path.join(os.getenv('HOST_PWD'), 'logs') + ':/app/logs:rw',
                        os.path.join(os.getenv('HOST_PWD'), 'nginx/ssl') + ':/etc/nginx/ssl:ro',
                        '/dev/shm:/dev/shm',
                    ],
                )
                logger.debug(f"Container '{container_name}' finished experiments with parameters '{repr(params)}'")
                Clients.push_results_to_all()
            except docker.errors.APIError:
                logger.error(
                    f"Could not run container '{container_name}' or container was unexpectedly removed", exc_info=True
                )
            finally:
                self.container_id_pool.put(container_id)

        thread = threading.Thread(target=start_container_thread)
        thread.start()
        logger.info(f"Container '{container_name}' started experiments for '{params.state}'")
        # To avoid race-condition where more than max containers are started
        time.sleep(3)

    def get_nb_of_running_worker_containers(self):
        return len(self.get_runnning_containers())

    def get_runnning_containers(self):
        return self.client.containers.list(filters={'label': 'bh_worker', 'status': 'running'}, ignore_removed=True)

    def wait_until_all_evaluations_are_done(self):
        if self.max_nb_of_containers == 1:
            return
        while True:
            if self.get_nb_of_running_worker_containers() == 0:
                break
            time.sleep(5)

    def forcefully_stop_all_running_containers(self):
        if self.max_nb_of_containers == 1:
            return
        for container in self.get_runnning_containers():
            container.remove(force=True)
