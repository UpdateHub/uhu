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
        'efu': ['metadata/*.json']
    },
    entry_points={
        'console_scripts': ['efu=efu.cli:cli']
    },
    install_requires=[
        'click==6.6',
        'jsonschema==2.5.1',
        'python-magic==0.4.12',
        'progress==1.2',
        'prompt-toolkit==1.0.3',
        'requests==2.10.0',
        'rfc3987==1.3.6',
    ],
    author='O.S. Systems Software LTDA',
    author_email='contato@ossystems.com.br',
    url='http://www.ossystems.com.br',
    license='MIT',
    zip_safe=False,
)
