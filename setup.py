# sample ./setup.py file
from setuptools import setup, find_packages

setup(
    name="docker-services",
    packages=find_packages(),
    use_scm_version=True,
    install_requires=[
        'docker',
        'pytest'
    ],
    entry_points={
        'pytest11': [
            'docker_services=docker_services.pytest_plugin',
        ]
    },
    classifiers=[
        "Framework :: Pytest",
    ],
)