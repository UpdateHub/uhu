# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import argparse
import os

from efu.upload import upload_patch


class EFUParser(object):

    def __init__(self):
        self.parser = argparse.ArgumentParser()
        self.subparsers = self.parser.add_subparsers()
        self.set_upload_parser()
        self.args = self.parser.parse_args()
        self.check_arguments()
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
        if os.path.isfile(filename):
            upload_patch(filename)
        else:
            self.parser.error('file {} does not exist'.format(filename))

    def check_arguments(self):
        """
        Checks if args is not empty. This is necessary since we are
        going to use subparser instead of common arguments.
        """
        if not any((self.args._get_args(), self.args._get_kwargs())):
            self.parser.error('You must provide a command (e.g. upload)')

    def run(self):
        self.args.handler()


def main():
    EFUParser()
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
