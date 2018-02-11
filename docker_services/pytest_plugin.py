import atexit

from docker_services import start_docker_services, stop_docker_services


def pytest_addoption(parser):
    parser.addoption(
        "--docker-services",
        action="store_true",
        default=False,
        dest="use_docker_services",
        help="Spawns docker containers for specified services")

    parser.addini(
        'docker_services',
        'lists all docker services required for the test suite'
    )


def pytest_sessionstart(session):

    if session.config.getoption('use_docker_services', False):
        services_config = session.config.getini('docker_services')

        if services_config is None:
            print('No services found, but `--use-docker-services` was specified')
        else:
            services = start_docker_services(services_config)
            atexit.register(stop_docker_services, services)
    else:
        print('Not loading services')
