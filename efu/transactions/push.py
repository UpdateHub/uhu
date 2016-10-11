# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import json

from ..core.object import ObjectUploadResult
from ..http.request import Request
from ..utils import get_server_url, validate_schema

from . import exceptions


class Push:

    def __init__(self, package, callback=None):
        self.package = package
        self.upload_list = None
        self.start_push_url = get_server_url(
            '/products/{}/packages'.format(self.package.product))
        self.finish_push_url = None
        self.callback = callback

    def start_push(self):
        body = self.package.serialize()
        validate_schema('metadata.json', body['metadata'])
        response = Request(
            self.start_push_url,
            method='POST',
            payload=json.dumps(body),
            json=True,
        ).send()
        if self.callback is not None:
            self.callback.push_start(response)
        if response.status_code != 201:
            raise exceptions.StartPushError(
                'It was not possible to start pushing')
        push = response.json()
        self.upload_list = push['uploads']
        self.finish_push_url = push['finish_url']

    def upload_objects(self):
        results = []
        for conf in self.upload_list:
            obj = self.package.objects[conf['object_id']]
            results.append(obj.upload(conf, self.callback))
        # stores all upload results
        for result in results:
            if not ObjectUploadResult.is_ok(result):
                raise exceptions.UploadError(
                    'Some objects has not been fully uploaded')

    def finish_push(self):
        response = Request(self.finish_push_url, 'POST').send()
        self.package.uid = response.json().get('package_id')
        if self.callback is not None:
            self.callback.push_finish(self.package, response)
        if response.status_code != 201:
            raise exceptions.FinishPushError(
                'It was not possible to finish push')
