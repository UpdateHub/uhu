# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

from ..core.utils import load_package
from ..http.request import Request
from ..utils import get_server_url

from .exceptions import CommitDoesNotExist


def get_commit_status(commit_id):
    package = load_package()
    url = get_server_url('/products/{product}/commits/{commit}/status'.format(
        product=package.get('product'), commit=commit_id
    ))
    response = Request(url, 'GET', json=True).send()
    if response.status_code == 200:
        return response.json().get('status')
    raise CommitDoesNotExist
