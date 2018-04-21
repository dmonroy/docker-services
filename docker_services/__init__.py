import random
import re
import string
from time import sleep

import docker
import os
import six
import yaml


def _random_string(length=10):
    return ''.join(
        random.choice(
            string.ascii_lowercase +
            string.ascii_uppercase +
            string.digits
        ) for _ in range(length)
    )


def parse_services(config_yaml):
    """Extracts name and image from service definition.

    >>> s = parse_services('postgres:')
    >>> s['postgres']['name']
    'postgres'
    >>> s['postgres']['image']
    'postgres'

    >>> s = parse_services('db: postgres')
    >>> s['db']['name']
    'db'
    >>> s['db']['image']
    'postgres'

    >>> s = parse_services('db: postgres:10')
    >>> s['db']['name']
    'db'
    >>> s['db']['image']
    'postgres:10'

    >>> s = parse_services('db: my.registry.com/custom/postgres:10')
    >>> s['db']['name']
    'db'
    >>> s['db']['image']
    'my.registry.com/custom/postgres:10'

    >>> s = parse_services('my/image: ')
    Traceback (most recent call last):
     ...
    AssertionError: Invalid characters in service name

    >>> s = parse_services('my/service: my/image:alpha')
    Traceback (most recent call last):
     ...
    AssertionError: Invalid characters in service name

    >>> parse_services('my.registry.com/custom/postgres:10:')
    Traceback (most recent call last):
     ...
    AssertionError: Invalid characters in service name


    :param config_yaml: services configuration (yaml string)
    :return: dictionary of services
    """

    def _parse():
        config = yaml.load(config_yaml)

        for name, config_details in config.items():
            service = {
                'name': name,
                'image': name
            }

            if isinstance(config_details, six.string_types) \
                    and config_details.strip() != '':
                service['image'] = config_details

            elif isinstance(config_details, dict):
                service.update(config_details)

            assert re.match(r'^[\w\d_]*$', service['name']), \
                'Invalid characters in service name'

            yield service

    return {
        _['name']: _ for _ in _parse()
    }

def generate_container_name(service_name):
    """
    >>> name = generate_container_name('my_service')
    >>> parts = name.split('.')
    >>> parts[0]
    'docker_services'
    >>> parts[1]
    'my_service'
    >>> len(parts[2])
    10
    """
    return 'docker_services.{}.{}'.format(
        service_name, _random_string()
    )


def stop_docker_services(services):
    print('Shutdown docker services:')
    for service in services.values():
        print(' ', service['name'], service['container'].name)
        service['container'].stop()


def start_docker_services(services_config):
    services = parse_services(services_config)

    client = docker.from_env()

    print('Launching docker services:')
    for service in services.values():
        print(' ', service['name'], service['image'])

        environment = service.get('environment', {})
        variables = {
            vn: vv
            for vn, vv in environment.items()
            if vn != '_templates'
        }

        variable_templates = environment.get('_templates', {})

        container = client.containers.run(
            image=service['image'],
            name=generate_container_name(service['name']),
            auto_remove=True,
            detach=True,
            publish_all_ports=True,
            environment=variables
        )

        while not container.status == 'running':
            sleep(0.1)
            container.reload()

        if container.attrs.get('State', {}).get('Health', {}):
            print('    waiting for healthy status')

            while container.attrs['State']['Health']['Status'] != 'healthy':
                sleep(0.1)
                container.reload()

        service['container'] = container

        # Create environment variables for all exposed ports
        ports = container.attrs['NetworkSettings']['Ports']
        for port, hosts in ports.items():
            number, protocol = port.split('/')
            for host_port in hosts:
                var_template = '{service[name]}_PORT_{number}_{protocol}_PORT'
                var_name = var_template.format(**locals()).upper()
                os.environ[var_name] = host_port['HostPort']

        # Also expose all variables defined on service's config
        for var_name, var_value in variables.items():
            os.environ[var_name] = var_value

        # If service exposes variable templates, create environment
        # variables using the templates and existing env variables
        # created in previous steps
        for var_name, template in variable_templates.items():
            value = template.format(env=os.environ)
            os.environ[var_name] = value

    return services

