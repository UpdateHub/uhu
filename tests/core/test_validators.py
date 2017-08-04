# Copyright (C) 2017 O.S. Systems Software LTDA.
# SPDX-License-Identifier: GPL-2.0

import unittest

from uhu.core.validators import validate_option_requirements


class ValidateOptionRequirementsTestCase(unittest.TestCase):

    def test_values_argument_type_checking(self):
        with self.assertRaises(TypeError):
            validate_option_requirements(None, {'key': 'value'})
