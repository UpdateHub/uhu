# Copyright (C) 2017 O.S. Systems Software LTDA.
# This software is released under the GPL-2.0 License

import json

from click.testing import CliRunner

from uhu.cli.product import use_command
from uhu.utils import LOCAL_CONFIG_VAR

from utils import EnvironmentFixtureMixin, FileFixtureMixin, UHUTestCase


class ProductTestCase(EnvironmentFixtureMixin, FileFixtureMixin, UHUTestCase):

    def setUp(self):
        self.runner = CliRunner()
        self.config_fn = '/tmp/.uhu'
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
