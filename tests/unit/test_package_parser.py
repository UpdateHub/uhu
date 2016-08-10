# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import json
import os
import unittest
from unittest.mock import Mock, patch

import click
from click.testing import CliRunner

import efu.package.parser_utils
import efu.package.parser

from efu.package import exceptions
from efu.package.parser import (
    add_command, remove_command, show_command,
    export_command, cleanup_command)
from efu.package.parser_modes import (
    inject_default_values, validate_dependencies,
    clean_params, interactive_mode, explicit_mode)
from efu.package.parser_options import INSTALL_MODE, FORMAT_OPTIONS
from efu.package.parser_utils import click as patched_click
from efu.package.parser_utils import (
    InstallMode, InstallModeChoiceType,
    ImageOption, LazyPromptOption,
    get_param_names, image_prompt, NONE_DEFAULT,
    replace_format, replace_underscores, replace_install_mode
)


class PromptTestCase(unittest.TestCase):

    def test_basic_image_prompt(self):
        observed = image_prompt('food', ':')
        expected = 'food:'
        self.assertEqual(observed, expected)

    def test_image_prompt_with_simple_default(self):
        observed = image_prompt('food', ':', default='spam', show_default=True)
        expected = 'food [spam]:'
        self.assertEqual(observed, expected)

    def test_image_prompt_with_empty_string_as_default(self):
        observed = image_prompt('food', ':', default='', show_default=True)
        expected = 'food [None]:'
        self.assertEqual(observed, expected)

    def test_image_prompt_with_NONE_DEFAULT(self):
        observed = image_prompt('food', ':', default='', show_default=True)
        expected = 'food [None]:'
        self.assertEqual(observed, expected)

    def test_patched_click_uses_image_prompt(self):
        expected = id(image_prompt)
        observed = id(patched_click.termui._build_prompt)
        self.assertEqual(expected, observed)

    def text_patched_build_prompt_is_different_from_click_build_prompt(self):
        args = {
            'text': 'food',
            'suffix': ':',
            'show_default': True,
            'default': 'spam spam eggs ham'
        }
        expected = patched_click.termui._build_prompt(**args)
        observed = click.termui._build_prompt(**args)
        self.assertNotEqual(observed, expected)


class ParserUtilsTestCase(unittest.TestCase):

    def test_get_param_names(self):
        options = [
            click.Option(['--foo']),
            click.Option(['--bar']),
            click.Option(['--spam']),
            click.Option(['--foo-bar']),
        ]
        expected = {'foo', 'bar', 'spam', 'foo_bar'}
        observed = get_param_names(options)
        self.assertEqual(observed, expected)

    def test_can_replace_format_correctly(self):
        image = {'format': True}
        observed = replace_format(image)
        self.assertIn('format?', observed)
        self.assertTrue(observed['format?'])
        self.assertEqual(len(observed), 1)

    def test_replace_format_has_no_side_effects(self):
        image = {'format': True}
        expected = {'format': True}
        replace_format(image)
        self.assertEqual(image, expected)

    def test_replace_format_doesnt_modify_image_if_nothing_to_replace(self):
        image = {'mount-options': True}
        observed = replace_format(image)
        self.assertEqual(image, observed)

    def test_can_replace_underscore(self):
        image = {'install_mode': 'raw'}
        observed = replace_underscores(image)
        self.assertIn('install-mode', observed)
        self.assertEqual(observed['install-mode'], 'raw')
        self.assertEqual(len(observed), 1)

    def test_replace_underscores_has_no_side_effects(self):
        image = {'install_mode': 'raw'}
        expected = {'install_mode': 'raw'}
        replace_underscores(image)
        self.assertEqual(expected, image)

    def test_replace_underscores_returns_same_image_if_no_replace_occurs(self):
        image = {'truncate': True}
        observed = replace_underscores(image)
        self.assertEqual(image, observed)

    def test_can_replace_install_mode(self):
        image = {'install-mode': InstallMode(name='raw')}
        expected = {'install-mode': 'raw'}
        observed = replace_install_mode(image)
        self.assertEqual(observed, expected)

    def test_replace_install_mode_has_no_side_effects(self):
        image = {'install-mode': InstallMode(name='raw')}
        expected = {'install-mode': InstallMode(name='raw')}
        replace_install_mode(image)
        self.assertNotEqual(image, expected)

    def test_replace_install_mode_returns_same_image_if_mode_already_set(self):
        image = {'install-mode': 'raw'}
        observed = replace_install_mode(image)
        self.assertEqual(image, observed)


