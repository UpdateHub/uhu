# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

from ..core import Object, Package
from ..http.request import Request
from ..utils import get_server_url, get_local_config_file


class DownloadObjectStatus:
    SUCCESS = 0
    EXISTS = 1
    ERROR = 2


class Pull(object):

    def __init__(self, product, package_id):
        self.product = product
        self.package_id = package_id
        self.existent_files = []

    def get_metadata(self):
        path = '/products/{product}/packages/{package}'.format(
            product=self.product, package=self.package_id)
        url = get_server_url(path)
        response = Request(url, 'GET').send()
        if response.ok:
            metadata = response.json()
            return metadata
        raise ValueError('Package not found')

    def _get_object(self, obj):
        if obj['filename'] in self.existent_files:
            return DownloadObjectStatus.EXISTS

        download_path = '/products/{product}/objects/{obj}'.format(
            product=self.product, obj=obj['sha256sum'])
        url = get_server_url(download_path)
        response = Request(url, 'GET', stream=True).send()
        if response.ok:
            with open(obj['filename'], 'wb') as fp:
                for chunk in response.iter_content():
                    fp.write(chunk)
            return DownloadObjectStatus.SUCCESS
        else:
            return DownloadObjectStatus.ERROR

    def check_local_files(self, pkg_objects):
        '''
        Verifies if local files will not be overwritten by commit files.

        Also, it populates self.existent_files with files that must
        not be downloaded.
        '''
        for pkg_obj in pkg_objects:
            try:
                obj = Object(pkg_obj['filename'])
                obj.load()
                if obj.sha256sum != pkg_obj['sha256sum']:
                    # files with same name with different content.
                    # Must abort pull.
                    raise FileExistsError
                else:
                    # file exists and it is identical to the local.
                    # We can pull, but it should not be downloaded.
                    self.existent_files.append(obj.filename)
            except FileNotFoundError:
                # file does not exist, so we can download it
                pass

    def pull(self, full=True):
        metadata = self.get_metadata()
        package = Package.from_metadata(metadata)
        package.dump(get_local_config_file())
        if full:
            objects = metadata.get('objects')
            if objects is not None:
                self.check_local_files(objects)
                for obj in objects:
                    self._get_object(obj)
        return package
