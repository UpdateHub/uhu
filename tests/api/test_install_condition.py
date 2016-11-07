# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import os
import tempfile
import unittest

from efu.core import install_condition as ic


class KernelVersionTestCase(unittest.TestCase):

    def get_kernel_fixture(self, fixture):
        basedir = os.path.join(os.path.dirname(__file__), '../fixtures/kernel')
        return os.path.join(basedir, fixture)

    def test_can_get_kernel_version(self):
        images = [
            ('arm-zImage', '4.4.1'),
            ('arm-uImage', '4.1.15-1.2.0+g274a055'),
            ('x86-bzImage', '4.1.30-1-MANJARO'),
            ('x86-zImage', '4.1.30-1-MANJARO'),
        ]
        for image, version in images:
            with open(self.get_kernel_fixture(image), 'br') as fp:
                observed = ic.get_kernel_version(fp)
                self.assertEqual(observed, version)

    def test_can_get_kernel_version_raises_error_if_cant_find_version(self):
        with tempfile.TemporaryFile() as fp:
            with self.assertRaises(ValueError):
                ic.get_kernel_version(fp)

    def test_is_arm_uImage_returns_True_when_arm_uImage(self):
        with open(self.get_kernel_fixture('arm-uImage'), 'br') as fp:
            self.assertTrue(ic.is_arm_uImage(fp))

    def test_is_arm_zImage_returns_True_when_arm_zImage(self):
        with open(self.get_kernel_fixture('arm-zImage'), 'br') as fp:
            self.assertTrue(ic.is_arm_zImage(fp))

    def test_is_x86_bzImage_returns_True_when_x86_bzImage(self):
        with open(self.get_kernel_fixture('x86-bzImage'), 'br') as fp:
            self.assertTrue(ic.is_x86_bzImage(fp))

    def test_is_x86_zImage_magic_returns_True_when_x86_zImage(self):
        with open(self.get_kernel_fixture('x86-zImage'), 'br') as fp:
            self.assertTrue(ic.is_x86_zImage(fp))

    def test_is_arm_uImage_returns_False_when_not_arm_uImage(self):
        images = ['arm-zImage', 'x86-bzImage', 'x86-zImage']
        for image in images:
            with open(self.get_kernel_fixture(image), 'rb') as fp:
                self.assertFalse(ic.is_arm_uImage(fp))

    def test_is_arm_zImage_returns_False_when_not_arm_zImage(self):
        images = ['arm-uImage', 'x86-bzImage', 'x86-zImage']
        for image in images:
            with open(self.get_kernel_fixture(image), 'rb') as fp:
                self.assertFalse(ic.is_arm_zImage(fp))

    def test_is_x86_bzImage_returns_False_when_not_x86_bzImage(self):
        images = ['arm-uImage', 'arm-zImage', 'x86-zImage']
        for image in images:
            with open(self.get_kernel_fixture(image), 'rb') as fp:
                self.assertFalse(ic.is_x86_bzImage(fp))

    def test_is_x86_zImage_magic_returns_False_when_not_x86_zImage(self):
        images = ['arm-uImage', 'arm-zImage', 'x86-bzImage']
        for image in images:
            with open(self.get_kernel_fixture(image), 'rb') as fp:
                self.assertFalse(ic.is_x86_zImage(fp))

    def test_can_get_arm_zImage_version(self):
        expected = '4.4.1'
        with open(self.get_kernel_fixture('arm-zImage'), 'br') as fp:
            observed = ic.get_arm_zImage_version(fp)
        self.assertEqual(expected, observed)

    def test_can_get_arm_uImage_version(self):
        expected = '4.1.15-1.2.0+g274a055'
        with open(self.get_kernel_fixture('arm-uImage'), 'br') as fp:
            observed = ic.get_arm_uImage_version(fp)
        self.assertEqual(expected, observed)

    def test_can_get_x86_bzImage_version(self):
        expected = '4.1.30-1-MANJARO'
        with open(self.get_kernel_fixture('x86-bzImage'), 'br') as fp:
            observed = ic.get_x86_bzImage_version(fp)
        self.assertEqual(expected, observed)

    def test_can_get_x86_zImage_version(self):
        expected = '4.1.30-1-MANJARO'
        with open(self.get_kernel_fixture('x86-zImage'), 'br') as fp:
            observed = ic.get_x86_zImage_version(fp)
        self.assertEqual(expected, observed)


class UBootVersionTestCase(unittest.TestCase):

    def test_can_get_uboot_version(self):
        fp = tempfile.TemporaryFile()
        self.addCleanup(fp.close)
        # U-Boot 13.08.1988 (13/08/1988)
        fp.write(bytearray.fromhex(
            '01552d426f6f742031332e30382e31393838202831332f30382f313938382902'))  # nopep8
        expected = '13.08.1988'
        observed = ic.get_uboot_version(fp)
        self.assertEqual(observed, expected)

    def test_get_uboot_version_raises_error_if_cant_find_version(self):
        with tempfile.TemporaryFile() as fp:
            with self.assertRaises(ValueError):
                ic.get_uboot_version(fp)


class CustomObjectVersionTestCase(unittest.TestCase):

    def test_can_get_custom_object_version(self):
        fp = tempfile.TemporaryFile()
        self.addCleanup(fp.close)
        fp.write(bytearray.fromhex('5f5f5f312e305f5f5f'))  # ___1.0___
        expected = '1.0'
        observed = ic.get_object_version(fp, br'\d\.\d', seek=3, buffer_size=5)
        self.assertEqual(observed, expected)

    def test_get_object_version_raises_error_if_cant_find_version(self):
        with tempfile.TemporaryFile() as fp:
            with self.assertRaises(ValueError):
                ic.get_object_version(fp, br'^unfindable$')