class InstallModeTestCase(unittest.TestCase):

    def setUp(self):
        self.required1 = click.Option(['--required-1'])
        self.required2 = click.Option(['--required-2'])
        self.optional1 = click.Option(['--optional-1'])
        self.optional2 = click.Option(['--optional-2'])
        self.invalid_option = click.Option(['--invalid'])

        self.options = [self.required1, self.required2,
                        self.optional1, self.optional2]
        self.required_names = {'required_1', 'required_2'}
        self.all_names = {'optional_1', 'optional_2',
                          'required_1', 'required_2'}
        self.mode = InstallMode(
            'copy',
            optional=[self.optional1, self.optional2],
            required=[self.required1, self.required2]
        )

    def test_install_mode_name(self):
        mode = InstallMode('tarball')
        self.assertEqual(mode.name, 'tarball')
        mode = InstallMode('copy')
        self.assertEqual(mode.name, 'copy')

    def test_install_mode_has_all_options(self):
        for option in self.options:
            self.assertIn(option, self.mode.params)

        self.assertEqual(len(self.mode.params), len(self.options))
        self.assertEqual(self.mode._params_names, self.all_names)

    def test_required_options_in_install_mode_are_correct(self):
        self.assertEqual(len(self.mode.required), 2)
        self.assertEqual(self.mode._required_names, self.required_names)

    def test_is_valid_returns_TRUE_when_passing_invalid_option(self):
        self.assertFalse(self.mode.is_valid(self.invalid_option))

    def test_is_valid_return_TRUE_for_all_valid_options(self):
        for option in self.options:
            self.assertTrue(self.mode.is_valid(option))

    def test_is_required_returns_TRUE_for_all_required_options(self):
        self.assertTrue(self.mode.is_required(self.required1))
        self.assertTrue(self.mode.is_required(self.required2))

    def test_is_required_returns_FALSE_for_all_optional_options(self):
        self.assertFalse(self.mode.is_required(self.optional1))
        self.assertFalse(self.mode.is_required(self.optional2))


class InstallModeChoiceTypeTestCase(unittest.TestCase):

    def setUp(self):
        self.required = click.Option(['--required'])
        self.optional = click.Option(['--optional'])

        self.choices = {
            'copy': InstallMode(
                'copy', required=[self.required], optional=[self.optional]),
            'tarball': InstallMode('tarball'),
            'raw': InstallMode('raw')
        }
        self.type = InstallModeChoiceType(self.choices)

    def test_can_initate_type_correctly(self):
        for key in self.choices.keys():
            self.assertIn(key, self.type.choices)

    def test_can_convert_choice_into_install_mode_object(self):
        observed = self.type.convert('copy', object, {})
        self.assertIsInstance(observed, InstallMode)
        self.assertEqual(observed.name, 'copy')
        self.assertEqual(len(observed.params), 2)
        self.assertIn(self.required, observed.required)
        self.assertIn(self.optional, observed.params)


class LazyPromptOptionTestCase(unittest.TestCase):

    def test_lazy_option_always_has_a_prompt_text(self):
        option1 = LazyPromptOption(['--option'], prompt=True)
        self.assertEqual(option1.prompt, 'Option')

        option2 = LazyPromptOption(['--option'])
        self.assertEqual(option2.prompt, 'Option')

    def test_lazy_options_does_not_prompt_when_processing_value(self):
        ''' Makes all assumptions that would make click prompt for a value '''
        ctx = Mock()
        ctx.resilient_parsing = False

        option = LazyPromptOption(['--spam'], prompt=True)
        observed = option.full_process_value(ctx, None)
        self.assertIsNone(observed)

    def test_lazy_options_can_full_process_a_value(self):
        option = LazyPromptOption(['--option'])
        observed = option.full_process_value({}, 1)
        self.assertEqual(observed, 1)

    @patch('efu.package.parser_options.click.prompt')
    def test_prompt_is_called_correctly(self, prompt):
        option = LazyPromptOption(['--option'], default_lazy=100)
        option.prompt_for_value({})
        self.assertTrue(prompt.called)
        args, kw = prompt.call_args
        self.assertEqual(kw['default'], 100)

    @patch('efu.package.parser_options.click.confirm')
    def test_prompt_also_works_for_boolean_flags(self, confirm):
        option = LazyPromptOption(['--spam/--no-spam'], default_lazy=False)
        option.prompt_for_value({})
        self.assertTrue(confirm.called)
        args, kw = confirm.call_args
        self.assertEqual(args[1], False)


