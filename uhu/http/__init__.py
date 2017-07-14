# Copyright (C) 2017 O.S. Systems Software LTDA.
# SPDX-License-Identifier: GPL-2.0

import requests

from ._request import Request


UNKNOWN_ERROR = 'A unexpected request error ocurred. Try again later.'


class HTTPError(requests.RequestException):
    """A generic error for HTTP requests."""


def request(method, url, *args, sign=True, **kwargs):
    try:
        if sign:
            response = Request(url, method, *args, **kwargs).send()
        else:
            response = requests.request(method, url, *args, **kwargs)
    except (requests.exceptions.MissingSchema,
            requests.exceptions.InvalidSchema,
            requests.exceptions.URLRequired,
            requests.exceptions.InvalidURL):
        raise HTTPError('You have provided an invalid server URL.')
    except (requests.ConnectionError, requests.ConnectTimeout):
        raise HTTPError('Server is not available. Try again later.')
    except requests.RequestException:
        raise HTTPError(UNKNOWN_ERROR)
    if response.status_code == 401:
        raise HTTPError('Unautorized. Did you set your credentials?')
    elif not response.ok:
        raise HTTPError(format_server_error(response))
    return response


def get(url, *args, **kwargs):
    return request('GET', url, *args, **kwargs)


def post(url, *args, **kwargs):
    return request('POST', url, *args, **kwargs)


def put(url, *args, **kwargs):
    return request('PUT', url, *args, **kwargs)


def format_server_error(response):
    try:
        body = response.json()
    except ValueError:
        return UNKNOWN_ERROR

    message = body.get('error_message')
    if message:
        return message

    errors = body.get('errors')
    if errors:
        try:
            return '\n'.join(
                ['- {}: {}'.format(k, ', '.join(v))
                 for k, v in errors.items()])
        except (AttributeError, TypeError):
            pass

    return UNKNOWN_ERROR


def read_stream(response, chunk_size):
    try:
        for chunk in response.iter_content(chunk_size):
            yield chunk
    except requests.RequestException:
        raise HTTPError('Could not stream data.')
