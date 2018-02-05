from docker_services import start_docker_services


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
        start_docker_services(session)
    else:
        print('Not loading services')
