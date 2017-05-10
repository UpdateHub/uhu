# Copyright (C) 2017 O.S. Systems Software LTDA.
# This software is released under the GPL-2.0 License

from setuptools import setup


def get_version():
    from efu import __version__
    return __version__


setup(
    name='updatehub-utils',
    description='updatehub description',
    keywords='fota ota firmware update utility',
    version=get_version(),
    packages=[
        'efu',
        'efu.config',
        'efu.push',
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
    license='GPL-2.0',
    zip_safe=False,
)
