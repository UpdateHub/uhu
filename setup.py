# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

from setuptools import find_packages, setup

from efu import __version__


setup(
    name='easyfota-utils',
    description='Easy Firmware Over The Air command line utility',
    keywords='fota ota firmware update utility',
    version=__version__,
    packages=find_packages(exclude=['tests*']),
    package_data={
        'efu': [
            'schemas/*.json',
            'core/*.json',
        ],
    },
    entry_points={
        'console_scripts': ['efu=efu.cli:cli']
    },
    install_requires=[
        'click>=6.5',
        'jsonschema>=2',
        'humanize>=0.5.1',
        'progress>=1.1',
        'prompt-toolkit>=0.57',
        'requests>=2',
        'rfc3987>=1.3',
    ],
    author='O.S. Systems Software LTDA',
    author_email='contato@ossystems.com.br',
    url='http://www.ossystems.com.br',
    license='MIT',
    zip_safe=False,
)
