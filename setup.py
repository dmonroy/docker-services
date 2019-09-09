# sample ./setup.py file
import os
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.md')) as f:
    long_description = f.read()

setup(
    name="docker-services",
    packages=find_packages(),
    use_scm_version=True,
    description='Uses docker to spawn containers for services required during tests',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/dmonroy/docker-services',
    author='Darwin Monroy',
    author_email='contact@darwinmonroy.com',
    setup_requires=['setuptools_scm'],
    install_requires=[
        'docker',
        'pytest',
        'pyyaml'
    ],
    entry_points={
        'pytest11': [
            'docker_services=docker_services.pytest_plugin',
        ]
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Framework :: Pytest",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Topic :: Software Development :: Build Tools",
    ],
)