#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# @Project : flask-shopify-utils
# @File    : test_klaviyo.py
# @Author  : Leo Chen<leo.cxy88@gmail.com>
# @Date    : 01/02/24 02:53 pm
"""
from os import getenv
from datetime import datetime
from pytest import fixture, mark
from simplejson import loads

# dynamic variable, could be overwritten by the environment variables
RECIPIENT_EMAIL = getenv('KLAVIYO_TEST_EMAIL', 'leo@pocketsquare.co.nz')
LIST_ID = getenv('KLAVIYO_TEST_LIST_ID', 'QXBa2Z')

# Those tests are hitting the real Klaviyo API, skip them while the API key is missing.
pytestmark = mark.skipif(
    not getenv('KLAVIYO_PRIVATE_KEY'),
    reason='KLAVIYO_PRIVATE_KEY is not set, skipping the Klaviyo API tests.'
)


def timestamp() -> str:
    """ Current timestamp, used as the profile property value """
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


@fixture(scope='function')
def profile_id(klaviyo) -> str:
    """ Look up the test profile once and share the unique id between the tests """
    helper, test = klaviyo
    rs, unique_id = helper.search_profile(RECIPIENT_EMAIL)
    test.assertTrue(rs)
    test.assertIsNot(None, unique_id)
    return unique_id


def test_create_profile(klaviyo) -> None:
    """ Create profile on Klaviyo"""
    helper, test = klaviyo
    # you can't delete the profile via API
    rs, unique_id = helper.search_profile(RECIPIENT_EMAIL)
    test.assertTrue(rs)
    # real test
    params = dict(data=dict(
        type='profile',
        attributes=dict(
            email=RECIPIENT_EMAIL,
            first_name='Test',
            last_name='Order',
            properties=dict(unit_test_create=timestamp())
        )
    ))
    rs, data = helper.create_profile(params)
    if unique_id:
        test.assertFalse(rs)
        errors = loads(data).get('errors', None)
        test.assertIsNot(None, errors)
        test.assertEqual(errors[0]['detail'], 'A profile already exists with one of these identifiers.')
    else:
        test.assertTrue(rs)


def test_search_profile(profile_id) -> None:
    """ Search profile on Klaviyo"""
    assert profile_id


def test_update_profile(klaviyo, profile_id) -> None:
    """ Update profile attribute on Klaviyo"""
    helper, test = klaviyo
    params = dict(data=dict(
        type='profile',
        id=profile_id,
        attributes=dict(
            properties=dict(unit_test_update=timestamp())
        )
    ))
    rs = helper.update_profile(profile_id, params, RECIPIENT_EMAIL)
    test.assertTrue(rs)


def test_suppress_profile(klaviyo) -> None:
    """ Suppress profile on Klaviyo"""
    helper, test = klaviyo
    rs, _data = helper.suppress_profile(RECIPIENT_EMAIL)
    test.assertTrue(rs)


def test_unsuppress_profile(klaviyo) -> None:
    """ Unsuppress profile on Klaviyo"""
    helper, test = klaviyo
    rs, _data = helper.unsuppress_profile(RECIPIENT_EMAIL)
    test.assertTrue(rs)


def test_query_profile_lists(klaviyo, profile_id) -> None:
    """ Query profile lists on Klaviyo"""
    helper, test = klaviyo
    rs, data = helper.get_profile_lists(profile_id)
    test.assertTrue(rs)
    print(data)


@mark.skipif(not LIST_ID, reason='KLAVIYO_TEST_LIST_ID is not set, skipping the subscription test.')
def test_subscribe_profile(klaviyo, profile_id) -> None:
    """ Subscribe profile to list on Klaviyo"""
    helper, test = klaviyo
    rs = helper.subscribe_profile(profile_id, LIST_ID, RECIPIENT_EMAIL)
    test.assertTrue(rs)


def test_create_event(klaviyo) -> None:
    """ Create event on Klaviyo"""
    helper, test = klaviyo
    params = dict(data=dict(
        type='event',
        attributes=dict(
            metric=dict(data=dict(
                type='metric',
                attributes=dict(name='Test Create Event')
            )),
            profile=dict(data=dict(
                type='profile',
                attributes=dict(email=RECIPIENT_EMAIL)
            )),
            properties=dict(
                value='999.0',
                card_number='TEST-1234567890',
                expiry_date=timestamp(),
                message='Just a test event',
                recipient_name='Leo',
                sender_name='UnitTest',
            )
        )
    ))
    rs = helper.create_event(params)
    test.assertTrue(rs)
