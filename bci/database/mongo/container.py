import logging
import os

import docker
import docker.errors
from pymongo import MongoClient

from bci.evaluations.logic import DatabaseConnectionParameters

LOGGER = logging.getLogger(__name__)

NETWORK_NAME = 'bh_net'

DEFAULT_ROOT_USER = 'bci_admin'
DEFAULT_ROOT_PW = 'bci_admin_pw'

DEFAULT_USER = 'bci'
DEFAULT_PW = 'bci-pw'
DEFAULT_DB_NAME = 'bci'
DEFAULT_HOST = 'bh_db'


def run() -> DatabaseConnectionParameters:
    docker_client = docker.from_env()
    try:
        mongo_container = docker_client.containers.get(DEFAULT_HOST)
        if mongo_container.attrs['State']['Running']:
            LOGGER.debug('MongoDB container is already running')
        else:
            LOGGER.debug('MongoDB container is present but stopped, starting now...')
            mongo_container.start()
    except docker.errors.NotFound:
        LOGGER.debug('MongoDB container not found, creating a new one...')
        __create_new_container(DEFAULT_USER, DEFAULT_PW, DEFAULT_DB_NAME, DEFAULT_HOST)
    LOGGER.debug('MongoDB container has started!')
    return DatabaseConnectionParameters(
        DEFAULT_HOST,
        DEFAULT_USER,
        DEFAULT_PW,
        DEFAULT_DB_NAME
    )


def __create_new_container(user: str, pw: str, db_name, db_host):
    docker_client = docker.from_env()
    docker_client.containers.run(
            'mongo:5.0.17',
            name=db_host,
            hostname=db_host,
            network=NETWORK_NAME,
            detach=True,
            remove=True,
            labels=['bh_db'],
            volumes=[
                os.path.join(os.getenv('host_pwd'), 'database/data') + ':/data/db'
            ],
            ports={'27017/tcp': 27017},
            environment={
                'MONGO_INITDB_ROOT_USERNAME': DEFAULT_ROOT_USER,
                'MONGO_INITDB_ROOT_PASSWORD': DEFAULT_ROOT_PW
            }
        )

    mongo_client = MongoClient(
        host=db_host,
        port=27017,
        username=DEFAULT_ROOT_USER,
        password=DEFAULT_ROOT_PW,
        authsource='admin',
        retryWrites=False
    )

    db = mongo_client[db_name]
    if not db.command('usersInfo', user)['users']:
        db.command(
            'createUser',
            user,
            pwd=pw,
            roles=[{
                'role': 'readWrite',
                'db': db_name
            }])
