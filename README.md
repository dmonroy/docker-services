Uses docker to spawn containers for services required during tests

[![Build Status](https://travis-ci.org/dmonroy/docker-services.svg?branch=master)](https://travis-ci.org/dmonroy/docker-services)

# Install

This project is available on pypi, so you can use _pip_ to install it:

```
pip install docker-services
```

Or include it as a dependency on `setup.py` or a `requirements.txt` file, whatever you prefer.


# Use it

## 1. Configure your project services

You need to start listing all services that your project depends on and leverage on _docker-services_ to maintain the lifecycle of those services during test runs.

This must happen using the `docker_services` config option on any pytest _.cfg_ or _.ini_ file, the value for that option requires a yaml structure where top level members are the service names and their values can be either an empty value, image name or a or an object.

This is a basic example for a project that depends on a `postgres` service:

```
[pytest]
docker_services=postgres:
```

This is the same:

```
[pytest]
docker_services=
    postgres:
```

And this:

```
[pytest]
docker_services=
    postgres: postgres
```

And this too:

```
[pytest]
docker_services=
    postgres:
        image: postgres
```

And guess what?... this too!

```
[pytest]
docker_services=
    database:
        name: postgres
        image: postgres
```

If the projects depends different services, list all of them:

```
[pytest]
docker_services=
    postgres:
    redis:
```

When image name is not specified (and I bet you already noticed this) it falls back to use the service name as image name, but it is possible to specify the image name and version to use:

```
[pytest]
docker_services=
    postgres: postgres:10
```

Also this way:

```
[pytest]
docker_services=
    postgres:
        image: postgres:10
```

Now the service name is `postgres` and image name is `postgres:10`.

Another option is to use a different name for the service, something like:

```
[pytest]
docker_services=
    db: postgres:10
```

```
[pytest]
docker_services=
    db:
        image: postgres:10
```

Now service name is `db` and image name is `postgres:10`.

If you don't want (or need) to set a specific image version, just ignore the version part like this:

```
[pytest]
docker_services=
    db: postgres
```

Also you are able to use images from a private registry:

```
[pytest]
docker_services=
    db: my.registry.com/custom/postgres
```

### 1.1. Configure environment variables for your services

You may want to customize the behaviour of your services by setting environment variables, it is also possible by adding to the config.

```
[pytest]
docker_services=
    db:
        image: postgres:10
        environment:
            POSTGRES_USERNAME: myuser
            POSTGRES_PASSWORD: $3cr3t
            POSTGRES_DB: mydb
```

Using that config above the _db_ service is now initialized with `POSTGRES_USERNAME`, `POSTGRES_PASSWORD` and `POSTGRES_DB` environment variables.

Those variables are also exposed to the actual session, so you can consume those values from within your app or tests too.

### 1.2. Configure dynamic variables too

Are you planning to configure a `DATABASE_URL` environment variable based on service's port number?... then don't wait and configure a variable template ;).

Talking about the `DATABASE_URL` for postgres one usually expects something like `postgres://user:password@host:port/dbname`, and that can be achieved by replacing

```
[pytest]
docker_services=
    postgres:
        image: postgres:10
        environment:
            POSTGRES_USERNAME: myuser
            POSTGRES_PASSWORD: $3cr3t
            POSTGRES_DB: mydb
            _templates:
                POSTGRES_PORT: "{env[POSTGRES_PORT_5432_TCP_PORT]}"
                DATABASE_URL: "postgres://myuser:$s3cr3t@localhost:{env[POSTGRES_PORT_5432_TCP_PORT]}/mydb"
```

It is also possible to use environment variables defined for the service, so you don't repeat the same:

```
DATABASE_URL: "postgres://{env[POSTGRES_USERNAME]}:{env[POSTGRES_PASSWORD]}@localhost:{env[POSTGRES_PORT_5432_TCP_PORT]}/{env[POSTGRES_DB]}"
```

The parameters on the template are replaced using python's `.format()` method and at the moment only `env` parameter is passed and it references actually to the content of `os.environ`, so all environment variables are available.

## 2. Run tests with docker-services enabled

_docker-services_ adds the `--use-docker-services` command line option for _py.test_, when setting this option it enables service's spawning using docker, run it like this:

```
py.test --use-docker-services
```

## 3. Communicate with the services

We spawn our services because we need to communicate with them during test sessions, either to consume data from or publish data to. For that `docker_services` rely on service's exposed ports to create unique environment variables for each port and protocol exposed on each of the services.

The variable names follows the same conventions as in environment variables created from [links](https://docs.docker.com/network/links/#environment-variables), but for now we only create the `*_PORT` environment variables, assuming docker is running on local machine and ports exposed to localhost.

So, if we have a `postgres` service we expect to communicate using port 5432, now looking at the [Dockerfile](https://github.com/docker-library/postgres/blob/674466e0d47517f4e05ec2025ae996e71b26cae9/10/Dockerfile) we can confirm that it [exposes port 5432](https://github.com/docker-library/postgres/blob/674466e0d47517f4e05ec2025ae996e71b26cae9/10/Dockerfile#L132).

Please note that _docker_services_ creates environment variables for exposed ports only, if service's image doesn't expose any port then no `*_PORT` variable would be reated.

For the `postgres` service use case, variable name for port `5432` would be: `POSTGRES_PORT_5432_TCP_PORT`, this variable name is built using this template: `{service_name}_PORT_{port}_{protocol}_PORT`.

Also remember that environment variables configured for a service are also available within the context of the pytest session, this applies to both static and dynamic variables!