class ImageOptionTestCase(unittest.TestCase):

    def test_lazy_option_dependencies(self):
        dep = ImageOption(['--spam'])
        option = ImageOption(['--option'], dependencies=[dep])
        self.assertIn('spam', option.dependencies)

    @patch('efu.package.parser_utils.LazyPromptOption.prompt_for_value')
    def test_prompt_uses_default_lazy_when_provided(self, mock):
        option = ImageOption(['--option'], default_lazy=128)
        self.assertEqual(option.default_lazy, 128)

        ctx = Mock()
        option.prompt_for_value(ctx)
        self.assertEqual(option.default_lazy, 128)

    @patch('efu.package.parser_utils.LazyPromptOption.prompt_for_value')
    def test_prompt_uses_NONE_DEFAULT_when_option_is_not_required(self, mock):
        option = ImageOption(['--option'])
        self.assertIsNone(option.default_lazy)

        ctx = Mock()
        ctx.install_mode.is_required.return_value = False
        option.prompt_for_value(ctx)
        self.assertEqual(option.default_lazy, NONE_DEFAULT)

    @patch('efu.package.parser_utils.LazyPromptOption.prompt_for_value')
    def test_prompt_uses_NONE_when_option_is_required(self, mock):
        option = ImageOption(['--option'])
        self.assertIsNone(option.default_lazy)

        ctx = Mock()
        ctx.install_mode.is_required.return_value = True
        option.prompt_for_value(ctx)
        self.assertIsNone(option.default_lazy)

    def test_raises_when_value_and_install_mode_param_is_missing(self):
        ctx = Mock()
        ctx.install_mode = None
        with self.assertRaises(click.MissingParameter):
            ImageOption.validate(ctx, param=None, value=100)

    def test_raises_when_value_and_param_is_not_valid_in_mode(self):
        install_mode = InstallMode('copy')
        invalid_param = ImageOption(['--truncate'])
        ctx = Mock()
        ctx.install_mode = install_mode
        with self.assertRaises(click.UsageError):
            ImageOption.validate(ctx, param=invalid_param, value=100)

    def test_raises_value_is_not_provided_and_it_is_required(self):
        param = ImageOption(['--filesystem'])
        install_mode = InstallMode('copy', required=[param])
        ctx = Mock()
        ctx.install_mode = install_mode
        with self.assertRaises(click.MissingParameter):
            ImageOption.validate(ctx, param=param, value=None)

    def test_validate_returns_value_when_it_is_valid(self):
        param = ImageOption(['--filesystem'])
        install_mode = InstallMode('copy', required=[param])
        ctx = Mock()
        ctx.install_mode = install_mode
        observed = ImageOption.validate(ctx, param=param, value='ext4')
        self.assertEqual(observed, 'ext4')


class OptionsCallbackTestCase(unittest.TestCase):

    def test_image_options_callback(self):
        mode = InstallMode('copy')
        ctx = Mock()
        INSTALL_MODE.callback(ctx, INSTALL_MODE, mode)
        self.assertEqual(mode, ctx.install_mode)

    def test_format_options_callback_returns_false_when_missing_format(self):
        params = {}
        result, _ = FORMAT_OPTIONS.callback_lazy(params)
        self.assertFalse(result)

    def test_format_options_callback_returns_False_when_format_is_False(self):
        params = {'format': False}
        result, _ = FORMAT_OPTIONS.callback_lazy(params)
        self.assertFalse(result)

    def test_format_options_callback_doesnt_raise_when_format_is_True(self):
        params = {'format': True}
        FORMAT_OPTIONS.callback_lazy(params)


