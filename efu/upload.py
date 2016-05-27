# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import os


def upload_patch(filename):
    if not os.path.isfile(filename):
        raise FileNotFoundError
    print('uploading {}'.format(filename))
