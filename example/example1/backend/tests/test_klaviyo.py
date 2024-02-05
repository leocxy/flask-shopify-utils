#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# @Project : flask-shopify-utils
# @File    : test_klaviyo.py
# @Author  : Leo Chen<leo.cxy88@gmail.com>
# @Date    : 01/02/24 02:53 pm
"""
from datetime import datetime
from simplejson import loads

# dynamic variable
RECIPIENT_EMAIL = 'leo@pocketsquare.co.nz'
LIST_ID = 'QXBa2Z'


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
            properties=dict(
                unit_test_create=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            )
        )
    ))
    rs, data = helper.create_profile(params)
    if unique_id:
        test.assertFalse(rs)
        data = loads(data)
        errors = data.get('errors', None)
        test.assertIsNot(None, errors)
        test.assertEqual(errors[0]['detail'], 'A profile already exists with one of these identifiers.')
    else:
        test.assertTrue(rs)


def test_search_profile(klaviyo) -> None:
    """ Search profile on Klaviyo"""
    helper, test = klaviyo
    rs, profile_id = helper.search_profile(RECIPIENT_EMAIL)
    test.assertTrue(rs)
    test.assertIsNot(None, profile_id)


def test_update_profile(klaviyo) -> None:
    """ Update profile attribute on Klaviyo"""
    helper, test = klaviyo
    rs, profile_id = helper.search_profile(RECIPIENT_EMAIL)
    test.assertTrue(rs)
    test.assertIsNot(None, profile_id)
    params = dict(
        type='profile',
        id=profile_id,
        attributes=dict(
            properties=dict(
                unit_test_update=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            )
        )
    )
    rs = helper.update_profile(profile_id, dict(data=params), RECIPIENT_EMAIL)
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


def test_query_profile_lists(klaviyo) -> None:
    """ Query profile lists on Klaviyo"""
    helper, test = klaviyo
    rs, unique_id = helper.search_profile(RECIPIENT_EMAIL)
    test.assertTrue(rs)
    test.assertIsNot(None, unique_id)
    rs, data = helper.get_profile_lists(unique_id)
    test.assertTrue(rs)
    print(data)


def test_subscribe_profile(klaviyo) -> None:
    """ Subscribe profile to list on Klaviyo"""
    helper, test = klaviyo
    rs, profile_id = helper.search_profile(RECIPIENT_EMAIL)
    test.assertTrue(rs)
    test.assertIsNot(None, profile_id)
    rs = helper.subscribe_profile(profile_id, LIST_ID, RECIPIENT_EMAIL)
    test.assertTrue(rs)


def test_create_event(klaviyo) -> None:
    """ Create event on Klaviyo"""
    helper, test = klaviyo
    params = dict(
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
                expiry_date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                message="Just a test event",
                recipient_name="Leo",
                sender_name="UnitTest",
            )
        )
    )
    rs = helper.create_event(dict(data=params))
    test.assertTrue(rs)
