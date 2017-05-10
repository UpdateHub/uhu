# Copyright (C) 2017 O.S. Systems Software LTDA.
# This software is released under the MIT License

from click.testing import CliRunner

from efu.cli.package import push_command
from efu.core.package import Package
from efu.core.manager import InstallationSetMode
from efu.utils import LOCAL_CONFIG_VAR, SERVER_URL_VAR

from utils import BasePushTestCase


class PushCommandMixin:

    def setUp(self):
        super().setUp()
        self.runner = CliRunner()
        self.pkg_fn = self.create_file('')
        self.set_env_var(LOCAL_CONFIG_VAR, self.pkg_fn)
        self.package.dump(self.pkg_fn)


class PushCommandTestCase(PushCommandMixin, BasePushTestCase):

    def test_push_command_returns_0_when_success(self):
        self.set_push(self.package, self.package_uid)
        result = self.runner.invoke(push_command, catch_exceptions=False)
        self.assertEqual(result.exit_code, 0)

    def test_push_command_returns_2_if_error_on_start(self):
        self.set_push(self.package, self.package_uid, start_success=False)
        result = self.runner.invoke(push_command, catch_exceptions=False)
        self.assertEqual(result.exit_code, 2)

    def test_push_command_returns_2_if_error_when_uploading(self):
        self.set_push(self.package, self.package_uid, upload_success=False)
        result = self.runner.invoke(push_command, catch_exceptions=False)
        self.assertEqual(result.exit_code, 2)

    def test_push_command_returns_2_if_error_on_finish(self):
        self.set_push(self.package, self.package_uid, finish_success=False)
        result = self.runner.invoke(push_command, catch_exceptions=False)
        self.assertEqual(result.exit_code, 2)

    def test_push_command_returns_3_if_cant_establish_connection(self):
        self.set_env_var(SERVER_URL_VAR, 'http://easyfota-unreachable.com')
        self.set_push(self.package, self.package_uid)
        result = self.runner.invoke(push_command, catch_exceptions=False)
        self.assertEqual(result.exit_code, 3)

    def test_push_command_returns_4_if_invalid_schema(self):
        self.package = Package(InstallationSetMode.ActiveInactive)
        self.package.dump(self.pkg_fn)
        self.set_push(self.package, self.package_uid)
        result = self.runner.invoke(push_command, catch_exceptions=False)
        self.assertEqual(result.exit_code, 4)
