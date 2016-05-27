# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

from ..cliparser import CLIBaseSubparser
from .upload import upload_patch


class UploadParser(CLIBaseSubparser):

    def set(self, parser):
        """
        Creates and configures the upload parser
        """
        self.parser = parser
        self.parser.upload_parser = self.parser.subparsers.add_parser(
            'upload',
            help='Uploads a patch',
        )
        self.parser.upload_parser.add_argument(
            'filename',
            help='patch file name',
        )
        self.parser.upload_parser.set_defaults(handler=self.handler)

    def handler(self):
        """
        This method will be responsible for validating arguments and
        sending them to the upload utility
        """
        filename = self.parser.args.filename
        try:
            upload_patch(filename)
        except FileNotFoundError:
            self.parser.error('file {} does not exist'.format(filename))
