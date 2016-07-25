# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import click

from . import config


@click.group(name='config')
def config_command():
    ''' Configures efu utility. '''
    pass


@click.command()
def init():
    ''' Sets efu required initial configuration. '''
    access_id = input('EasyFOTA Access Key ID: ')
    access_secret = input('EasyFota Systems Secret Access Key: ')
    config.set_initial(access_id, access_secret)


@click.command(name='set')
@click.argument('entry')
@click.argument('value')
@click.option('--section', help='Section to write the configuration')
def set_(entry, value, section):
    '''
    Sets the given VALUE in a configuration ENTRY.
    '''
    config.set(entry, value, section=section)


@click.command()
@click.argument('entry')
@click.option('--section', help='Section to write the configuration')
def get(entry, section):
    '''
    Gets the value from a given ENTRY.
    '''
    value = config.get(entry, section=section)
    if value:
        print(value)


config_command.add_command(set_)
config_command.add_command(get)
config_command.add_command(init)
