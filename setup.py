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