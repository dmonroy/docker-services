import random
import re
import socket
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


def stop_docker_service(service):
    print('Terminating service {} {}'.format(service['name'], service['container'].name))
    service['container'].stop()

# See https://stackoverflow.com/a/28950776
def get_hostname():
    """Platform-independent way to get the hostname of a machine."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

def start_docker_services(services_config):
    services = parse_services(services_config)

    client = docker.from_env()

    _on_hold = lambda x: {_['name'] for _ in x.values() if _.get('container', None) is None}
    _running = lambda x: {_['name'] for _ in x.values() if _.get('container', None) is not None}

    print('Launching docker services:')
    while _on_hold(services):
        for service_name in _on_hold(services):
            service = services[service_name]
            print(' {} {}'.format(service['name'], service['image']))
            requires = service.get('requires', [])
            if requires:
                for required_service in requires:
                    if required_service not in services:
                        raise KeyError(
                            "Service '{}' doesn't exist.".format(required_service)
                        )

                if any(_ in _on_hold(services) for _ in required_service):
                    continue

            environment = service.get('environment', {})
            variables = {
                vn: vv
                for vn, vv in environment.items()
                if vn != '_templates'
            }
            for required_service in requires:
                variables.update(
                    services[required_service]['compiled_env']
                )


            variable_templates = environment.get('_templates', {})

            try:
                image = client.images.get(service['image'])
            except:
                print('    pulling image: {}'.format(service['image']))
                client.images.pull(service['image'])

            container = client.containers.run(
                image=service['image'],
                command=service.get('command', None),
                working_dir=service.get('workdir', None),
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
                print('      waiting for healthy status')

                while container.attrs['State']['Health']['Status'] != 'healthy':
                    sleep(0.1)
                    container.reload()

            service['container'] = container

            for _cmd in service.get('setup_commands', []):
                print(_cmd)
                _cmd_result = container.exec_run(_cmd)
                print(_cmd_result.output)

            # Create environment variables for all exposed ports
            ports = container.attrs['NetworkSettings']['Ports']
            hostname = os.getenv('DOCKER_SERVICES_HOST') or get_hostname()
            service['compiled_env'] = {}
            for port, hosts in ports.items():
                number, protocol = port.split('/')
                for host_port in hosts:
                    port_var_template = '{service[name]}_PORT_{number}_{protocol}_PORT'
                    addr_var_template = '{service[name]}_PORT_{number}_{protocol}_ADDR'
                    port_var_name = port_var_template.format(**locals()).upper()
                    os.environ[port_var_name] = host_port['HostPort']
                    service['compiled_env'][port_var_name] = host_port['HostPort']
                    addr_var_name = addr_var_template.format(**locals()).upper()
                    os.environ[addr_var_name] = hostname
                    service['compiled_env'][addr_var_name] = hostname

            # Also expose all variables defined on service's config
            for var_name, var_value in variables.items():
                os.environ[var_name] = var_value
                service['compiled_env'][var_name] = var_value

            # If service exposes variable templates, create environment
            # variables using the templates and existing env variables
            # created in previous steps
            for var_name, template in variable_templates.items():
                value = template.format(env=os.environ)
                os.environ[var_name] = value
                service['compiled_env'][var_name] = value

            yield service

