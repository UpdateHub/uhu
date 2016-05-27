# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import argparse
import sys


class CLIBaseSubparser(object):

    def __init__(self):
        self.parser = None
        self.commands = None

    def set(self, parser):
        """
        This method must be responsible for adding itself as a
        subparser into parser.
        """
        raise NotImplementedError

    def handler(self):
        """
        This method must be responsible for the subparser main entry
        point
        """
        raise NotImplementedError


class CLIParser(object):

    def __init__(self, subparsers=None):
        self.parser = argparse.ArgumentParser()
        self.set_subparsers(subparsers)
        self.args = self.parser.parse_args()
        self.check_has_arguments()
        self.run()

    def set_subparsers(self, subparsers):
        if subparsers is not None:
            self.subparsers = self.parser.add_subparsers()
            for parser in subparsers:
                parser.set(self)

    def check_has_arguments(self):
        """
        Checks if args is not empty. This is necessary since we are
        going to use subparser instead of common arguments.
        """
        if len(sys.argv) == 1:
            self.parser.error('You must provide a command (e.g. upload)')

    def run(self):
        self.args.handler()
