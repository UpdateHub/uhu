# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import json

from ..package import File
from ..package.exceptions import InvalidFileError
from ..package.utils import load_package, create_package_from_metadata
from ..push.exceptions import CommitDoesNotExist
from ..utils import get_server_url
from ..request import Request


class DownloadObjectStatus:
    SUCCESS = 0
    EXISTS = 1
    ERROR = 2


class Pull(object):

    def __init__(self, commit_id):
        self.package = load_package()
        self.commit_id = commit_id
        self.commit_file = 'efu-commit-{}.json'.format(self.commit_id)
        self.existent_files = []

    def get_metadata(self):
        path = '/products/{product}/commits/{commit}'.format(
            product=self.package['product'], commit=self.commit_id)
        url = get_server_url(path)
        response = Request(url, 'GET').send()
        if response.ok:
            metadata = response.json()
            with open(self.commit_file, 'w') as fp:
                json.dump(metadata, fp)
            return metadata
        raise CommitDoesNotExist

    def _get_object(self, image):
        if image['filename'] in self.existent_files:
            return DownloadObjectStatus.EXISTS

        download_path = '/products/{product}/objects/{obj}'.format(
            product=self.package['product'], obj=image['sha256sum'])
        url = get_server_url(download_path)
        response = Request(url, 'GET', stream=True).send()
        if response.ok:
            with open(image['filename'], 'wb') as fp:
                for chunk in response.iter_content():
                    fp.write(chunk)
            return DownloadObjectStatus.SUCCESS
        else:
            return DownloadObjectStatus.ERROR

    def check_local_files(self, images):
        '''
        Verifies if local files will not be overwritten by commit files.

        Also, it populates self.existent_files with files that must
        not be downloaded.
        '''
        for image in images:
            try:
                file = File(image['filename'])
                if file.sha256sum != image['sha256sum']:
                    # files with same name with different content.
                    # Must abort pull.
                    raise FileExistsError
                else:
                    # file exists and it is identical to the local.
                    # We can pull, but it should not be downloaded.
                    self.existent_files.append(file.name)
            except InvalidFileError:
                # file does not exist, so we can download it
                pass

    def pull(self, full=True):
        metadata = self.get_metadata()
        create_package_from_metadata(metadata)
        if full:
            images = metadata.get('images')
            if images is not None:
                self.check_local_files(images)
                return [self._get_object(image) for image in images]