class PostParamEvaluationTestCase(unittest.TestCase):

    def setUp(self):
        self.option = ImageOption(['--option'], default_lazy='default-value')
        self.dependency = ImageOption(
            ['--dependency'], dependencies=[self.option])
        self.mode = InstallMode(
            'copy', optional=[self.dependency, self.option])

    def test_inject_values_do_not_overwrite_passed_values(self):
        passed_params = {'option': 'eggs'}
        observed = inject_default_values(self.mode, passed_params)
        self.assertEqual(passed_params['option'], 'eggs')

    def test_can_inject_values_in_passed_params(self):
        passed_params = {}
        observed = inject_default_values(self.mode, passed_params)
        self.assertEqual(passed_params['option'], 'default-value')

    def test_can_inject_values_keeps_options_without_default_values(self):
        passed_params = {'argument': 'eggs'}
        observed = inject_default_values(self.mode, passed_params)
        self.assertEqual(len(observed), 2)
        self.assertEqual(passed_params['option'], 'default-value')
        self.assertEqual(passed_params['argument'], 'eggs')

    def test_validate_dependencies_returns_NONE_if_valid(self):
        passed_params = {'dependency': 'spam', 'option': 'eggs'}
        observed = validate_dependencies(self.mode, passed_params)
        self.assertIsNone(observed)

    def test_validate_dependencies_raises_when_missing_dependency(self):
        passed_params = {'dependency': 'eggs'}
        with self.assertRaises(click.BadOptionUsage):
            validate_dependencies(self.mode, passed_params)

    def test_validate_dependencies_raises_with_callback_lazy(self):
        dependency = ImageOption(
            ['--dependency'], dependencies=[self.option],
            callback_lazy=lambda x: (False, None))
        mode = InstallMode(
            'copy', optional=[dependency, self.option])
        passed_params = {'dependency': 'eggs', 'option': 'ham'}
        with self.assertRaises(click.BadOptionUsage):
            validate_dependencies(mode, passed_params)

    def test_validate_dependencies_returns_NONE_if_callback_returns_true(self):
        dependency = ImageOption(
            ['--dependency'], dependencies=[self.option],
            callback_lazy=lambda x: (True, None))
        mode = InstallMode(
            'copy', optional=[dependency, self.option])
        passed_params = {'dependency': 'eggs', 'option': 'ham'}
        self.assertIsNone(validate_dependencies(mode, passed_params))


class ParserModeTestCase(unittest.TestCase):

    @patch('click.prompt')
    def test_interactive_mode_returns_params_correctly(self, prompt):
        option1 = ImageOption(['--option'])
        option2 = ImageOption(['--other'])
        mode = InstallMode(
            'copy', optional=[option1, option2])

        prompt.side_effect = [mode, 10, 20]
        ctx = Mock()

        observed = interactive_mode(ctx)
        self.assertEqual(observed['install_mode'], mode)
        self.assertEqual(observed['option'], 10)
        self.assertEqual(observed['other'], 20)

    @patch('click.prompt')
    def test_interactive_mode_makes_prompt_default_correctly(self, prompt):
        option1 = ImageOption(['--option'], default_lazy=100)
        option2 = ImageOption(['--other'])
        mode = InstallMode(
            'copy', optional=[option1, option2])

        prompt.side_effect = [mode, 10, 20]
        ctx = Mock()
        interactive_mode(ctx)

        # Install mode pormpt must not have a default (and always
        # prompt user until get a valid value)
        install_mode_prompt = prompt.call_args_list[0]
        args, kw = install_mode_prompt
        self.assertIsNone(kw['default'])

        # Images prompt must always have a default value, even if it
        # is not required. In this case, an empty string must be
        # passed
        option_with_default = prompt.call_args_list[1]
        args, kw = option_with_default
        self.assertEqual(kw['default'], 100)

        option_without_default = prompt.call_args_list[2]
        args, kw = option_without_default
        self.assertEqual(kw['default'], '')

    @patch('click.prompt')
    def test_no_prompt_in_interactive_mode_if_missing_dependency(self, prompt):
        '''
        Different from explicit mode, if a option dependency is not
        satisfied, we should not raise an exception. Instead, we must
        not prompt this specific option.

        Here, we have 2 options: 'option' and 'other'. Also 'other'
        implies 'option' to be provided.

        In this case, we simulate a user leaving blank the 'option'
        prompt so 'other' must not be prompted.
        '''
        option1 = ImageOption(['--option'])
        option2 = ImageOption(['--other'], dependencies=[option1])
        mode = InstallMode(
            'copy', optional=[option1, option2])
        prompt.side_effect = [mode, '']
        ctx = Mock()
        interactive_mode(ctx)
        # one call for getting mode, and other call for getting option.
        self.assertEqual(prompt.call_count, 2)

    @patch('click.prompt')
    def test_no_prompt_in_interactive_mode_if_invalid_dependency(self, prompt):
        '''
        This case is similar with the previous one. Here, a value is
        provided for 'option' but it does not satisfies 'other'
        dependency.
        '''
        option1 = ImageOption(['--option'])
        option2 = ImageOption(
            ['--other'], dependencies=[option1],
            callback_lazy=lambda x: (False, None))
        mode = InstallMode(
            'copy', optional=[option1, option2])
        prompt.side_effect = [mode, 'invalid-value']
        ctx = Mock()
        interactive_mode(ctx)
        # one call for getting mode, and other call for getting option.
        self.assertEqual(prompt.call_count, 2)

    @patch('click.prompt')
    def test_interactive_mode_does_not_add_option_if_empty_value(self, prompt):
        '''
        If a option is not required and id does not have a default value,
        it should not be added to final image if user does not provide
        a value for it.
        '''
        option1 = ImageOption(['--option'])
        mode = InstallMode(
            'copy', optional=[option1])
        prompt.side_effect = [mode, '']
        ctx = Mock()
        params = interactive_mode(ctx)
        self.assertIsNone(params.get('option'))

    def test_clean_params_removes_unnecessary_values(self):
        params = {'ham': None, 'spam': True, 'eggs': False}
        observed = clean_params(params)
        self.assertEqual(len(observed), 2)
        self.assertIsNone(observed.get('ham'))

    def test_explicty_mode_returns_params_correctly(self):
        # option required, must be present
        spam = ImageOption(['--spam'])
        # option not required, must not be present
        ham = ImageOption(['--ham'])
        # option not required with default, must be present
        eggs = ImageOption(['--eggs'], default_lazy=2)

        mode = InstallMode('copy', optional=[eggs, ham], required=[spam])
        params = {'ham': None, 'spam': True, 'eggs': None}
        observed = explicit_mode(mode, params)
        expected = {'spam': True, 'eggs': 2}
        self.assertEqual(observed, expected)


