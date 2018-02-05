import atexit
import random
import re
import string
from time import sleep

import docker
import os
import pytest


def _random_string(length=10):
    return ''.join(
        random.choice(
            string.ascii_lowercase +
            string.ascii_uppercase +
            string.digits
        ) for _ in range(length)
    )


def parse_service(service):
    """Extracts name and image from service definition.

    >>> s = parse_service('postgres')
    >>> s['name']
    'postgres'
    >>> s['image']
    'postgres'

    >>> s = parse_service('db=postgres')
    >>> s['name']
    'db'
    >>> s['image']
    'postgres'

    >>> s = parse_service('db=postgres:10')
    >>> s['name']
    'db'
    >>> s['image']
    'postgres:10'

    >>> s = parse_service('db=my.registry.com/custom/postgres:10')
    >>> s['name']
    'db'
    >>> s['image']
    'my.registry.com/custom/postgres:10'

    >>> s = parse_service('my/image')
    >>> s['name']
    'my_image'
    >>> s['image']
    'my/image'

    >>> s = parse_service('my/image:alpha')
    >>> s['name']
    'my_image'
    >>> s['image']
    'my/image:alpha'

    >>> parse_service('my.registry.com/custom/postgres:10')
    Traceback (most recent call last):
     ...
    Exception: Service name not allowed: my.registry.com_custom_postgres


    :param service: service description
    :return: dict with service and image name
    """
    service = service.strip()

    to_dict = lambda x, y: {'name': x, 'image': y}

    if '=' in service:
        service_dict = to_dict(*service.split('=', 1))
    elif ':' in service:
        service_dict = to_dict(service.split(':', 1)[0], service)
    else:
        service_dict = to_dict(service, service)

    if '/' in service_dict['name'] or ':' in service_dict['name']:
        service_dict['name'] = \
            service_dict['name'].replace('/', '_').split(':', 1)[0]

    if not re.match(r'^[\w_]*$', service_dict['name']):
        raise Exception(
            'Service name not allowed: {service_dict[name]}'.format(
                **locals()
            )
        )

    return service_dict


def generate_container_name(service_name):
    """
    >>> name = generate_container_name('my_service')
    >>> parts = name.split('.')
    >>> parts[0]
    'pytest'
    >>> parts[1]
    'my_service'
    >>> len(parts[2])
    10
    """
    return 'pytest.{}.{}'.format(
        service_name, _random_string()
    )


def stop_docker_services(services):
    print('Shutdown docker services:')
    for service in services:
        print(' ', service['name'], service['container'].name)
        service['container'].stop()


def start_docker_services(session):
    services = pytest.config.getini('docker_services')

    if services is None:
        print('No services found, but `--use-docker-services` was specified')
    else:
        services = [
            parse_service(s) for s in services.splitlines()
        ]

        client = docker.from_env()

        print('Launching docker services:')
        for service in services:
            print(' ', service['name'], service['image'])
            container = client.containers.run(
                image=service['image'],
                name=generate_container_name(service['name']),
                auto_remove=True,
                detach=True,
                publish_all_ports=True
            )

            while not container.status == 'running':
                container.reload()
                sleep(0.1)

            service['container'] = container
            ports = container.attrs['NetworkSettings']['Ports']
            for port, hosts in ports.items():
                number, protocol = port.split('/')
                for host_port in hosts:
                    var_template = '{service[name]}_PORT_{number}_{protocol}_PORT'
                    var_name = var_template.format(**locals()).upper()
                    os.environ[var_name] = host_port['HostPort']

        atexit.register(stop_docker_services, services)
