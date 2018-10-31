import atexit

import os

from docker_services import start_docker_services, stop_docker_services


def pytest_addoption(parser):
    parser.addoption(
        "--docker-services",
        action="store_true",
        default=False,
        dest="use_docker_services",
        help="Spawns docker containers for specified services")

    parser.addoption(
        "--docker-services-keepalive",
        action="store_true",
        default=False,
        dest="keepalive_docker_services",
        help="Maintain service's containers running after tests execution")

    parser.addini(
        'docker_services',
        'lists all docker services required for the test suite'
    )


def config_from_file():
    files = [
        '.services.yaml',
        '.services.yml',
        'tests/.services.yaml',
        'tests/.services.yml'
    ]

    for filename in files:
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                return f.read()


def pytest_configure(config):

    if config.getoption('use_docker_services', False):
        services_config = \
            config_from_file() or \
            config.getini('docker_services')

        if services_config is None:
            print('No services found, but `--use-docker-services` was specified')
        else:
            services = start_docker_services(services_config)
            atexit.register(stop_docker_services, services)
    else:
        print('Not loading services')