class AddCommandTestCase(unittest.TestCase):

    def setUp(self):
        with open('.efu-test', 'w'):
            pass
        self.addCleanup(os.remove, '.efu-test')
        os.environ['EFU_PACKAGE_FILE'] = '.efu-test'
        self.runner = CliRunner()

    def test_explicit_mode_is_called_if_options_are_provided(self):
        with patch('efu.package.parser.interactive_mode') as interactive:
            with patch('efu.package.parser.explicit_mode') as explicit:
                self.runner.invoke(
                    add_command, [__file__, '-m', 'raw', '-td', 'device'])
                self.assertTrue(explicit.called)
                self.assertFalse(interactive.called)

    def test_interactive_mode_is_called_if_options_are_provided(self):
        with patch('efu.package.parser.interactive_mode') as interactive:
            with patch('efu.package.parser.explicit_mode') as explicit:
                self.runner.invoke(add_command, [__file__])
                self.assertTrue(interactive.called)
                self.assertFalse(explicit.called)

    def test_no_mode_is_called_if_package_file_does_not_exist(self):
        del os.environ['EFU_PACKAGE_FILE']
        with patch('efu.package.parser.interactive_mode') as interactive:
            with patch('efu.package.parser.explicit_mode') as explicit:
                self.runner.invoke(
                    add_command, [__file__, '-m', 'raw', '-td', 'device'])
                self.runner.invoke(add_command, [__file__])
                self.assertFalse(explicit.called)
                self.assertFalse(interactive.called)


class RemoveCommandTestCase(unittest.TestCase):

    def remove_package_file_env_var(self):
        try:
            del os.environ['EFU_PACKAGE_FILE']
        except KeyError:
            # already deleted
            pass

    def remove_package_file(self):
        try:
            os.remove(self.package_fn)
        except FileNotFoundError:
            # already deleted
            pass

    def setUp(self):
        self.package_fn = '.efu-test'
        data = {
            'product': '1234R',
            'files': {'setup.py': {}}
        }
        os.environ['EFU_PACKAGE_FILE'] = self.package_fn
        self.addCleanup(self.remove_package_file_env_var)

        with open(self.package_fn, 'w') as fp:
            json.dump(data, fp)
        self.addCleanup(self.remove_package_file)

        self.runner = CliRunner()

    def test_can_remove_image_with_rm_command(self):
        self.runner.invoke(remove_command, args=['setup.py'])
        with open(self.package_fn) as fp:
            package = json.load(fp)
        self.assertIsNone(package['files'].get('setup.py'))

    def test_rm_command_returns_0_if_successful(self):
        result = self.runner.invoke(remove_command, args=['setup.py'])
        self.assertEqual(result.exit_code, 0)

    def test_rm_command_returns_1_if_package_does_not_exist(self):
        os.environ['EFU_PACKAGE_FILE'] = '.not-exists'
        result = self.runner.invoke(remove_command, args=['setup.py'])
        self.assertEqual(result.exit_code, 1)

    def test_rm_command_returns_2_if_image_does_not_exist(self):
        result = self.runner.invoke(remove_command, args=['not-exists.py'])
        self.assertEqual(result.exit_code, 2)


