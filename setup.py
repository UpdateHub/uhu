# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

from pip.req import parse_requirements
from setuptools import setup


def get_test_requirements():
    file = parse_requirements('requirements-test.txt', session=False)
    requirements = [str(req.req) for req in file]
    return requirements


setup(
    name='easyfota-utils',
    description='Easy Firmware Over The Air command line utility',
    keywords='fota ota firmware update utility',
    version='0.0.dev0',
    packages=['efu'],
    entry_points={
        'console_scripts': ['efu=efu.__main__:main']
    },
    setup_requires=['pytest-runner'],
    test_suite='tests',
    tests_require=get_test_requirements(),
    author='O.S. Systems Software LTDA',
    author_email='contato@ossystems.com.br',
    url='http://www.ossystems.com.br',
    license='MIT',
    zip_safe=False,
)
