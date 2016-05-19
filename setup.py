# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

from setuptools import setup


setup(
    name='easyfota-utils',
    description='Easy Firmware Over The Air command line utility',
    keywords='fota ota firmware update utility',
    version='0.0.dev0',
    packages=['efu'],
    setup_requires=['pytest-runner'],
    test_suite='tests',
    tests_require=['pep8', 'pytest-cov', 'pytest-pep8', 'pytest'],
    author='O.S. Systems Software LTDA',
    author_email='contato@ossystems.com.br',
    url='http://www.ossystems.com.br',
    license='MIT',
    zip_safe=False,
)
