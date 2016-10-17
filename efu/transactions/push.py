# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import json

from ..core.object import ObjectUploadResult
from ..http.request import Request
from ..utils import call, get_server_url, validate_schema

from . import exceptions


class Push:

    def __init__(self, package, callback=None):
        self.package = package
        self.start_push_url = get_server_url(
            '/products/{}/packages'.format(self.package.product))
        self.callback = callback

    @property
    def finish_push_url(self):
        path = '/products/{}/packages/{}/finish'.format(
            self.package.product, self.package.uid)
        return get_server_url(path)

    def start_push(self):
        body = self.package.metadata()
        validate_schema('metadata.json', body)
        response = Request(
            self.start_push_url, method='POST',
            payload=json.dumps(body), json=True).send()
        call(self.callback, 'push_start', response)
        response_body = response.json()
        if response.status_code != 201:
            errors = '\n'.join(response_body.get('errors', []))
            error_msg = 'It was not possible to start pushing:\n{}'
            raise exceptions.StartPushError(error_msg.format(errors))
        self.package.uid = response_body['package-uid']

    def upload_objects(self):
        results = []
        for obj in self.package.objects.values():
            results.append(obj.upload(
                self.package.product, self.package.uid, self.callback))
        for result in results:
            if not ObjectUploadResult.is_ok(result):
                raise exceptions.UploadError(
                    'Some objects has not been fully uploaded')

    def finish_push(self):
        response = Request(self.finish_push_url, 'POST').send()
        call(self.callback, 'push_finish', self.package, response)
        if response.status_code != 202:
            errors = '\n'.join(response.json()['errors'])
            error_msg = 'It was not possible to finish pushing:\n{}'
            raise exceptions.FinishPushError(error_msg.format(errors))
