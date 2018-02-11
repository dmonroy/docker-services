import atexit

import os

from docker_services import parse_services, start_docker_services, stop_docker_services


def test_parse_services_normal():
    config = '''
        postgres: postgres:10
        redis: redis:latest
    '''
    services = parse_services(config)
    assert len(services) == 2
    assert services['postgres']['name'] == 'postgres'
    assert services['postgres']['image'] == 'postgres:10'
    assert services['redis']['name'] == 'redis'
    assert services['redis']['image'] == 'redis:latest'


def test_parse_services_mixed():
    config = '''
        postgres: 
        redis: redis:latest
    '''
    services = parse_services(config)
    assert len(services) == 2
    assert services['postgres']['name'] == 'postgres'
    assert services['postgres']['image'] == 'postgres'
    assert services['redis']['name'] == 'redis'
    assert services['redis']['image'] == 'redis:latest'


def test_parse_services_mixed_no_version():
    config = '''
        postgres: 
        redis: redis
    '''
    services = parse_services(config)
    assert len(services) == 2
    assert services['postgres']['name'] == 'postgres'
    assert services['postgres']['image'] == 'postgres'
    assert services['redis']['name'] == 'redis'
    assert services['redis']['image'] == 'redis'


def test_parse_services_mixed_no_image():
    config = '''
        postgres: 
        redis:
    '''
    services = parse_services(config)
    assert len(services) == 2
    assert services['postgres']['name'] == 'postgres'
    assert services['postgres']['image'] == 'postgres'
    assert services['redis']['name'] == 'redis'
    assert services['redis']['image'] == 'redis'


def test_parse_services_with_options():
    config = '''
        postgres: 
            name: pgdb
            image: postgres:10
        redis: 
            image: redis:latest
    '''
    services = parse_services(config)
    assert len(services) == 2
    assert services['pgdb']['name'] == 'pgdb'
    assert services['pgdb']['image'] == 'postgres:10'
    assert services['redis']['name'] == 'redis'
    assert services['redis']['image'] == 'redis:latest'


def test_parse_services_with_options_mixed():
    config = '''
        postgres: 
            name: pgdb
            image: postgres:10
        redis: redis:latest
    '''
    services = parse_services(config)
    assert len(services) == 2
    assert services['pgdb']['name'] == 'pgdb'
    assert services['pgdb']['image'] == 'postgres:10'
    assert services['redis']['name'] == 'redis'
    assert services['redis']['image'] == 'redis:latest'


def test_parse_services_with_variables():
    config = '''
        postgres: 
            image: postgres:10
            environment: 
                POSTGRES_USERNAME: myuser
                POSTGRES_PASSWORD: $3cr3t
                POSTGRES_DB: mydb
                _templates:
                    POSTGRES_PORT: "{env[POSTGRES_PORT_5432_TCP_PORT]/}"
                    DATABASE_URL: "postgres://myuser:$3cr3t@localhost:{env[POSTGRES_PORT_5432_TCP_PORT]/mydb}"
        redis: redis:latest
    '''
    services = parse_services(config)
    assert len(services) == 2
    assert services['postgres']['name'] == 'postgres'
    assert services['postgres']['image'] == 'postgres:10'
    assert services['redis']['name'] == 'redis'
    assert services['redis']['image'] == 'redis:latest'


def test_parse_services_with_variables_and_containers():
    config = '''
        postgres: 
            image: postgres:10
            environment: 
                POSTGRES_USERNAME: myuser
                POSTGRES_PASSWORD: $3cr3t
                POSTGRES_DB: mydb
                _templates:
                    POSTGRES_PORT: "{env[POSTGRES_PORT_5432_TCP_PORT]}"
                    DATABASE_URL: "postgres://{env[POSTGRES_USERNAME]}:{env[POSTGRES_PASSWORD]}@localhost:{env[POSTGRES_PORT_5432_TCP_PORT]}/{env[POSTGRES_DB]}"
        redis: redis:latest
    '''
    services = start_docker_services(config)

    # Ensure services are removed at exit
    atexit.register(stop_docker_services, services)

    assert 'DATABASE_URL' in os.environ
    assert os.environ['POSTGRES_PORT'] == os.environ['POSTGRES_PORT_5432_TCP_PORT']

    # POSTGRES_PORT is a number, no ValueError when casting to int
    port = int(os.environ['POSTGRES_PORT'])
    # it is a positive integer
    assert port > 0
    database_url = 'postgres://myuser:$3cr3t@localhost:{port}/mydb'.format(port=port)

    assert os.environ['DATABASE_URL'] == database_url

