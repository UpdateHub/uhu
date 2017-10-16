# Copyright (C) 2017 O.S. Systems Software LTDA.
# SPDX-License-Identifier: GPL-2.0

import requests

from ..utils import get_custom_ca_certs_file
from ._request import Request, HTTPError


UNKNOWN_ERROR = 'A unexpected request error ocurred. Try again later.'


def request(method, url, *args, sign=True, **kwargs):
    custom_ca_certs_file = get_custom_ca_certs_file()

    if custom_ca_certs_file is not None and 'verify' not in kwargs:
        kwargs['verify'] = custom_ca_certs_file

    try:
        if sign:
            response = Request(url, method, *args, **kwargs).send()
        else:
            response = requests.request(
                method, url, *args, timeout=30, **kwargs)
    except HTTPError as error:
        raise error
    except (requests.exceptions.MissingSchema,
            requests.exceptions.InvalidSchema,
            requests.exceptions.URLRequired,
            requests.exceptions.InvalidURL):
        raise HTTPError('You have provided an invalid server URL.')
    except requests.ConnectTimeout:
        raise HTTPError('Connection timed out. Try again later.')
    except requests.ConnectionError:
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
