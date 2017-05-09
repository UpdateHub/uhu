# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

from setuptools import find_packages, setup

from efu import get_efu_version


setup(
    name='easyfota-utils',
    description='Easy Firmware Over The Air command line utility',
    keywords='fota ota firmware update utility',
    version=get_efu_version(),
    packages=find_packages(exclude=['tests*']),
    package_data={
        'efu': [
            'core/*.json',
        ],
    },
    entry_points={
        'console_scripts': ['efu=efu.cli:cli']
    },
    install_requires=[
        'click>=6.5',
        'humanize>=0.5.1',
        'progress>=1.1',
        'prompt-toolkit>=0.57',
        'updatehub-package-schema',
        'requests>=2',
        'rfc3987>=1.3',
    ],
    author='O.S. Systems Software LTDA',
    author_email='contato@ossystems.com.br',
    url='http://www.ossystems.com.br',
    license='MIT',
    zip_safe=False,
)
