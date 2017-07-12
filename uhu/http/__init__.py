# Copyright (C) 2017 O.S. Systems Software LTDA.
# SPDX-License-Identifier: GPL-2.0

import requests

from ._request import Request


class HTTPError(requests.RequestException):
    """A generic error for HTTP requests."""


def request(method, url, *args, sign=True, **kwargs):
    try:
        if sign:
            return Request(url, method, *args, **kwargs).send()
        return requests.request(method, url, *args, **kwargs)
    except (requests.exceptions.MissingSchema,
            requests.exceptions.InvalidSchema,
            requests.exceptions.URLRequired,
            requests.exceptions.InvalidURL):
        raise HTTPError('You have provided an invalid server URL.')
    except (requests.ConnectionError, requests.ConnectTimeout):
        raise HTTPError('Server is not available. Try again later.')
    except requests.RequestException:
        raise HTTPError('A unexpected request error ocurred. Try again later.')


def get(url, *args, **kwargs):
    return request('GET', url, *args, **kwargs)


def post(url, *args, **kwargs):
    return request('POST', url, *args, **kwargs)


def put(url, *args, **kwargs):
    return request('PUT', url, *args, **kwargs)


def format_server_error(response):
    base = 'It was not possible to start pushing:'
    error = response.get('error_message')
    if error is not None:
        return '{} {}.'.format(base, error)
    errors = response.get('errors')
    if errors is None:
        return '{} unknown error.'.format(base)
    try:
        error = '\n'.join(['  - {}: {}'.format(key, ', '.join(error))
                           for key, error in errors.items()])
        error = '\n{}'.format(error)
    except (AttributeError, TypeError):
        error = ' unknown error'
    return '{}{}.'.format(base, error)
