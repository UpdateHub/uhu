# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

from ..package import File
from ..package.exceptions import InvalidFileError
from ..utils import get_server_url
from ..request import Request


class DownloadObjectStatus:
    SUCCESS = 0
    EXISTS = 1
    ERROR = 2


class Pull(object):

    def __init__(self, product_id, commit_id):
        self.product_id = product_id
        self.commit_id = commit_id
        self.existent_files = []

    def get_metadata(self):
        path = '/products/{product}/commits/{commit}'.format(
            product=self.product_id, commit=self.commit_id)
        url = get_server_url(path)
        response = Request(url, 'GET', '').send()
        if response.ok:
            return response.json()
        return None

    def _get_object(self, image):
        if image['filename'] in self.existent_files:
            return DownloadObjectStatus.EXISTS

        download_path = '/products/{product}/objects/{obj}'.format(
            product=self.product_id, obj=image['sha256sum'])
        url = get_server_url(download_path)
        response = Request(url, 'GET', '', stream=True).send()
        if response.ok:
            with open(image['filename'], 'wb') as fp:
                for chunk in response.iter_content():
                    fp.write(chunk)
            return DownloadObjectStatus.SUCCESS
        else:
            return DownloadObjectStatus.ERROR

    def can_download(self, images):
        '''
        Verifies if files will not overwrite existent local files if they
        diverges.

        Also, it populates self.existent_files with files that must be
        not downloaded.
        '''
        for image in images:
            try:
                file = File(image['filename'])
                if file.sha256sum != image['sha256sum']:
                    # files with same name with different content.
                    # Must abort pull.
                    return False
                else:
                    # file exists and it is identical to the local.
                    # We can pull, but it should not be downloaded.
                    self.existent_files.append(file.name)
            except InvalidFileError:
                # file does not exist, so we can download it
                pass
        # File does not exists or it is identical to local one.
        # We can safely start to download.
        return True

    def pull(self):
        metadata = self.get_metadata()
        images = metadata.get('images')
        if images is not None and self.can_download(images):
            return [self._get_object(image) for image in images]
        return None
