#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# @Project : flask-shopify-utils
# @File    : test_get_version.py
# @Author  : Leo Chen<leo.cxy88@gmail.com>
# @Date    : 27/05/23 3:16 pm
"""
from os import environ
from datetime import datetime
from unittest import TestCase
from unittest.mock import patch
from pytest import fixture, raises, mark
from flask_shopify_utils.utils import get_version, VERSION_KEY


@fixture(scope='function')
def test() -> TestCase:
    """ TestCase helper + keep the `API_VERSION` environment variable untouched """
    origin = environ.get(VERSION_KEY)
    environ.pop(VERSION_KEY, None)
    case = TestCase()
    case.maxDiff = None
    yield case
    environ.pop(VERSION_KEY, None)
    if origin is not None:
        environ[VERSION_KEY] = origin


def freeze(year: int, month: int, day: int = 15):
    """ Patch `datetime` within the utils module, so `datetime.today()` is predictable """
    return patch('flask_shopify_utils.utils.datetime', **{'today.return_value': datetime(year, month, day)})


@mark.parametrize('month, expected', [
    (1, '2025-01'), (2, '2025-01'), (3, '2025-01'),
    (4, '2025-04'), (5, '2025-04'), (6, '2025-04'),
    (7, '2025-07'), (8, '2025-07'), (9, '2025-07'),
    (10, '2025-10'), (11, '2025-10'), (12, '2025-10'),
])
def test_latest_version_per_month(test, month, expected) -> None:
    """ The latest version always falls back to the Jan/Apr/Jul/Oct release """
    with freeze(2025, month):
        # `2000-01` is way too old, so the latest version will be used
        environ[VERSION_KEY] = '2000-01'
        test.assertEqual(expected, get_version())


@mark.parametrize('value', ['abc', '202601', '2026-1', '26-01', '0000-01', '2026-01-01', ' 2026-01'])
def test_invalid_format(test, value) -> None:
    """ Invalid version format raises `ValueError` """
    with raises(ValueError) as err:
        get_version(value)
    test.assertEqual('Invalid API version format: {}'.format(value), str(err.value))
    # the environment variable should not be updated
    test.assertIsNone(environ.get(VERSION_KEY))


@mark.parametrize('value', ['', 'abc', '202601', '0000-01'])
def test_invalid_format_from_environment_variable(test, value) -> None:
    """ Invalid version format from the environment variable raises `ValueError` """
    environ[VERSION_KEY] = value
    with raises(ValueError) as err:
        get_version()
    test.assertEqual('Invalid API version format: {}'.format(value), str(err.value))


def test_default_value(test) -> None:
    """ Without the environment variable, the hardcoded default `2026-04` is used """
    with freeze(2026, 4):
        test.assertEqual('2026-04', get_version())
    # the environment variable should be updated
    test.assertEqual('2026-04', environ.get(VERSION_KEY))


def test_environment_variable(test) -> None:
    """ A valid version from the environment variable is respected """
    environ[VERSION_KEY] = '2025-04'
    with freeze(2025, 10):
        test.assertEqual('2025-04', get_version())
    test.assertEqual('2025-04', environ.get(VERSION_KEY))


def test_environment_variable_out_of_range(test) -> None:
    """ Too old / too new version from the environment variable falls back to the latest one """
    with freeze(2025, 10):
        # older than 1 year
        environ[VERSION_KEY] = '2024-07'
        test.assertEqual('2025-10', get_version())
        # newer than the latest release
        environ[VERSION_KEY] = '2026-01'
        test.assertEqual('2025-10', get_version())
    test.assertEqual('2025-10', environ.get(VERSION_KEY))


def test_environment_variable_boundary(test) -> None:
    """ Both boundaries(latest / earliest) are valid values """
    with freeze(2025, 10):
        environ[VERSION_KEY] = '2025-10'
        test.assertEqual('2025-10', get_version())
        environ[VERSION_KEY] = '2024-10'
        test.assertEqual('2024-10', get_version())


def test_force_version(test) -> None:
    """ The given version wins over the environment variable """
    environ[VERSION_KEY] = '2025-04'
    with freeze(2025, 10):
        test.assertEqual('2025-07', get_version('2025-07'))
    test.assertEqual('2025-07', environ.get(VERSION_KEY))


def test_force_version_out_of_range(test) -> None:
    """ The given version is used as-is, even if it is out of the valid range """
    with freeze(2025, 10):
        test.assertEqual('2020-01', get_version('2020-01'))
        test.assertEqual('2020-01', environ.get(VERSION_KEY))
        test.assertEqual('2099-10', get_version('2099-10'))
        test.assertEqual('2099-10', environ.get(VERSION_KEY))
