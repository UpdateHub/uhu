# Copyright (C) 2017 O.S. Systems Software LTDA.
# This software is released under the GPL-2.0 License

from setuptools import find_packages, setup

from uhu import get_version


setup(
    name='uhu',
    description="UpdateHub's firmware update package management utilities",
    keywords='industrial-linux embedded-linux embedded firmware-updates linux update-service',  # nopep8
    version=get_version(),
    packages=find_packages(exclude=['tests*']),
    entry_points={
        'console_scripts': ['uhu=uhu.cli:cli']
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
    license='GPL-2.0',
    zip_safe=False,
)
