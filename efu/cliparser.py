# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import argparse
import sys

from .upload import upload_patch


class CLIParser(object):

    def __init__(self):
        self.parser = argparse.ArgumentParser()
        self.subparsers = self.parser.add_subparsers()
        self.set_upload_parser()
        self.args = self.parser.parse_args()
        self.check_has_arguments()
        self.run()

    def set_upload_parser(self):
        """
        Creates and configures the upload parser
        """
        self.upload_parser = self.subparsers.add_parser(
            'upload',
            help='Uploads a patch',
        )
        self.upload_parser.add_argument('filename', help='patch file name')
        self.upload_parser.set_defaults(handler=self.upload_handler)

    def upload_handler(self):
        """
        This method will be responsible for validating arguments and
        sending them to the upload utility
        """
        filename = self.args.filename
        try:
            upload_patch(filename)
        except FileNotFoundError:
            self.parser.error('file {} does not exist'.format(filename))

    def check_has_arguments(self):
        """
        Checks if args is not empty. This is necessary since we are
        going to use subparser instead of common arguments.
        """
        if len(sys.argv) == 1:
            self.parser.error('You must provide a command (e.g. upload)')

    def run(self):
        self.args.handler()
