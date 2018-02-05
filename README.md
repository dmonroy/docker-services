Uses docker to spawn containers for services required during tests

# Install

This project is available on pypi, so you can use _pip_ to install it:

```
pip install docker-services
```

Or include it as a dependency on `setup.py` or a `requirements.txt` file, whatever you prefer.


# Use it

## 1. Configure your project services

You need to start listing all services that your project depends on and leverage on _docker-services_ to maintain the lifecycle of those services during test runs.

This must happen using the `docker_services` config option on any pytest _.cfg_ or _.ini_ file, the value for that option must be one or multiple services, one per line.

This is a basic example for a project that depends on a `postgres` service:

```
[pytest]
docker_services=postgres
```

Also this is the same:

```
[pytest]
docker_services=
    postgres
```

If the projects depends different services, list all one by one:

```
[pytest]
docker_services=
    postgres
    redis
```

When image name is not specified then it falls back to use the service name as image name, but it is possible to specify the image name and version to use:

```
[pytest]
docker_services=
    postgres:9.10
```

This way service name is `postgres` and image name is `postgres:10`.

Another option is to use a different name for the service, something like:


```
[pytest]
docker_services=
    db=postgres:10
```

Now service name is `db` and image name id `postgres:10`.

If you don't want (or need) to set a specific image name, just ignore the version part like this:

```
[pytest]
docker_services=
    db=postgres
```

Also you are able to use images from a private registry:

```
[pytest]
docker_services=
    db: my.registry.com/custom/postgres
```

## 2. Run tests with docker-services enabled

_docker-services_ adds the `--use-docker-services` command line option for _py.test_, when setting this option it enables service's spawning using docker, run it like this:

```
py.test --use-docker-services
```



