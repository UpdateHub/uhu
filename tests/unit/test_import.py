# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import unittest


class ImportTestCase(unittest.TestCase):

    def test_import(self):
        try:
            import efu
        except ImportError:
            self.fail('It is not possible to import efu package')


if __name__ == '__main__':
    unittest.main()
