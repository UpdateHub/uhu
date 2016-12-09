# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import json

from click.testing import CliRunner

from efu.cli.product import use_command
from efu.utils import LOCAL_CONFIG_VAR

from utils import EnvironmentFixtureMixin, FileFixtureMixin, EFUTestCase


class ProductTestCase(EnvironmentFixtureMixin, FileFixtureMixin, EFUTestCase):

    def setUp(self):
        self.runner = CliRunner()
        self.config_fn = '/tmp/.efu'
        self.addCleanup(self.remove_file, self.config_fn)
        self.set_env_var(LOCAL_CONFIG_VAR, self.config_fn)

    def test_use_command_can_set_a_product(self):
        self.runner.invoke(use_command, args=['42'])
        with open(self.config_fn) as fp:
            config = json.load(fp)
        self.assertEqual(config['product'], '42')

    def test_use_command_returns_0_when_successful(self):
        result = self.runner.invoke(use_command, args=['42'])
        self.assertEqual(result.exit_code, 0)
