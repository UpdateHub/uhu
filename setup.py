# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

from setuptools import setup


def get_version():
    from efu import __version__
    return __version__


setup(
    name='easyfota-utils',
    description='Easy Firmware Over The Air command line utility',
    keywords='fota ota firmware update utility',
    version=get_version(),
    packages=[
        'efu',
        'efu.config',
        'efu.push',
        'efu.pull',
    ],
    entry_points={
        'console_scripts': ['efu=efu.__main__:main']
    },
    install_requires=[
        'click==6.6',
        'progress==1.2',
        'requests==2.10.0',
    ],
    author='O.S. Systems Software LTDA',
    author_email='contato@ossystems.com.br',
    url='http://www.ossystems.com.br',
    license='MIT',
    zip_safe=False,
)
