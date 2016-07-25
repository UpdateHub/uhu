# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import threading
from functools import wraps
from http.server import BaseHTTPRequestHandler, HTTPServer
from time import sleep


class Request(object):

    def __init__(self, request):
        addr, port = request.server.server_address
        self.url = 'http://{}:{}{}'.format(addr, port, request.path)
        self.method = request.command
        self.headers = request.headers
        content_length = int(self.headers.get('Content-length', 0))
        self.body = request.rfile.read(content_length)


class Response(object):

    def __init__(self, status_code, headers, body=None):
        self.status_code = status_code
        self.headers = headers
        try:
            self.body = body.encode()
        except AttributeError:
            self.body = body


class RequestHandler(BaseHTTPRequestHandler):
    '''
    This class is responsible for returning pre registered responses.

    It is able to return a 404 if there is no response registered for
    a given request. Also, it responds a 405 if a method is not
    allowed in a given path.
    '''

    def _simulate_application(self):
        '''
        Method that simiulates a server process
        '''
        if self.server.simulate_application:
            sleep(0.1)

    def generic_handler(f):
        @wraps(f)
        def wrapped(self):
            # Adds request into the request history
            self.server.requests.append(Request(self))

            self._simulate_application()

            # Check if path exists. If not, throw a 404.
            path = self.server.responses.get(self.path, None)
            if path is None:
                self.send_error(
                    404,
                    '{} is not a registered path'.format(self.path)
                )
                return None

            # Check if method is allowed. If not, throw a 405.
            response = path.get(self.command, None)
            if response is None:
                self.send_error(
                    405,
                    '{} method is not allowed'.format(self.command)
                )
                return None

            # Start to send the response
            self.send_response(response.status_code)
            for header in response.headers.items():
                self.send_header(*header)
            self.end_headers()
            if response.body:
                self.wfile.write(response.body)

        return wrapped

    @generic_handler
    def do_POST(self):
        '''
        POST handler. Override it if you do not want to use generic
        handler.
        '''

    @generic_handler
    def do_GET(self):
        '''
        GET handler. Override it if you do not want to use generic
        handler.
        '''

    @generic_handler
    def do_PUT(self):
        '''
        PUT handler. Override it if you do not want to use generic
        handler.
        '''

    @generic_handler
    def do_DELETE(self):
        '''
        DELETE handler. Override it if you do not want to use generic
        handler.
        '''

    @generic_handler
    def do_HEAD(self):
        '''
        HEAD handler. Override it if you do not want to use generic
        handler.
        '''


class HTTPMockServer(HTTPServer):
    '''
    Basic HTTP mock server that is able to map responses for a given
    request.

    This server storages all requests (good and bad ones) received so
    it is easy to debug how your code is making requests.
    '''

    responses = {}  # where responses are registered
    requests = []  # where request history is storaged

    def __init__(self, simulate_application=False):
        super().__init__(('0.0.0.0', 0), RequestHandler)
        self.simulate_application = simulate_application

    def start(self):
        threading.Thread(target=self.serve_forever).start()

    def url(self, path='/'):
        '''
        Returns URL that matches this server address.

        By default, it returns the server web root (eg. http://127.0.0.1:80/).

        If path is provided, it is appended into the end of the url so
        you can create any URI (eg. http://127.0.0.1:80/this/is/a/path).
        '''
        return 'http://{addr}:{port}{path}'.format(
            addr=self.server_address[0],
            port=self.server_address[1],
            path=path
        )

    @classmethod
    def register_response(cls, path, method='GET', headers={},
                          body=None, status_code=200):
        '''
        This method is responsible for registering a response for a given
        request.
        '''
        cls.responses[path] = cls.responses.get(path, {})
        cls.responses[path][method] = Response(status_code, headers, body)

    @classmethod
    def clear_requests(cls):
        '''
        Cleans request history.
        '''
        cls.requests = []

    @classmethod
    def clear_responses(cls):
        '''
        Removes all registered responses.
        '''
        cls.responses = {}

    @classmethod
    def clear_history(cls):
        cls.clear_requests()
        cls.clear_responses()
