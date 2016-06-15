# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import json
from functools import wraps
from http.server import BaseHTTPRequestHandler


class RequestHandler(BaseHTTPRequestHandler):

    body = None
    code = 200
    response_headers = {}

    @classmethod
    def reset_defaults(cls):
        cls.body = None
        cls.code = 200
        cls.response_headers = {}

    def generic_handler(f):
        @wraps(f)
        def wrapped(self):
            self.send_response(self.code)
            for header, value in self.response_headers.items():
                self.send_header(header, value)
            self.end_headers()
            if self.body:
                body = json.dumps(self.body).encode()
                self.wfile.write(body)
            RequestHandler.reset_defaults()
        return wrapped

    @generic_handler
    def do_POST(self):
        pass

    @generic_handler
    def do_GET(self):
        pass

    @generic_handler
    def do_PUT(self):
        pass

    @generic_handler
    def do_DELETE(self):
        pass

    @generic_handler
    def do_HEAD(self):
        pass
