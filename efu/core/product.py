# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import json
import os

from ..utils import get_local_config, get_local_config_file


class Product:

    def __init__(self):
        self._config = get_local_config()
        self.uid = self._config['product']

    @classmethod
    def use(cls, uid, force=False):
        config_fn = get_local_config_file()
        if os.path.exists(config_fn) and not force:
            raise FileExistsError('Local config file already exists')
        config = {'product': uid}
        with open(config_fn, 'w') as fp:
            json.dump(config, fp)
        return Product()
