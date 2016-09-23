# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import hashlib
import os

from ..http.request import Request
from ..utils import get_server_url


class DownloadObjectResult:
    SUCCESS = 0
    EXISTS = 1
    ERROR = 2


class Pull:

    def __init__(self, package):
        self.package = package
        self.metadata = None
        self.existent_files = []

    def get_metadata(self):
        path = '/products/{product}/packages/{package}'.format(
            product=self.package.product, package=self.package.uid)
        response = Request(get_server_url(path), 'GET').send()
        if not response.ok:
            raise ValueError('Package not found')
        self.metadata = response.json()

    def check_local_files(self, package):
        '''
        Verifies if local files will not be overwritten by incoming files.

        Also, it populates self.existent_files with files that must
        not be downloaded.
        '''
        for obj in package:
            if not os.path.exists(obj.filename):
                continue  # File does not exist
            sha256sum = hashlib.sha256()
            for chunk in obj:
                sha256sum.update(chunk)
            if sha256sum.hexdigest() != obj.sha256sum:
                # Local file diverges from server file
                raise FileExistsError(
                    '{} will be overwritten', obj.filename)
            # Local file is equal to server file
            self.existent_files.append(obj.filename)

    def download_object(self, obj):
        if obj.filename in self.existent_files:
            return DownloadObjectResult.EXISTS
        download_path = '/products/{product}/objects/{obj}'.format(
            product=self.package.product, obj=obj.sha256sum)
        response = Request(
            get_server_url(download_path), 'GET', stream=True).send()
        if response.ok:
            with open(obj.filename, 'wb') as fp:
                for chunk in response.iter_content():
                    fp.write(chunk)
            return DownloadObjectResult.SUCCESS
        else:
            return DownloadObjectResult.ERROR