class CleanupCommandTestCase(unittest.TestCase):

    def setUp(self):
        os.environ['EFU_PACKAGE_FILE'] = '.efu-test'
        self.runner = CliRunner()
        self.addCleanup(os.environ.pop, 'EFU_PACKAGE_FILE')

    def test_can_cleanup_efu_files(self):
        with open('.efu-test', 'w') as fp:
            pass
        self.assertTrue(os.path.exists('.efu-test'))
        self.runner.invoke(cleanup_command)
        self.assertFalse(os.path.exists('.efu-test'))

    def test_cleanup_command_returns_0_if_successful(self):
        with open('.efu-test', 'w') as fp:
            pass
        result = self.runner.invoke(cleanup_command)
        self.assertEqual(result.exit_code, 0)

    def test_cleanup_command_returns_1_if_package_is_already_deleted(self):
        result = self.runner.invoke(cleanup_command)
        self.assertEqual(result.exit_code, 1)


class ShowCommandTestCase(unittest.TestCase):

    def remove_package_file(self):
        try:
            os.remove('.efu-test')
        except FileNotFoundError:
            pass  # already deleted

    def setUp(self):
        os.environ['EFU_PACKAGE_FILE'] = '.efu-test'
        self.runner = CliRunner()
        self.addCleanup(os.environ.pop, 'EFU_PACKAGE_FILE')
        self.addCleanup(self.remove_package_file)

    def test_show_command_returns_0_if_successful(self):
        package = {
            'product': '1234',
            'files': {
                'spam.py': {
                    'install-mode': 'raw',
                    'target-device': 'device',
                }
            }
        }
        with open('.efu-test', 'w') as fp:
            json.dump(package, fp)
        result = self.runner.invoke(show_command)
        self.assertEqual(result.exit_code, 0)

    def test_show_command_returns_1_if_package_does_not_exist(self):
        result = self.runner.invoke(show_command)
        self.assertEqual(result.exit_code, 1)


class ExportCommandTestCase(unittest.TestCase):

    def remove_file(self, fn):
        try:
            os.remove(fn)
        except FileNotFoundError:
            pass  # already deleted

    def setUp(self):
        self.package_fn = '.efu-test'
        self.exported_package_fn = 'efu-exported'
        os.environ['EFU_PACKAGE_FILE'] = self.package_fn
        self.runner = CliRunner()
        self.addCleanup(os.environ.pop, 'EFU_PACKAGE_FILE')

        self.addCleanup(self.remove_file, self.package_fn)
        self.addCleanup(self.remove_file, self.exported_package_fn)
        self.package = {
            'product': '1234',
            'files': {
                'spam.py': {
                    'install-mode': 'raw',
                    'target-device': 'device',
                }
            }
        }

    def create_package(self):
        with open(self.package_fn, 'w') as fp:
            json.dump(self.package, fp)

    def test_can_export_package_file(self):
        self.create_package()
        self.assertFalse(os.path.exists(self.exported_package_fn))
        self.runner.invoke(export_command, args=[self.exported_package_fn])
        self.assertTrue(os.path.exists(self.exported_package_fn))

        with open(self.exported_package_fn) as fp:
            exported_package = json.load(fp)
        self.assertEqual(exported_package, self.package)

    def test_export_package_command_returns_0_if_successful(self):
        self.create_package()
        result = self.runner.invoke(
            export_command, args=[self.exported_package_fn])
        self.assertEqual(result.exit_code, 0)

    def test_export_command_returns_1_if_package_does_not_exist(self):
        result = self.runner.invoke(
            export_command, args=[self.exported_package_fn])
        self.assertEqual(result.exit_code, 1)
